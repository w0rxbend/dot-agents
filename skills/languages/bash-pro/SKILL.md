---
name: bash-pro
description: 'Write, review or harden Bash scripts for automation, CI/CD and system utilities - strict mode, quoting, safe argument parsing, traps, portability across Bash versions and GNU/BSD tools, ShellCheck/shfmt and bats tests. Use when authoring or reviewing a .sh/Bash script; for one-off terminal commands use bash-linux.'
risk: critical
source: community
date_added: '2026-02-27'
---
## Use this skill when

- Writing or reviewing Bash scripts for automation, CI/CD, ops
- Hardening shell scripts for safety, portability

## Do not use this skill when

- Need POSIX-only shell without Bash features
- Complex logic needs higher-level language
- Need Windows-native scripting (PowerShell)

## Instructions

1. Define script inputs, outputs, failure modes.
2. Apply strict mode and safe argument parsing.
3. Write core logic with defensive patterns.
4. Add Bats tests and ShellCheck linting.

## Safety

- Treat input as untrusted; avoid eval and unsafe globbing.
- Prefer dry-run modes before destructive actions.

## Approach

- Always use strict mode `set -Eeuo pipefail` with error trapping
- Quote all variable expansions; prevents word splitting and globbing
- Prefer arrays over unsafe patterns like `for f in $(ls)`
- Use `[[ ]]` for Bash conditionals; fall back to `[ ]` for POSIX compliance
- Parse arguments with `getopts` plus usage function
- Create temporary files and directories with `mktemp` and cleanup traps
- Prefer `printf` over `echo` for predictable output
- Use command substitution `$()`, not backticks
- Structured logging with timestamps, configurable verbosity
- Idempotent scripts with dry-run modes
- Use `shopt -s inherit_errexit` for better error propagation in Bash 4.4+
- Set `IFS=$'\n\t'` to prevent word splitting on spaces
- Validate required environment variables: `: "${VAR:?message}"`
- End option parsing with `--`: `rm -rf -- "$dir"`
- Support `--trace` mode with opt-in `set -x`; wrap secret-handling lines in `set +x` (xtrace prints expanded values)
- Use `xargs -0` with NUL boundaries for safe subprocess orchestration
- Use `readarray`/`mapfile` for safe array population from command output
- Detect script directory: `SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"`
- NUL-safe loops: `find -print0 | while IFS= read -r -d '' file; do ...; done`

## Compatibility & Portability

- Use `#!/usr/bin/env bash` shebang for portability
- Check Bash version at start for 4.4+ features: `(( BASH_VERSINFO[0] > 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 4) ))` (comparing major and minor independently wrongly rejects 5.0-5.3)
- Check required external commands exist: `command -v jq &>/dev/null || exit 1`
- Detect platform: `case "$(uname -s)" in Linux*) ... ;; Darwin*) ... ;; esac`
- Handle GNU vs BSD tool differences (e.g., `sed -i` vs `sed -i ''`)
- Test on all target platforms (Linux, macOS, BSD variants)
- Document minimum versions in script header comments
- Provide fallbacks for platform-specific features
- Avoid bashisms when POSIX compliance is required; document Bash-specific features used

## Readability & Maintainability

- Long-form options in scripts: `--verbose` instead of `-v`
- Naming: snake_case for functions/variables, UPPER_CASE for constants
- Comment-block section headers to organize related functions
- Keep functions under 50 lines; split larger ones
- Consistent indentation (2 or 4 spaces, never tabs mixed with spaces)
- Opening brace on same line: `function_name() {`
- Document function parameters and return values in header comments

## Safety & Security Patterns

- Declare constants `readonly` to prevent accidental modification
- Use `local` for all function variables; avoid polluting global scope
- Wrap external commands in `timeout`: `timeout 30s curl ...` prevents hangs
- Check file permissions before operations: `[[ -r "$file" ]] || exit 1`
- Use process substitution `<(command)` instead of temporary files when possible
- Sanitize user input before use in commands or file operations
- Validate numeric input with pattern matching: `[[ $num =~ ^[0-9]+$ ]]`
- Never use `eval` on user input; build dynamic commands with arrays
- Restrictive umask for sensitive operations: `(umask 077; touch "$secure_file")`
- Log security-relevant operations (authentication, privilege changes, file access)
- Check exit codes of all security-critical operations explicitly

## Performance Optimization

- Avoid subshells in loops; use `while read` instead of `for i in $(cat file)`
- Bash built-ins over external commands: `[[ ]]` instead of `test`, `${var//pattern/replacement}` instead of `sed`
- Batch operations instead of repeated single ones (e.g., one `sed` with multiple expressions)
- Avoid repeated command substitutions; store result in variable once
- Arithmetic expansion `$(( ))` instead of `expr`
- Associative arrays for lookups instead of repeated grepping
- Process large files line-by-line, not whole file in memory
- Use `xargs -P` for parallel processing when operations are independent

## Documentation Standards

- `--help` and `-h` flags showing usage, options, examples
- `--version` flag showing script version and copyright
- Describe every command-line option
- Mark required vs optional arguments clearly in usage message
- Document exit codes: 0 for success, 1 for general errors, specific codes for specific failures
- Prerequisites section listing required commands and versions
- Header comment block: script purpose, author, modification date
- Document environment variables script uses or requires
- Troubleshooting section in help for common issues
- Generate markdown documentation with `shdoc` from special comment formats
- Man pages with `shellman` for system integration
- Architecture diagrams (Mermaid or GraphViz) for complex scripts

## Modern Bash Features (5.x)

- **Bash 5.0**: `EPOCHSECONDS` and `EPOCHREALTIME` (microsecond precision), `BASH_ARGV0`
- **Bash 5.1**: `${var@U}` / `${var@u}` / `${var@L}` case conversion, `${var@K}`, `SRANDOM`
- **Bash 5.2**: `varredir_close` and `patsub_replacement` shell options, `globskipdots`
- Check version before using modern features: `(( BASH_VERSINFO[0] > 5 || (BASH_VERSINFO[0] == 5 && BASH_VERSINFO[1] >= 2) ))`
- `${parameter@Q}` for shell-quoted output (Bash 4.4+)
- `${parameter@E}` for escape sequence expansion (Bash 4.4+)
- `${parameter@P}` for prompt expansion (Bash 4.4+)
- `${parameter@A}` for assignment format (Bash 4.4+)
- `wait -n` waits for any background job (Bash 4.3+)
- `mapfile -d delim` for custom delimiters (Bash 4.4+)

## CI/CD Integration

- **GitHub Actions**: `shellcheck-problem-matchers` for inline annotations
- **Pre-commit hooks**: `.pre-commit-config.yaml` with `shellcheck`, `shfmt`, `checkbashisms`
- **Matrix testing**: Bash 4.4, 5.0, 5.1, 5.2 on Linux and macOS
- **Container testing**: Official bash:5.2 Docker images for reproducible tests
- **Actionlint**: Validate GitHub Actions workflows that use shell scripts
- **Automated releases**: Tag versions, generate changelogs automatically
- **Coverage reporting**: Track test coverage; fail on regressions
- Example workflow: `shellcheck *.sh && shfmt -d *.sh && bats test/`

## Security Scanning & Hardening

- **SAST**: Semgrep with custom rules for shell-specific vulnerabilities
- **Secrets detection**: `gitleaks` or `trufflehog` to prevent credential leaks
- **Supply chain**: Verify checksums of sourced external scripts
- **Sandboxing**: Run untrusted scripts in containers with restricted privileges
- **SBOM**: Document dependencies and external tools for compliance
- **Security linting**: ShellCheck with security-focused rules enabled
- **Privilege analysis**: Audit scripts for unnecessary root/sudo requirements
- **Input sanitization**: Validate all external inputs against allowlists
- **Audit logging**: Log all security-relevant operations to syslog
- **Container security**: Scan script execution environments for vulnerabilities

## Observability & Logging

- **Structured logging**: JSON output for log aggregation systems
- **Log levels**: DEBUG, INFO, WARN, ERROR with configurable verbosity
- **Syslog integration**: `logger` command
- **Distributed tracing**: Trace IDs to correlate multi-script workflows
- **Metrics export**: Prometheus-format metrics for monitoring
- **Error context**: Stack traces, environment info in error logs; redact secrets, never dump full `env`
- **Log rotation**: Rotate log files for long-running scripts
- **Performance metrics**: Execution time, resource usage, external call latency
- Example: `log_info() { logger -t "$SCRIPT_NAME" -p user.info "$*"; echo "[INFO] $*" >&2; }`

## Quality Checklist

- Passes ShellCheck with minimal suppressions
- Formatted consistently with shfmt standard options
- Bats tests cover edge cases
- All variable expansions quoted
- Error handling covers all failure modes with meaningful messages
- EXIT traps clean up temporary resources
- `--help` gives clear usage information
- Input validation prevents injection attacks, handles edge cases
- Portable across target platforms (Linux, macOS)
- Performance adequate for expected workloads and data sizes

## Output

- Test suites in bats-core or shellspec with TAP output
- CI/CD pipeline configurations (GitHub Actions, GitLab CI) for automated testing
- Structured project layout: reusable library functions, dependency management
- Static analysis configuration files (.shellcheckrc, .shfmt.toml, .editorconfig)
- Performance benchmarks, profiling reports for critical workflows
- Migration guides for Bash 3→5 upgrades and legacy modernization
- Package distribution configurations (Homebrew formulas, deb/rpm specs)
- Container images for reproducible execution

## Essential Tools

### Static Analysis & Formatting
- **ShellCheck**: Static analyzer, `enable=all` and `external-sources=true` configuration
- **shfmt**: Formatter, standard config (`-i 2 -ci -bn -sr -kp`)
- **checkbashisms**: Detects bash-specific constructs for portability analysis

### Testing Frameworks
- **bats-core**: Maintained Bats fork, modern features, active development
- **shellspec**: BDD-style framework, rich assertions and mocking
- **shunit2**: xUnit-style framework for shell scripts

### Modern Development Tools
- **bashly**: CLI framework generator
- **bpkg**: Alternative bash package manager, npm-like interface

### CI/CD & Automation
- **Makefile**: Lint, format, test, release automation

## Common Pitfalls to Avoid

- Relying on `set -e` without proper error trapping in complex flows

## Dependency Management

- **Package managers**: `basher` or `bpkg` for shell script dependencies
- **Vendoring**: Copy dependencies into project for reproducible builds
- **Lock files**: Record exact dependency versions
- **Version pinning**: Pin specific versions to prevent breaking changes
- **Dependency isolation**: Separate directories for different dependency sets
- **Update automation**: Dependabot or Renovate
- **Security scanning**: Scan dependencies for known vulnerabilities
- Example: `basher install username/repo@version` or `bpkg install username/repo@<tag>`; never install from an unpinned default branch

## Advanced Techniques

- **Error Context**: `trap 'echo "Error at line $LINENO: exit $?" >&2' ERR` for debugging
- **Safe Temp Handling**: `tmpdir=$(mktemp -d) || exit 1; trap 'rm -rf -- "$tmpdir"' EXIT` (assign before trap, so a failed `mktemp` never deletes an inherited `$tmpdir`)
- **Binary-Safe Arrays**: `readarray -d '' files < <(find . -print0)`
- **Function Returns**: `declare -g result` returns complex data from functions
- **Associative Arrays**: `declare -A config=([host]="localhost" [port]="8080")` for complex data structures
- **Parameter Expansion**: `${filename%.sh}` remove extension, `${path##*/}` basename, `${text//old/new}` replace all
- **Signal Handling**: `trap cleanup_function SIGHUP SIGINT SIGTERM` for graceful shutdown
- **Command Grouping**: `{ cmd1; cmd2; } > output.log` shares redirection; `( cd dir && cmd )` isolates in subshell
- **Co-processes**: `coproc proc { cmd; }; echo "data" >&"${proc[1]}"; read -u "${proc[0]}" result` for bidirectional pipes
- **Here-documents**: in `cat <<-'EOF'`, `-` strips leading tabs; quotes prevent expansion
- **Process Management**: `wait $pid` waits for background job; `jobs -p` lists background PIDs
- **Conditional Execution**: `cmd1 && cmd2` runs cmd2 only if cmd1 succeeds; `cmd1 || cmd2` runs cmd2 if cmd1 fails
- **Brace Expansion**: `touch file{1..10}.txt` creates multiple files
- **Nameref Variables**: `declare -n ref=varname` references another variable (Bash 4.3+)
- **Parallel Execution**: `xargs -P $(nproc) -n 1 command` runs in parallel across CPU cores
- **Structured Output**: `jq -n --arg key "$value" '{key: $key}'` for JSON generation
- **Performance Profiling**: `/usr/bin/time -v` (GNU time; `/usr/bin/time -l` on macOS) for detailed resource usage, or `TIMEFORMAT` for custom timing. Plain `time -v` hits Bash keyword and fails.

## References & Further Reading

### Style Guides & Best Practices
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html) - Covers quoting, arrays, when to use shell
- [Bash Pitfalls](https://mywiki.wooledge.org/BashPitfalls) - Common Bash mistakes and how to avoid them
- [GNU Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html) - Authoritative reference: expansions, builtins, shell options
- [Greg's Bash Guide and FAQ](https://mywiki.wooledge.org/BashGuide) - Practical guide and FAQ from Bash Pitfalls authors
- [Defensive BASH Programming](https://www.kfirlavi.com/blog/2012/11/14/defensive-bash-programming/) - Defensive programming patterns

### Tools & Frameworks
- [ShellCheck](https://github.com/koalaman/shellcheck) - Static analysis tool, extensive wiki
- [shfmt](https://github.com/mvdan/sh) - Formatter, detailed flag documentation
- [bats-core](https://github.com/bats-core/bats-core) - Maintained Bash testing framework
- [shellspec](https://github.com/shellspec/shellspec) - BDD-style shell testing framework
- [bashly](https://bashly.dannyb.co/) - Bash CLI framework generator
- [shdoc](https://github.com/reconquest/shdoc) - Shell script documentation generator

### Security & Advanced Topics
- [Awesome Bash](https://github.com/awesome-lists/awesome-bash) - Curated Bash resources and tools
- [Pure Bash Bible](https://github.com/dylanaraps/pure-bash-bible) - Pure bash alternatives to external commands

## Example

**User request:** "Review `deploy.sh` before we run it in CI."

**Approach:** run `shellcheck -o all deploy.sh` and `shfmt -d deploy.sh`. Check for strict mode with `ERR`/`EXIT` trap, quoted expansions, `--` before user-supplied paths, `--dry-run` path for destructive steps, and `command -v` checks for required tools. Report each finding with file:line and corrected snippet. Then add bats test for any fixed bug.

## Limitations

- Bash only: for POSIX `sh`, PowerShell, or logic outgrowing shell (complex data structures, heavy JSON), say so and suggest different tool.
- Version- and platform-specific advice (Bash 5.x features, GNU vs BSD flags) must be checked against target system's `bash --version` and tool man pages.
