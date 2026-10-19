---
name: pylint-checkers
user-invocable: false
description: Understand Pylint's built-in checkers and optional extensions, and write, register, and test custom checkers on astroid ASTs. Use when enforcing a project-specific rule Pylint lacks, building a Pylint plugin, or interpreting which checker emits a message.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Pylint checkers

Configuration lives in `pylint-configuration`; CI wiring in `pylint-integration`.
Before writing a checker, confirm the rule is not already available:

```bash
pylint --list-msgs | grep -i <keyword>        # all messages, including disabled ones
pylint --list-extensions                       # optional built-in plugins
pylint --help-msg=<symbol>                     # which checker emits a message, and why
```

Also check whether Ruff, a framework plugin (`pylint-django`, `pylint-pytest`), or a
type checker already enforces the rule more cheaply.

## How checkers work

- Pylint parses each module with **astroid**, an AST with inference
  (`node.infer()`, `node.inferred()`), then walks it.
- A checker declares messages and implements `visit_<nodename>` / `leave_<nodename>`
  methods; node names are lowercased astroid class names (`visit_call`,
  `visit_functiondef`, `visit_importfrom`).
- Base classes: `BaseChecker` (AST), `BaseRawFileChecker` (raw file bytes),
  `BaseTokenChecker` (tokens; formatting-style rules).
- Explore node shapes interactively:

```python
import astroid
node = astroid.extract_node("requests.get(url, timeout=5)")
print(node.repr_tree())
```

## A custom checker

Example rule (not built into Pylint): forbid naive `datetime.now()` / `utcnow()`.

```python
# tools/pylint_plugins/naive_datetime.py
import astroid
from astroid import nodes
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter


# CPython 3.12+ implements datetime in _pydatetime; astroid reports that qname.
_DATETIME_QNAMES = frozenset({"datetime.datetime", "_pydatetime.datetime"})


class NaiveDatetimeChecker(BaseChecker):
    name = "naive-datetime"
    msgs = {
        "W9101": (
            "datetime.%s() returns a naive datetime; pass tz=",
            "naive-datetime-now",
            "Naive datetimes silently assume the host time zone.",
        ),
    }

    def visit_call(self, node: nodes.Call) -> None:
        func = node.func
        if not (isinstance(func, nodes.Attribute) and func.attrname in {"now", "utcnow"}):
            return
        if not self._is_datetime_class(func.expr):
            return
        if func.attrname == "now" and (node.args or any(kw.arg == "tz" for kw in node.keywords or ())):
            return
        self.add_message("naive-datetime-now", node=node, args=(func.attrname,))

    @staticmethod
    def _is_datetime_class(expr: nodes.NodeNG) -> bool:
        try:
            return any(
                isinstance(inferred, nodes.ClassDef) and inferred.qname() in _DATETIME_QNAMES
                for inferred in expr.infer()
            )
        except astroid.InferenceError:
            return False


def register(linter: PyLinter) -> None:
    linter.register_checker(NaiveDatetimeChecker(linter))
```

Rules of thumb:
- Message tuple is `(template, symbol, description)`; `args=` fills `%s` placeholders.
- Choose an ID prefix and number range not used by Pylint or other loaded plugins
  (check `--list-msgs`). Users will refer to the **symbol**, so make it descriptive.
- Use inference (as above) so aliased imports (`from datetime import datetime as dt`)
  are caught and unrelated objects with a `now` method are not. Always handle
  `InferenceError`; inference yields `Uninferable` on dynamic code.
- Check qualified names by printing what astroid actually infers on the target
  Python version; stdlib modules can resolve to private implementation modules.
- Prefer false negatives over false positives; noisy checkers get disabled.
- Add `options = (("option-name", {...}),)` for configurable thresholds; read them via
  `self.linter.config.option_name`.
- Keep checkers stateless across modules, or reset state in `open()` / `close()`.

## Loading the plugin

```toml
[tool.pylint.main]
load-plugins = ["naive_datetime"]
# the module must be importable: install it, or add its directory to the path
init-hook = "import sys; sys.path.append('tools/pylint_plugins')"
```

Prefer packaging the plugin (even as a local path dependency) over `init-hook`, so
editors and CI import it the same way. Verify with
`pylint --load-plugins=naive_datetime --list-msgs | grep naive-datetime-now`.

## Testing

```python
import astroid
import pylint.testutils

from naive_datetime import NaiveDatetimeChecker


class TestNaiveDatetimeChecker(pylint.testutils.CheckerTestCase):
    CHECKER_CLASS = NaiveDatetimeChecker

    def test_flags_naive_now(self):
        call = astroid.extract_node(
            """
            from datetime import datetime as dt
            dt.now()  #@
            """
        )
        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="naive-datetime-now", node=call, args=("now",)),
            ignore_position=True,
        ):
            self.checker.visit_call(call)

    def test_accepts_aware_now(self):
        call = astroid.extract_node(
            """
            import datetime
            datetime.datetime.now(tz=datetime.UTC)  #@
            """
        )
        with self.assertNoMessages():
            self.checker.visit_call(call)
```

- `#@` marks the node `extract_node` returns.
- Test the negative cases that matter: aliased imports, a local object with its own
  `now()` method, positional `tz`.
- Finish with an end-to-end run on a fixture file:
  `pylint --load-plugins=naive_datetime --disable=all --enable=naive-datetime-now fixtures/`.

## Useful built-in extensions

Enable via `load-plugins = ["pylint.extensions.<name>"]`:

| Extension | Adds |
| --- | --- |
| `docparams` | docstring parameters/raises/returns must match the signature |
| `mccabe` | `too-complex` cyclomatic complexity |
| `code_style` | `consider-using-tuple`, assignment-expression suggestions |
| `typing` | modern typing syntax suggestions for the configured `py-version` |
| `broad_try_clause` | `try` blocks with too many statements |
| `no_self_use` | methods that could be functions or static methods |
| `redefined_variable_type` | a variable reassigned to a different type |
| `magic_value` | comparisons against unexplained literals |

## Done when

- The checker has unit tests for positive and key negative cases, and an end-to-end
  run on real project code produces no unexpected findings.
- The plugin loads identically in CI, pre-commit, and editors.
- The message symbol and rationale are documented where the team configures Pylint.
