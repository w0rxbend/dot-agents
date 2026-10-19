# ZIO Skills Project Instructions

This directory is a vendored copy of the upstream zio-skills project inside dot-agents.

Do not install the upstream skill-attribution git hook (`setup-skill-hook` / `setup-skill-hook.sh`):
its post-commit hook runs `git commit --amend`, which re-triggers post-commit and loops forever.
Make commits normally, without any extra setup step.
