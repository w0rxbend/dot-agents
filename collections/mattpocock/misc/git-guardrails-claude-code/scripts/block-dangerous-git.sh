#!/usr/bin/env bash
# PreToolUse hook for the Bash tool: blocks destructive git commands.
#
# Reads the hook JSON on stdin, splits the command into shell segments
# (; && || | & newlines, subshells, $(...) and backticks), skips VAR=value
# prefixes and keywords (if/then/do...), checks every word after wrappers
# such as env/sudo/xargs/find (their options may take values), looks inside
# `bash -c` / `sh -c` / `eval` strings, strips git global options such as
# `-C <dir>`, then matches the git subcommand and its flags.
# Text inside quoted arguments (for example a commit message) is not treated
# as a command, so `git commit -m 'avoid git push'` is allowed.
#
# Best-effort guard, not a sandbox: git aliases, scripts that run git
# internally, and other obfuscation are not detected. Pair it with
# `permissions.deny` rules in Claude Code settings.
#
# Exit 0 = allow, exit 2 = block (stderr is shown to Claude).
# Fails closed: if jq is missing, the input cannot be parsed, or shells nest
# too deep to inspect, it blocks.

if ! command -v jq >/dev/null 2>&1; then
  echo "BLOCKED: git guardrail hook needs jq to inspect commands, and jq is not installed. Install jq (or remove this hook) to run shell commands." >&2
  exit 2
fi

INPUT=$(cat)
if ! COMMAND=$(printf '%s' "$INPUT" | jq -er '.tool_input.command // ""' 2>/dev/null); then
  echo "BLOCKED: git guardrail hook could not parse the hook input as JSON." >&2
  exit 2
fi

# Parse bytes, not characters: shell metacharacters are ASCII, and per-char
# substrings in a UTF-8 locale are ~5x slower on long commands.
LC_ALL=C

block() {
  echo "BLOCKED: '$COMMAND' runs '$1', which the user has blocked. You do not have authority to run it; ask the user to run it themselves if it is needed." >&2
  exit 2
}

# Split $1 into TOKS; segment boundaries become the token $SEP.
SEP=$'\x01'
VARRE='^\$\{[A-Za-z0-9_]+\}'
tokenize() {
  local s=$1 i=0 n=${#1} c state=none tok="" have=0
  TOKS=()
  while [ "$i" -lt "$n" ]; do
    c=${s:i:1}
    case $state in
      single)
        if [ "$c" = "'" ]; then state=none; else tok+=$c; fi ;;
      double)
        if [ "$c" = '\' ] && [ $((i + 1)) -lt "$n" ]; then
          i=$((i + 1)); tok+=${s:i:1}
        elif [ "$c" = '"' ]; then state=none
        else tok+=$c; fi ;;
      none)
        case $c in
          "'") state=single; have=1 ;;
          '"') state=double; have=1 ;;
          '\')
            if [ $((i + 1)) -lt "$n" ]; then
              i=$((i + 1))
              [ "${s:i:1}" != $'\n' ] && { tok+=${s:i:1}; have=1; }
            fi ;;
          ' ' | $'\t' | '<' | '>')
            [ "$have" = 1 ] && TOKS+=("$tok"); tok=""; have=0 ;;
          ';' | '&' | '|' | '(' | ')' | '`' | '{' | '}' | $'\n')
            # The find/xargs placeholder {} is a plain word.
            if [ "${s:i:2}" = '{}' ]; then tok+='{}'; have=1; i=$((i + 1)); else
            [ "$have" = 1 ] && TOKS+=("$tok"); tok=""; have=0
            TOKS+=("$SEP"); fi ;;
          '$')
            if [ "${s:i+1:1}" = "(" ]; then
              [ "$have" = 1 ] && TOKS+=("$tok"); tok=""; have=0
              TOKS+=("$SEP"); i=$((i + 1))
            elif [[ ${s:i:66} =~ $VARRE ]]; then # ${name} is a plain word
              tok+=${BASH_REMATCH[0]}; have=1; i=$((i + ${#BASH_REMATCH[0]} - 1))
            else tok+=$c; have=1; fi ;;
          *) tok+=$c; have=1 ;;
        esac ;;
    esac
    i=$((i + 1))
  done
  [ "$have" = 1 ] && TOKS+=("$tok")
}

is_whole_tree() {
  case $1 in
    . | ./ | '*' | :/ | ':/*' | ':(top)' | ':(top).') return 0 ;;
  esac
  return 1
}

# Check one git invocation: $@ = arguments after the `git` word.
check_git() {
  local a sub="" args=()
  while [ $# -gt 0 ]; do
    a=$1; shift
    if [ -z "$sub" ]; then
      case $a in
        -C | -c | --git-dir | --work-tree | --namespace | --super-prefix | --config-env) shift ;;
        -*) ;;
        *) sub=$a ;;
      esac
    else
      args+=("$a")
    fi
  done
  [ -z "$sub" ] && return 0

  local force=0 dry=0 hard=0 del=0 bigd=0 staged=0 worktree=0 whole=0 seen_dd=0
  for a in ${args[@]+"${args[@]}"}; do
    if [ "$seen_dd" = 1 ]; then is_whole_tree "$a" && whole=1; continue; fi
    case $a in
      --) seen_dd=1 ;;
      --force) force=1 ;;
      --dry-run) dry=1 ;;
      --hard) hard=1 ;;
      --delete) del=1 ;;
      --staged) staged=1 ;;
      --worktree) worktree=1 ;;
      --*) ;;
      -*)
        case $a in -*f*) force=1 ;; esac
        case $a in -*n*) dry=1 ;; esac
        case $a in -*D*) bigd=1 ;; esac
        case $a in -*d*) del=1 ;; esac
        case $a in -*S*) staged=1 ;; esac
        case $a in -*W*) worktree=1 ;; esac ;;
      *) is_whole_tree "$a" && whole=1 ;;
    esac
  done

  case $sub in
    push) block "git push" ;;
    reset) [ "$hard" = 1 ] && block "git reset --hard" ;;
    clean) [ "$force" = 1 ] && [ "$dry" = 0 ] && block "git clean --force" ;;
    branch)
      { [ "$bigd" = 1 ] || { [ "$del" = 1 ] && [ "$force" = 1 ]; }; } && block "git branch -D" ;;
    checkout)
      { [ "$whole" = 1 ] || [ "$force" = 1 ]; } && block "git checkout . / --force" ;;
    restore)
      [ "$whole" = 1 ] && { [ "$staged" = 0 ] || [ "$worktree" = 1 ]; } && block "git restore ." ;;
  esac
  return 0
}

# Check a command starting at word $1.
check_words() {
  local a
  case ${1##*/} in
    git) shift; check_git "$@" ;;
    bash | sh | zsh | dash | ksh)
      # Options before -c may take values (-o pipefail), so find the -c cluster
      # and check every word after it.
      shift
      while [ $# -gt 0 ]; do
        case $1 in
          --*) ;;
          -*c*) shift; for a in "$@"; do check_command "$a"; done; return 0 ;;
        esac
        shift
      done ;;
    eval) shift; check_command "$*" ;;
  esac
  return 0
}

# Check one segment: $@ = its tokens.
check_segment() {
  local scan=0
  # Skip VAR=value prefixes and shell keywords. Wrapper options may take values
  # (nice -n 5, sudo -u bob, timeout -s KILL 5), so after a wrapper check every
  # later word.
  while [ $# -gt 0 ]; do
    case $1 in [A-Za-z_]*=*) shift; continue ;; esac
    case ${1##*/} in
      '!' | sudo | doas | env | command | exec | nohup | time | nice | xargs | builtin | timeout | find) scan=1; shift ;;
      if | then | elif | else | while | until | do) shift ;;
      *) break ;;
    esac
  done
  while [ $# -gt 0 ]; do
    check_words "$@"
    [ "$scan" = 1 ] || return 0
    case $1 in
      -S?* | -[!-]*S?* | --split-string=*) check_command "${1#*[S=]}" ;;
      -S | -[!-]*S | --split-string) [ $# -gt 1 ] && check_command "$2" ;;
    esac
    shift
  done
  return 0
}

# Check a full command string (recursive for nested shells).
check_command() {
  local depth=${DEPTH:-0}
  [ "$depth" -gt 5 ] && block "more than 5 nested shells (too deep to inspect)"
  DEPTH=$((depth + 1))
  tokenize "$1"
  local toks=(${TOKS[@]+"${TOKS[@]}"}) seg=() t
  for t in ${toks[@]+"${toks[@]}"} "$SEP"; do
    if [ "$t" = "$SEP" ]; then
      [ ${#seg[@]} -gt 0 ] && check_segment "${seg[@]}"
      seg=()
    else
      # Command substitution inside a double-quoted word still runs.
      case $t in *'$('* | *'`'*) check_command "$t" ;; esac
      seg+=("$t")
    fi
  done
  DEPTH=$depth
}

[ -z "$COMMAND" ] && exit 0
DEPTH=0
check_command "$COMMAND"
exit 0
