#!/usr/bin/env bash
set -euo pipefail

# Resolve the skill directory regardless of where the skill is installed.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Wiki root is configurable. Override with WIKI_ROOT env var or --root flag.
# Default to ~/dair-wikis so the skill works out of the box on any machine.
WIKI_ROOT="${WIKI_ROOT:-$HOME/dair-wikis}"

usage() {
  echo "Usage: init_wiki.sh <slug> --title \"Readable Title\" [--flavor research|paper|domain|product|person|organization|project] [--root /path/to/wikis]" >&2
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

SLUG="$1"
shift
TITLE=""
FLAVOR="research"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)
      TITLE="${2:-}"
      shift 2
      ;;
    --flavor)
      FLAVOR="${2:-}"
      shift 2
      ;;
    --root)
      WIKI_ROOT="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! "$SLUG" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "Slug must be lowercase kebab-case: $SLUG" >&2
  exit 1
fi

case "$FLAVOR" in
  research|paper|domain|product|person|organization|project) ;;
  *)
    echo "Unsupported flavor: $FLAVOR" >&2
    exit 1
    ;;
esac

if [[ -z "$TITLE" ]]; then
  TITLE="$(echo "$SLUG" | sed 's/-/ /g' | awk '{for (i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')"
fi

mkdir -p "$WIKI_ROOT"
DEST="$WIKI_ROOT/$SLUG"
if [[ -e "$DEST" ]]; then
  echo "Wiki already exists: $DEST" >&2
  exit 1
fi

DATE="$(date +%Y-%m-%d)"

# Build in a temp dir next to DEST and move it into place only when complete,
# so a failure never leaves a half-built wiki behind.
STAGE="$(mktemp -d "$WIKI_ROOT/.${SLUG}.tmp.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/raw" "$STAGE/wiki" "$STAGE/derived" "$STAGE/prompts" "$STAGE/logs" "$STAGE/assets"

render_template() {
  local src="$1"
  local dest="$2"
  local content
  IFS= read -r -d '' content < "$src" || true
  # Plain string substitution with quoted replacements: titles containing
  # / & \ or other sed metacharacters are copied literally.
  content="${content//"{{SLUG}}"/"$SLUG"}"
  content="${content//"{{TITLE}}"/"$TITLE"}"
  content="${content//"{{FLAVOR}}"/"$FLAVOR"}"
  content="${content//"{{DATE}}"/"$DATE"}"
  content="${content//"{{ROOT}}"/"$DEST"}"
  printf '%s' "$content" > "$dest"
}

render_template "$SKILL_DIR/templates/wiki.config.md" "$STAGE/wiki.config.md"
render_template "$SKILL_DIR/templates/index.md" "$STAGE/wiki/index.md"
render_template "$SKILL_DIR/templates/sources.md" "$STAGE/sources.md"
render_template "$SKILL_DIR/templates/maintenance-log.md" "$STAGE/logs/maintenance-log.md"

cp "$SKILL_DIR"/templates/prompts/*.md "$STAGE/prompts/"

mv -T "$STAGE" "$DEST" 2>/dev/null || mv "$STAGE" "$DEST"
trap - EXIT

cat <<EOF
Created wiki:
$DEST

Next:
1. Edit wiki.config.md for the exact purpose and audience.
2. Add source material to raw/.
3. Record sources in sources.md.
4. Compile durable pages under wiki/.
EOF
