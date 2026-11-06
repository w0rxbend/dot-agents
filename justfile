# dot-agents maintenance tasks. `just --list` shows them; plain `just` runs `check`.
set positional-arguments := true

# Validate the snapshot, test the installer, verify the rendered config
check:
    python3 scripts/validate.py
    python3 -m unittest discover -s tests -v
    ./install.sh render --check

# Run the unit tests only
test:
    python3 -m unittest discover -s tests -v

# Regenerate the readable catalog (docs/catalog.md)
catalog:
    python3 scripts/catalog.py

# Deliberately refresh the snapshot from recognized global roots
import-skills *args:
    python3 scripts/import_skills.py --replace "$@"

# Record skills whose tree changed since review
refresh-review:
    python3 scripts/refresh_review.py

# List the skills that still need review
review:
    python3 scripts/refresh_review.py --list

# Mark skills reviewed: just mark-reviewed all-changed "what was read and why it is fine"
mark-reviewed ids note:
    python3 scripts/refresh_review.py --mark-reviewed "$1" --note "$2"

# Regenerate install.conf.yaml
render:
    ./install.sh render

# Link skills into agents (installer options pass through, e.g. --agents all)
install *args:
    ./install.sh install "$@"

# Remove this repository's skill links (installer options pass through)
uninstall *args:
    ./install.sh uninstall "$@"

# Build the release archive and checksums for VERSION
release:
    python3 scripts/package.py --version "$(cat VERSION)"
