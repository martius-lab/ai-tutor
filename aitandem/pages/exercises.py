import reflex as rx
from sqlmodel import select
from aitandem.models import Exercise
from typing import List, Optional

def fetch_exercises(session_id: Optional[str] = None) -> List[Exercise]:
    with rx.session() as session:
        exercises = session.exec(select(Exercise)).all()
        return exercises
    
def render_exercise_card(exercise: Exercise) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(exercise.title, size="4"),
            rx.cond(
                exercise.description is not None,
                rx.text(f"Description: {exercise.description}", size="2")
            ),
            rx.cond(
                len(exercise.tags) > 0,
                rx.hstack(
                    rx.text("Tags:", weight="bold"),
                    rx.hstack(
                        *[
                            rx.badge(tag, variant="soft", color_scheme="blue") 
                            for tag in exercise.tags
                        ],
                        spacing="2"
                    )
                )
            ),
            rx.cond(
                exercise.image is not None,
                rx.image(
                    src=exercise.image,
                    width="200px",
                    height="auto",
                    border_radius="md"
                )
            ),
            spacing="2",
            align="start",
        ),
        variant="surface",
        width="100%",
    )