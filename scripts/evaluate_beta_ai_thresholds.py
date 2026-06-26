"""Evaluate Beta AI Tutor threshold behavior from simulation traces.

The script is intentionally read-only. It consumes JSON files written by
``scripts/simulate_beta_ai_exercise.py`` and produces a compact evidence report
for the numeric and state-transition heuristics used by the Beta AI didactic
control layer.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCORE_THRESHOLDS = {
    "off_task_relevance_boundary": 0.3,
    "completion_relevance_guard": 0.5,
    "higher_level_normal_pass": 0.7,
    "higher_level_unclear_pass": 0.85,
}

HIGHER_LEVEL_NORMAL_CANDIDATES = [0.7, 0.8, 0.9]
HIGHER_LEVEL_UNCLEAR_CANDIDATES = [0.85, 0.9]

OTHER_HEURISTICS = {
    "keyword_only_word_count": 4,
    "short_request_word_count": 8,
    "copy_similarity_threshold": 0.82,
    "copy_min_text_length": 24,
    "copy_recent_message_window": 8,
    "misconception_repair_loop": "no human-review threshold",
    "tutor_leak_min_core_text_length": 24,
}

PROBLEMATIC_PATTERNS = {
    "help_seeking",
    "tutor_derived_answer",
    "off_task",
    "shallow_keyword_only",
    "misconception_present",
}


@dataclass
class PersonaMetrics:
    """Aggregated metrics for one simulation JSON file."""

    path: Path
    persona: str
    turn_count: int
    completed_all: bool
    completed_concepts: int
    final_states: Counter[str] = field(default_factory=Counter)
    validated_patterns: Counter[str] = field(default_factory=Counter)
    cumulative_patterns: Counter[str] = field(default_factory=Counter)
    policy_actions: Counter[str] = field(default_factory=Counter)
    llm_to_app_normalizations: Counter[str] = field(default_factory=Counter)
    score_values: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    threshold_near_misses: Counter[str] = field(default_factory=Counter)
    risky_progress_events: list[str] = field(default_factory=list)
    friction_events: list[str] = field(default_factory=list)
    misconception_events: list[str] = field(default_factory=list)
    unclear_events: list[str] = field(default_factory=list)
    repair_or_fallback_events: list[str] = field(default_factory=list)
    higher_level_candidate_events: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    basic_turns_to_pass: list[int] = field(default_factory=list)
    basic_overhard_events: list[str] = field(default_factory=list)
    basic_oversoft_events: list[str] = field(default_factory=list)


def load_json(path: Path) -> dict[str, Any]:
    """Load one simulation JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: Any) -> float | None:
    """Return a float when the value is numeric enough for score analysis."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def concept_completion_count(trace: list[dict[str, Any]]) -> int:
    """Count concepts that reached secure state at least once in a trace."""
    secure_concepts = {
        entry.get("concept_id")
        for entry in trace
        if entry.get("student_state", {}).get("state") == "secure"
    }
    return len({concept_id for concept_id in secure_concepts if concept_id is not None})


def score_bucket_near_threshold(
    score: float, threshold: float, margin: float = 0.05
) -> bool:
    """Return whether a score lies close enough to a threshold to inspect."""
    return abs(score - threshold) <= margin


def summarize_scores(values: list[float]) -> str:
    """Return compact summary statistics for a score list."""
    if not values:
        return "n/a"
    return (
        f"n={len(values)}, min={min(values):.2f}, "
        f"mean={statistics.mean(values):.2f}, max={max(values):.2f}"
    )


def entry_label(entry: dict[str, Any]) -> str:
    """Return a stable human-readable turn label."""
    return (
        f"{entry.get('concept_label', 'unknown concept')} "
        f"turn {entry.get('turn_in_concept', '?')}"
    )


def level_status(entry: dict[str, Any]) -> dict[str, Any]:
    """Return the normalized level-status-ish mapping stored in a trace entry."""
    state = entry.get("student_state", {})
    value = state.get("level_status", {})
    return value if isinstance(value, dict) else {}


def answered_level(entry: dict[str, Any]) -> str:
    """Best-effort answered level for older traces.

    Simulation entries currently persist the generated *next* tutor turn rather
    than a dedicated current_question_level-before-answer field. For aggregate
    calibration this is still useful as an approximation, because higher-level
    repair/transition traces keep the active level in the generated tutor turn.
    """
    tutor_turn = entry.get("tutor_turn", {})
    return str(tutor_turn.get("question_level") or "")


def is_problematic_pattern(pattern: str) -> bool:
    """Return whether a diagnosis pattern should never create progress alone."""
    return pattern in PROBLEMATIC_PATTERNS or pattern == "tutor_derived_answer"


def record_threshold_candidate_events(
    *,
    metrics: PersonaMetrics,
    entry: dict[str, Any],
    validated_pattern: str,
    relevance: float,
    correctness: float,
) -> None:
    """Record what alternative higher-level thresholds would decide."""
    level = answered_level(entry)
    if level not in {"explain_reasoning", "apply_or_compare"}:
        return
    if is_problematic_pattern(validated_pattern):
        return

    if validated_pattern == "unclear":
        candidates = HIGHER_LEVEL_UNCLEAR_CANDIDATES
        rule_name = "higher_level_unclear_pass"
    else:
        candidates = HIGHER_LEVEL_NORMAL_CANDIDATES
        rule_name = "higher_level_normal_pass"

    score = min(relevance, correctness)
    for candidate in candidates:
        decision = "would_pass" if score >= candidate else "would_block"
        metrics.higher_level_candidate_events[f"{rule_name}@{candidate:.2f}"][
            decision
        ] += 1


def record_basic_fairness_events(
    *,
    metrics: PersonaMetrics,
    entry: dict[str, Any],
    validated_pattern: str,
    relevance: float,
    correctness: float,
) -> None:
    """Record evidence about Basic-level strictness/leniency."""
    status = level_status(entry)
    state = entry.get("student_state", {})
    basic_status = str(status.get("basic_understanding", ""))
    turn = int(entry.get("turn_in_concept") or 0)

    if basic_status == "passed" and turn:
        metrics.basic_turns_to_pass.append(turn)

    if (
        basic_status != "passed"
        and relevance >= 0.9
        and correctness >= 0.9
        and validated_pattern == "correct_but_incomplete"
    ):
        missing = state.get("missing_core_point_ids", [])
        metrics.basic_overhard_events.append(
            f"{entry_label(entry)}: high rel/corr={relevance:.2f}/{correctness:.2f} "
            f"but Basic not passed; missing={missing}"
        )

    if basic_status == "passed" and (
        is_problematic_pattern(validated_pattern)
        or relevance < 0.5
        or correctness < 0.7
    ):
        metrics.basic_oversoft_events.append(
            f"{entry_label(entry)}: Basic passed despite pattern={validated_pattern}, "
            f"rel={relevance:.2f}, corr={correctness:.2f}"
        )


def analyze_simulation(path: Path) -> PersonaMetrics:
    """Analyze one simulation trace file."""
    data = load_json(path)
    trace: list[dict[str, Any]] = list(data.get("trace", []))
    persona = str(
        data.get("persona") or path.stem.replace("beta_ai_simulation_vorlesung1_", "")
    )
    metrics = PersonaMetrics(
        path=path,
        persona=persona,
        turn_count=len(trace),
        completed_all=bool(data.get("completed_all")),
        completed_concepts=concept_completion_count(trace),
    )

    seen_concepts: dict[Any, str] = {}
    for entry in trace:
        concept_id = entry.get("concept_id")
        if concept_id is not None:
            seen_concepts[concept_id] = str(entry.get("concept_label", concept_id))

        raw = entry.get("raw_diagnosis", {})
        validated = entry.get("validated_diagnosis", {})
        cumulative = entry.get("cumulative_diagnosis", {})
        policy = entry.get("policy", {})
        tutor_turn = entry.get("tutor_turn", {})
        state = entry.get("student_state", {})

        metrics.final_states[str(state.get("state", "unknown"))] += 1
        validated_pattern = str(validated.get("diagnosis_pattern", "unknown"))
        cumulative_pattern = str(cumulative.get("diagnosis_pattern", "unknown"))
        llm_pattern = str(entry.get("llm_suggested_pattern", "unknown"))
        metrics.validated_patterns[validated_pattern] += 1
        metrics.cumulative_patterns[cumulative_pattern] += 1
        metrics.policy_actions[str(policy.get("action", "unknown"))] += 1

        if llm_pattern != validated_pattern:
            metrics.llm_to_app_normalizations[
                f"{llm_pattern} -> {validated_pattern}"
            ] += 1

        for score_name in ("task_relevance", "correctness", "completeness"):
            score = as_float(validated.get(score_name))
            if score is None:
                continue
            metrics.score_values[score_name].append(score)
            for threshold_name, threshold in SCORE_THRESHOLDS.items():
                if score_bucket_near_threshold(score, threshold):
                    metrics.threshold_near_misses[
                        f"{score_name} near {threshold_name} ({threshold})"
                    ] += 1

        # False-progress risk: problematic current evidence should not pass
        # levels or secure concepts.
        if validated_pattern in PROBLEMATIC_PATTERNS:
            level_status = state.get("level_status", {})
            if "passed" in set(level_status.values()) or state.get("state") in {
                "satisfactory",
                "secure",
            }:
                metrics.risky_progress_events.append(
                    f"{entry_label(entry)}: problematic pattern "
                    f"{validated_pattern} occurred while state/levels show "
                    f"progress: {level_status}, state={state.get('state')}"
                )

        # Friction risk: strong scores but still no higher-level progress.
        relevance = as_float(validated.get("task_relevance")) or 0.0
        correctness = as_float(validated.get("correctness")) or 0.0
        question_level = str(tutor_turn.get("question_level") or "")
        if (
            question_level in {"explain_reasoning", "apply_or_compare"}
            and relevance >= 0.9
            and correctness >= 0.9
            and state.get("state") not in {"satisfactory", "secure"}
            and cumulative_pattern != "sufficient_for_completion"
        ):
            metrics.friction_events.append(
                f"{entry_label(entry)}: high scores rel={relevance:.2f}/"
                f"corr={correctness:.2f} but state={state.get('state')} "
                f"and cumulative={cumulative_pattern}"
            )

        if validated_pattern == "misconception_present" or state.get(
            "misconception_hits", 0
        ):
            metrics.misconception_events.append(
                f"{entry_label(entry)}: pattern={validated_pattern}, "
                f"action={policy.get('action')}, state={state.get('state')}, "
                f"hits={state.get('misconception_hits')}"
            )
            if state.get("state") == "review_required":
                metrics.risky_progress_events.append(
                    f"{entry_label(entry)}: misconception caused review_required "
                    "instead of automatic repair loop."
                )

        if validated_pattern == "unclear" or raw.get("diagnosis_pattern") == "unclear":
            metrics.unclear_events.append(
                f"{entry_label(entry)}: raw={raw.get('diagnosis_pattern')}, "
                f"validated={validated_pattern}, rel={relevance:.2f}, "
                f"corr={correctness:.2f}, state={state.get('state')}"
            )

        record_threshold_candidate_events(
            metrics=metrics,
            entry=entry,
            validated_pattern=validated_pattern,
            relevance=relevance,
            correctness=correctness,
        )
        record_basic_fairness_events(
            metrics=metrics,
            entry=entry,
            validated_pattern=validated_pattern,
            relevance=relevance,
            correctness=correctness,
        )

        if (
            tutor_turn.get("reveals_answer")
            or "fallback" in str(policy.get("rationale", "")).lower()
        ):
            metrics.repair_or_fallback_events.append(
                f"{entry_label(entry)}: tutor reveals_answer="
                f"{tutor_turn.get('reveals_answer')}, "
                f"action={policy.get('action')}"
            )

    # Convert per-turn state counts into final concept state counts where possible.
    final_by_concept: dict[Any, str] = {}
    for entry in trace:
        concept_id = entry.get("concept_id")
        if concept_id is not None:
            final_by_concept[concept_id] = str(
                entry.get("student_state", {}).get("state", "unknown")
            )
    metrics.final_states = Counter(final_by_concept.values())
    return metrics


def recommendation_for_threshold(
    name: str, all_metrics: list[PersonaMetrics]
) -> tuple[str, str]:
    """Return a recommendation label and rationale for one threshold."""
    total_turns = sum(metric.turn_count for metric in all_metrics)
    near_count = sum(
        count
        for metric in all_metrics
        for key, count in metric.threshold_near_misses.items()
        if name in key
    )
    risky_count = sum(len(metric.risky_progress_events) for metric in all_metrics)
    friction_count = sum(len(metric.friction_events) for metric in all_metrics)
    misconception_review = sum(
        1
        for metric in all_metrics
        for event in metric.risky_progress_events
        if "review_required" in event
    )
    unclear_events = sum(len(metric.unclear_events) for metric in all_metrics)

    if name == "misconception_repair_loop":
        if misconception_review:
            return (
                "ändern",
                "Simulationen zeigen review_required bei Misconceptions; "
                "das widerspricht dem Ziel einer automatischen Repair-Schleife.",
            )
        return (
            "behalten",
            "Misconceptions werden geloggt und mit ask_contrast_question "
            "repariert, ohne in einen Human-Review-Zustand zu wechseln.",
        )
    if name == "higher_level_unclear_pass":
        if unclear_events:
            return (
                "kritisch prüfen",
                "Unclear-Fälle treten auf; ein automatischer Pass über hohe "
                "Scores ist schwer didaktisch zu begründen.",
            )
        return (
            "derzeit wenig Evidenz",
            "Keine oder kaum unclear-Fälle in den Traces; gezielte "
            "Simulationen nötig, bevor 0.85 begründbar ist.",
        )
    if name == "higher_level_normal_pass":
        if risky_count > 0:
            return (
                "prüfen",
                "Es gibt Risikoereignisse; 0.7 könnte zu lax sein oder "
                "wird durch andere Regeln umgangen.",
            )
        if friction_count > 0:
            return (
                "prüfen",
                "Hohe Scores führen teils nicht zu Fortschritt; 0.7 ist "
                "nicht das einzige Bottleneck.",
            )
        return (
            "vorläufig behalten",
            "Keine auffälligen Risikoereignisse in vorhandenen Traces; "
            "weitere Persona-Runs nötig.",
        )
    if name == "off_task_relevance_boundary":
        if near_count == 0 and total_turns:
            return (
                "gezielt testen",
                "Vorhandene Simulationen enthalten kaum Grenzfälle um 0.3; "
                "off_topic/lazy Runs nötig.",
            )
        return (
            "prüfen",
            "Es gibt Grenzfälle um 0.3; manuelle Trace-Review empfohlen.",
        )
    if name == "completion_relevance_guard":
        return (
            "vorläufig behalten als Sicherheitsgurt",
            "Completion hängt primär an allen required Core Points; 0.5 "
            "ist sekundär und sollte nur off-topic Voll-Coverage verhindern.",
        )
    return (
        "dokumentieren",
        "Heuristik ist testbar; Empfehlung hängt von Boundary-Tests "
        "und Spezial-Personas ab.",
    )


def render_counter(counter: Counter[str], *, limit: int = 12) -> list[str]:
    """Render a counter as markdown bullet lines."""
    if not counter:
        return ["- none"]
    return [f"- `{key}`: {value}" for key, value in counter.most_common(limit)]


def render_threshold_sensitivity(metrics: list[PersonaMetrics]) -> list[str]:
    """Render alternative higher-level pass threshold decisions."""
    aggregate: dict[str, Counter[str]] = defaultdict(Counter)
    for metric in metrics:
        for key, counter in metric.higher_level_candidate_events.items():
            aggregate[key].update(counter)

    if not aggregate:
        return [
            "- No higher-level candidate events found. Run more "
            "Explain/Apply simulations."
        ]

    lines = [
        "| Rule candidate | Would pass | Would block | Pass rate | Interpretation |",
        "|---|---:|---:|---:|---|",
    ]
    for key in sorted(aggregate):
        would_pass = aggregate[key].get("would_pass", 0)
        would_block = aggregate[key].get("would_block", 0)
        total = would_pass + would_block
        pass_rate = would_pass / total if total else 0.0
        if "@0.90" in key and pass_rate < 0.5:
            interpretation = (
                "strict; likely reduces false positives but may create friction"
            )
        elif "@0.70" in key and pass_rate > 0.9:
            interpretation = "lenient; inspect examples for possible over-crediting"
        else:
            interpretation = "middle ground; compare with manual trace review"
        lines.append(
            f"| `{key}` | {would_pass} | {would_block} | "
            f"{pass_rate:.0%} | {interpretation} |"
        )
    return lines


def render_basic_fairness(metrics: list[PersonaMetrics]) -> list[str]:
    """Render Basic-level fairness signals from the traces."""
    turns_to_pass = [turn for metric in metrics for turn in metric.basic_turns_to_pass]
    overhard = [
        f"{metric.persona}: {event}"
        for metric in metrics
        for event in metric.basic_overhard_events
    ]
    oversoft = [
        f"{metric.persona}: {event}"
        for metric in metrics
        for event in metric.basic_oversoft_events
    ]

    if turns_to_pass:
        summary = (
            f"Basic passed observations: n={len(turns_to_pass)}, "
            f"min_turn={min(turns_to_pass)}, "
            f"mean_turn={statistics.mean(turns_to_pass):.1f}, "
            f"max_turn={max(turns_to_pass)}."
        )
    else:
        summary = "No Basic-pass observations found in analyzed traces."

    lines = [
        summary,
        "",
        "**Potential over-hardness signals** "
        "(high relevance/correctness but Basic not passed):",
        "",
    ]
    lines.extend([f"- {event}" for event in overhard[:20]] or ["- none detected"])
    if len(overhard) > 20:
        lines.append(f"- ... {len(overhard) - 20} more")
    lines.extend(
        [
            "",
            "**Potential over-softness signals** "
            "(Basic passed despite problematic or low-score current turn):",
            "",
        ]
    )
    lines.extend([f"- {event}" for event in oversoft[:20]] or ["- none detected"])
    if len(oversoft) > 20:
        lines.append(f"- ... {len(oversoft) - 20} more")
    lines.extend(
        [
            "",
            "Interpretation: Basic completion is based on cumulative required "
            "core-point coverage, not an arbitrary 80% score. This is "
            "defensible, but high-score over-hardness cases should be manually "
            "reviewed to see whether the LLM failed to mark core-point coverage "
            "or whether the answer was genuinely incomplete.",
        ]
    )
    return lines


def render_report(metrics: list[PersonaMetrics], output_json: Path) -> str:
    """Render a markdown threshold-evaluation report."""
    total_turns = sum(metric.turn_count for metric in metrics)
    completed_all_count = sum(1 for metric in metrics if metric.completed_all)
    aggregate_patterns: Counter[str] = Counter()
    aggregate_actions: Counter[str] = Counter()
    aggregate_normalizations: Counter[str] = Counter()
    aggregate_states: Counter[str] = Counter()
    aggregate_near: Counter[str] = Counter()
    all_risks: list[str] = []
    all_friction: list[str] = []
    all_misconceptions: list[str] = []
    all_unclear: list[str] = []
    for metric in metrics:
        aggregate_patterns.update(metric.validated_patterns)
        aggregate_actions.update(metric.policy_actions)
        aggregate_normalizations.update(metric.llm_to_app_normalizations)
        aggregate_states.update(metric.final_states)
        aggregate_near.update(metric.threshold_near_misses)
        all_risks.extend(
            f"{metric.persona}: {event}" for event in metric.risky_progress_events
        )
        all_friction.extend(
            f"{metric.persona}: {event}" for event in metric.friction_events
        )
        all_misconceptions.extend(
            f"{metric.persona}: {event}" for event in metric.misconception_events
        )
        all_unclear.extend(
            f"{metric.persona}: {event}" for event in metric.unclear_events
        )

    lines = [
        "# Beta AI Threshold Evaluation",
        "",
        "This report evaluates numeric and state-transition heuristics from "
        "the Beta AI Tutor control layer using simulation traces.",
        "",
        "## Data basis",
        "",
        f"- Simulation files analyzed: **{len(metrics)}**",
        f"- Total simulated turns: **{total_turns}**",
        "- Simulations with all concepts completed: "
        f"**{completed_all_count}/{len(metrics)}**",
        f"- Machine-readable companion: `{output_json}`",
        "",
        "### Per-simulation overview",
        "",
        "| Persona/file | Turns | Completed all | Completed concepts | "
        "Final concept states |",
        "|---|---:|---:|---:|---|",
    ]
    for metric in metrics:
        states = (
            ", ".join(f"{key}={value}" for key, value in metric.final_states.items())
            or "n/a"
        )
        lines.append(
            f"| `{metric.persona}` | {metric.turn_count} | "
            f"{metric.completed_all} | {metric.completed_concepts} | "
            f"{states} |"
        )

    lines.extend(
        [
            "",
            "## Aggregate behavior",
            "",
            "### Validated diagnosis patterns",
            "",
            *render_counter(aggregate_patterns),
            "",
            "### Policy actions",
            "",
            *render_counter(aggregate_actions),
            "",
            "### LLM suggestion normalized by app",
            "",
            *render_counter(aggregate_normalizations),
            "",
            "### Scores",
            "",
        ]
    )
    for score_name in ("task_relevance", "correctness", "completeness"):
        values = [
            value
            for metric in metrics
            for value in metric.score_values.get(score_name, [])
        ]
        lines.append(f"- `{score_name}`: {summarize_scores(values)}")

    lines.extend(
        [
            "",
            "### Threshold-near observations (±0.05)",
            "",
            *render_counter(aggregate_near, limit=20),
            "",
            "### Higher-level threshold sensitivity",
            "",
            *render_threshold_sensitivity(metrics),
            "",
            "### Basic-level fairness signals",
            "",
            *render_basic_fairness(metrics),
            "",
            "## Threshold recommendations",
            "",
            "| Heuristic | Current value | Recommendation | Rationale |",
            "|---|---:|---|---|",
        ]
    )
    for name, value in {**SCORE_THRESHOLDS, **OTHER_HEURISTICS}.items():
        recommendation, rationale = recommendation_for_threshold(name, metrics)
        lines.append(f"| `{name}` | `{value}` | **{recommendation}** | {rationale} |")

    lines.extend(
        [
            "",
            "## Key diagnostic findings",
            "",
            "### Possible risky progress / architecture mismatches",
            "",
        ]
    )
    lines.extend(
        [f"- {event}" for event in all_risks[:30]]
        or ["- none detected in analyzed traces"]
    )
    if len(all_risks) > 30:
        lines.append(f"- ... {len(all_risks) - 30} more")

    lines.extend(["", "### Possible friction / over-blocking", ""])
    lines.extend(
        [f"- {event}" for event in all_friction[:30]]
        or ["- none detected in analyzed traces"]
    )
    if len(all_friction) > 30:
        lines.append(f"- ... {len(all_friction) - 30} more")

    lines.extend(["", "### Misconception flow observations", ""])
    lines.extend(
        [f"- {event}" for event in all_misconceptions[:30]]
        or ["- none in analyzed traces; run `misconception` persona"]
    )
    if len(all_misconceptions) > 30:
        lines.append(f"- ... {len(all_misconceptions) - 30} more")

    lines.extend(["", "### Unclear-pattern observations", ""])
    lines.extend(
        [f"- {event}" for event in all_unclear[:30]]
        or ["- none in analyzed traces; targeted unclear simulation needed"]
    )
    if len(all_unclear) > 30:
        lines.append(f"- ... {len(all_unclear) - 30} more")

    lines.extend(
        [
            "",
            "## Interpretation for the Bachelorarbeit",
            "",
            "The current evidence should be framed as engineering calibration, "
            "not as a literature-derived universal threshold proof. Stronger "
            "claims require multiple persona traces, boundary tests, and manual "
            "review of representative turns.",
            "",
            "Preliminary architectural conclusion: required-core-point completion "
            "is more defensible than an arbitrary 80% threshold. Misconception "
            "handling should likely remain an automatic repair loop rather than "
            "moving the concept into a human-review state. The `unclear` "
            "high-score pass rule requires targeted evidence before it can be "
            "justified.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json_summary(metrics: list[PersonaMetrics], output_path: Path) -> None:
    """Write a machine-readable summary for later comparison."""
    payload = {
        "score_thresholds": SCORE_THRESHOLDS,
        "other_heuristics": OTHER_HEURISTICS,
        "simulations": [
            {
                "path": str(metric.path),
                "persona": metric.persona,
                "turn_count": metric.turn_count,
                "completed_all": metric.completed_all,
                "completed_concepts": metric.completed_concepts,
                "final_states": dict(metric.final_states),
                "validated_patterns": dict(metric.validated_patterns),
                "cumulative_patterns": dict(metric.cumulative_patterns),
                "policy_actions": dict(metric.policy_actions),
                "llm_to_app_normalizations": dict(metric.llm_to_app_normalizations),
                "threshold_near_misses": dict(metric.threshold_near_misses),
                "higher_level_candidate_events": {
                    key: dict(counter)
                    for key, counter in metric.higher_level_candidate_events.items()
                },
                "basic_turns_to_pass": metric.basic_turns_to_pass,
                "basic_overhard_events": metric.basic_overhard_events,
                "basic_oversoft_events": metric.basic_oversoft_events,
                "risky_progress_events": metric.risky_progress_events,
                "friction_events": metric.friction_events,
                "misconception_events": metric.misconception_events,
                "unclear_events": metric.unclear_events,
            }
            for metric in metrics
        ],
    }
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def discover_inputs(patterns: list[str]) -> list[Path]:
    """Return existing JSON paths matching CLI patterns."""
    paths: list[Path] = []
    for pattern in patterns:
        matches = sorted(Path().glob(pattern))
        if matches:
            paths.extend(match for match in matches if match.suffix == ".json")
        else:
            candidate = Path(pattern)
            if candidate.exists() and candidate.suffix == ".json":
                paths.append(candidate)
    return sorted(set(paths))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="*",
        default=["tmp/beta_ai_simulation*.json"],
        help="Simulation JSON files or glob patterns.",
    )
    parser.add_argument("--out-md", default="tmp/beta_ai_threshold_evaluation.md")
    parser.add_argument("--out-json", default="tmp/beta_ai_threshold_evaluation.json")
    return parser.parse_args()


def main() -> None:
    """Run threshold evaluation."""
    args = parse_args()
    input_paths = discover_inputs(args.inputs)
    if not input_paths:
        raise SystemExit("No simulation JSON files found.")

    metrics = [analyze_simulation(path) for path in input_paths]
    output_json = Path(args.out_json)
    output_md = Path(args.out_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    write_json_summary(metrics, output_json)
    output_md.write_text(render_report(metrics, output_json), encoding="utf-8")
    print(f"Wrote {output_md} and {output_json}")


if __name__ == "__main__":
    main()
