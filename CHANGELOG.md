# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Removed
- Remove remaining occurrences of the global `UserRole` (deprecated in v2.0.0b1) [#616].

## [2.0.0b2] - 2026-10-26

### Added
- Exercise import: Make prompt optional.  If not set in the import file, the lecture's
  current default prompt will be used.  [#524]
- Manage users: Add search function [#598]


### Fixed
- Make the lecture navigation bar scrollable (was previously cut off if not enough
  screen space) [#603].
- Seed demo data: Mark added users as verified [#601].
- Add/Edit exercises: Apply length limit when uploading a PDF for lesson context [#609].
- Hidden exercises are now visible for tutors and lecture owners again [#608].


### Changed
- Registration: check the registration code first [#514].
- Do not use the global `UserRole` anymore for access checks on pages and state methods
  (#596, #602).
- Add/Edit exercises: More compact display of uploaded filename for lesson context
  [#523].
- Set the number of granian workers in Docker to 1 per CPU core [#599].
- When joining a lecture, one now directly enters it [#604].
- Split lecture list into joined and others for admin users [#611].



## [2.0.0b1] - 2026-10-07

Big beta release with great restructuring.

### Added
- More granular permission system that is to replace `UserRole` [#326].
- Lectures: Support multiple lectures within one AI-Tutor instance.  Users with the
  "lecturer" permission can create new lectures on their own.  All the exercise logic is
  now inside those lectures.
- Email addresses are now verified during registration (#496, #504).


### Fixed
- Fixed some serious security issues.
- Error on the "Token Analyzer" page [#510].


### Changed
- Increased default token limit [#337].


### Deprecated
- `UserRole`: Use the new global permissions instead.


## [1.0.0] - 2026-04-13

Initial release

---

[Unreleased]: https://github.com/martius-lab/ai-tutor/compare/v2.0.0b2...HEAD
[2.0.0b2]: https://github.com/martius-lab/ai-tutor/compare/v2.0.0b1...v2.0.0b2
[2.0.0b1]: https://github.com/martius-lab/ai-tutor/compare/v1.0.0...v2.0.0b1
[1.0.0]: https://github.com/martius-lab/ai-tutor/releases/tag/v1.0.0

[#326]: https://github.com/martius-lab/ai-tutor/pull/326
[#337]: https://github.com/martius-lab/ai-tutor/pull/337
[#496]: https://github.com/martius-lab/ai-tutor/pull/496
[#510]: https://github.com/martius-lab/ai-tutor/pull/510
[#514]: https://github.com/martius-lab/ai-tutor/pull/514
[#523]: https://github.com/martius-lab/ai-tutor/pull/523
[#524]: https://github.com/martius-lab/ai-tutor/pull/524
[#596]: https://github.com/martius-lab/ai-tutor/pull/596
[#598]: https://github.com/martius-lab/ai-tutor/pull/598
[#599]: https://github.com/martius-lab/ai-tutor/pull/599
[#601]: https://github.com/martius-lab/ai-tutor/pull/601
[#603]: https://github.com/martius-lab/ai-tutor/pull/603
[#604]: https://github.com/martius-lab/ai-tutor/pull/604
[#608]: https://github.com/martius-lab/ai-tutor/pull/608
[#609]: https://github.com/martius-lab/ai-tutor/pull/609
[#611]: https://github.com/martius-lab/ai-tutor/pull/611
[#616]: https://github.com/martius-lab/ai-tutor/pull/616
