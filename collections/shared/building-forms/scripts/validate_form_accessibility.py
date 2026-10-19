#!/usr/bin/env python3
"""
Validate Form Accessibility (basic label checks)

Static checks for HTML or JSX/TSX form markup:
- Every form control has an accessible name: <label for/htmlFor>, a wrapping
  <label>, aria-label or aria-labelledby
- Controls marked aria-invalid="true" point to an error message via
  aria-describedby
- aria-labelledby / aria-describedby reference ids that exist in the file

This is a heuristic first pass, not a WCAG audit: it cannot see colour
contrast, focus order, runtime state or labels built dynamically in JSX
expressions. Confirm with an accessibility tool (axe, Lighthouse) and a
screen reader.

Usage:
    python validate_form_accessibility.py form.html [more files or dirs ...]
    python validate_form_accessibility.py ../examples/      # scans *.html, *.htm, *.jsx, *.tsx

Exit codes: 0 pass, 1 errors found (or unreadable input), 2 warnings only.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List
from html.parser import HTMLParser

CONTROL_TAGS = {'input', 'textarea', 'select'}
# Inputs that are not labelled by <label> (they carry their own text or are invisible)
SELF_LABELLED_TYPES = {'hidden', 'submit', 'button', 'reset', 'image'}
SCAN_SUFFIXES = {'.html', '.htm', '.jsx', '.tsx'}


class FormAccessibilityChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inputs: List[Dict] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.label_for = set()
        self.ids = set()
        self.label_depth = 0

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else '') for k, v in attrs}
        if 'id' in a:
            self.ids.add(a['id'])

        if tag == 'label':
            target = a.get('for') or a.get('htmlfor')  # HTMLParser lower-cases htmlFor
            if target:
                self.label_for.add(target)
            self.label_depth += 1
            return

        if tag in CONTROL_TAGS:
            ctype = a.get('type', 'text').lower() if tag == 'input' else tag
            if ctype in SELF_LABELLED_TYPES:
                return
            self.inputs.append({
                'type': ctype,
                'id': a.get('id'),
                'name': a.get('name'),
                'line': self.getpos()[0],
                'wrapped': self.label_depth > 0,
                'aria_label': a.get('aria-label'),
                'aria_labelledby': a.get('aria-labelledby'),
                'aria_describedby': a.get('aria-describedby'),
                'aria_invalid': a.get('aria-invalid'),
            })

    def handle_startendtag(self, tag, attrs):
        # <input ... /> - a void element, so no matching end tag
        self.handle_starttag(tag, attrs)
        if tag == 'label':
            self.label_depth = max(0, self.label_depth - 1)

    def handle_endtag(self, tag):
        if tag == 'label':
            self.label_depth = max(0, self.label_depth - 1)

    @staticmethod
    def _static_ref(value):
        # JSX expressions such as {errorId} cannot be resolved statically
        return value and not value.startswith('{')

    def validate(self):
        for c in self.inputs:
            where = f"line {c['line']}: <{c['type']}" + (f" name={c['name']!r}" if c['name'] else '') + '>'
            labelled = (
                c['wrapped']
                or (c['id'] and c['id'] in self.label_for)
                or c['aria_label']
                or c['aria_labelledby']
            )
            if not labelled:
                self.errors.append(
                    f"{where} has no accessible name. Add <label for/htmlFor=\"id\">, "
                    f"wrap it in <label>, or add aria-label/aria-labelledby."
                )
            for attr in ('aria_labelledby', 'aria_describedby'):
                ref = c[attr]
                if self._static_ref(ref):
                    missing = [i for i in ref.split() if i not in self.ids]
                    if missing:
                        self.warnings.append(
                            f"{where} {attr.replace('_', '-')} references missing id(s): {', '.join(missing)}"
                        )
            if c['aria_invalid'] == 'true' and not c['aria_describedby']:
                self.warnings.append(
                    f"{where} is aria-invalid but has no aria-describedby pointing at its error message."
                )


def validate_file(filepath: Path) -> Dict:
    """Validate form accessibility in one HTML/JSX file"""
    result = {"file": str(filepath), "inputs_found": 0, "errors": [], "warnings": []}
    try:
        content = filepath.read_text(encoding='utf-8')
    except OSError as e:
        result["error"] = f"Error reading file: {e}"
        return result

    checker = FormAccessibilityChecker()
    checker.feed(content)
    checker.close()
    checker.validate()
    result.update(inputs_found=len(checker.inputs), errors=checker.errors, warnings=checker.warnings)
    return result


def print_results(results: Dict):
    print(f"\n{'='*70}")
    print(f"Form Accessibility Check: {results['file']}")
    print(f"{'='*70}\n")

    if results.get("error"):
        print(f"ERROR: {results['error']}\n")
        return

    print(f"Found {results['inputs_found']} labellable form controls\n")
    if results["errors"]:
        print("ERRORS (must fix):\n")
        for error in results["errors"]:
            print(f"  - {error}")
        print()
    if results["warnings"]:
        print("WARNINGS:\n")
        for warning in results["warnings"]:
            print(f"  - {warning}")
        print()
    if results["errors"]:
        status = "FAIL"
    elif results["warnings"]:
        status = "PASS WITH WARNINGS"
    else:
        status = "PASS (basic label checks only - not a full WCAG audit)"
    print(f"Status: {status}\n")


def collect(paths: List[str]) -> List[Path]:
    files: List[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(f for f in p.rglob('*') if f.suffix in SCAN_SUFFIXES))
        else:
            files.append(p)
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Static accessible-name checks for form controls in HTML/JSX/TSX files "
                    "(heuristic; not a full WCAG audit).")
    parser.add_argument('paths', nargs='+', help='files or directories to scan')
    args = parser.parse_args()

    files = collect(args.paths)
    if not files:
        parser.error('no .html/.htm/.jsx/.tsx files found')

    exit_code = 0
    for f in files:
        results = validate_file(f)
        print_results(results)
        if results.get("error") or results["errors"]:
            exit_code = 1
        elif results["warnings"] and exit_code == 0:
            exit_code = 2
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
