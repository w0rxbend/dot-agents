"""Read-only structural gates for historical Scala research artifacts.

Public API: validate_candidate(Path, repository) and
validate_review(review_path, candidate_dir, repository) return list[str].
CLI: python3 -m scripts.scala_research.quality candidate|review PATH
     --repository OWNER/REPO [--candidate PATH]
CLI exits 0 for structural validity, 1 for errors, 2 for invalid invocation.
A valid blocked candidate or revise/blocked review is NOT acceptance. Callers
must inspect status/verdict and hash the entire stopped candidate tree as well
as report.json. Validate only quiescent artifacts: this is not a sandbox against
concurrent malicious filesystem writers.

Producer conventions supplementing research/scala-history/CONTRACT.md:
* coverage.examined_prs: unique positive PR numbers; years_sampled: unique UTC
  years; inspected_source_paths: repository-relative paths;
  substantive_reviewer_exchanges: cited discussion evidence IDs; gaps: strings.
* Evidence timestamps are RFC3339 instants with seconds and explicit timezone;
  window comparisons use UTC. Blob/commit SHAs are lowercase 40-character hex.
  Discussion URLs identify exact comments/reviews. Role basis is substantive
  historical evidence or the literal string "unknown", never a bare role label.
* SKILL.md uses REQUIRED_SECTIONS, with distinct ### happy/good, broken/repair
  (including correction), and negative/should-not-trigger cases under Examples.
  Scalar name/description frontmatter follows scripts.common conventions.
* Reviews declare evaluation_mode: model-based, execution, compiled, executed,
  or mixed. Actual execution modes also need nonempty execution_evidence paths;
  mixed reviews specify each evaluated skill's mode. Evaluation artifact paths
  are relative to the review directory; all symlinks and traversal are rejected.
  Findings cite evidence IDs/URLs or local artifacts; skill_id may be null for
  report-level findings. Medium and higher/error/blocker findings block accept;
  any severity may explicitly set blocking=true.
* Accept requires every citation used by each skill in verified_evidence_ids.
  Non-accept reviews still require nonempty verified citations and evaluations;
  evidence-free blocked reports are valid research outcomes, not reviewed skills.

Passing is NOT source verification, semantic review, compilation, proof of
public repository visibility, attribution/maintainer status, historical build
compatibility, holdout independence, or permission to promote a skill. Content
length/word-count/approval checks are only shallow-content tripwires. Independent
review must reopen sources, verify exact excerpts and roles, challenge inference,
and validate actual behavior. No network, credential reads, artifact writes,
installation or code execution is performed by these validation functions.
"""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
import os
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import unquote, urlsplit

from scripts.common import frontmatter

REPOSITORY = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9_.-]{1,100}')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}')
SKILL_ID = re.compile(r'scala-[a-z0-9]+(?:-[a-z0-9]+)*')
MAX_BYTES = 8 * 1024 * 1024
APPROVAL_WORDS = frozenset('''a all also amazing an and anything approve approved approving
awesome contribution done everything excellent fine for good great happy i is it job lgtm
look looks me merge merged merging nice no nothing of ok okay ready really ship thank thanks
that the these this to very well with wonderful work you your'''.split())


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _substantive(value):
    """A shallow-content tripwire, deliberately NOT a semantic quality score."""
    if not _text(value) or len(value.strip()) < 40:
        return False
    words = set(re.findall(r'[\w-]+', value.casefold()))
    return (len(words) >= 6 and not words <= APPROVAL_WORDS
            and not re.search(r'\b(?:TODO|TBD|lorem ipsum|placeholder)\b', value, re.I))


def _repo(value):
    return (isinstance(value, str) and REPOSITORY.fullmatch(value) is not None
            and value.split('/')[1] not in ('.', '..'))


def _binding(value, repository, at, errors):
    if not _repo(value) or value.casefold() != repository.casefold():
        errors.append(f'{at}.repository: expected repository {repository!r}, without normalization')


def _version(data, at, errors):
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        errors.append(f'{at}.schema_version: require integer 1 (not a boolean)')


def _strings(value, at, errors, *, nonempty=False):
    if not isinstance(value, list):
        errors.append(f'{at}: require an array of nonempty strings')
        return []
    if nonempty and not value:
        errors.append(f'{at}: require at least one entry')
    result = []
    for index, item in enumerate(value):
        if not _text(item):
            errors.append(f'{at}[{index}]: require a nonempty string')
        else:
            result.append(item)
    return result


def _references(value, known, at, errors, *, nonempty=True):
    values = _strings(value, at, errors, nonempty=nonempty)
    seen = set()
    for item in values:
        if item in seen:
            errors.append(f'{at}: duplicate reference {item!r}')
        seen.add(item)
        if item not in known:
            errors.append(f'{at}: unknown reference {item!r}')
    return set(values) & known.keys()


def _records(value, at, errors):
    if not isinstance(value, list):
        errors.append(f'{at}: require an array of objects with unique IDs')
        return {}
    records, seen = {}, set()
    for index, item in enumerate(value):
        where = f'{at}[{index}]'
        if not isinstance(item, dict):
            errors.append(f'{where}: require an object')
            continue
        identifier = item.get('id')
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            errors.append(f'{where}.id: require a nonempty safe identifier of at most 128 characters')
        elif identifier.casefold() in seen:
            errors.append(f'{where}.id: duplicate ID {identifier!r}')
        else:
            records[identifier] = item
            seen.add(identifier.casefold())
    return records


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key {key!r}')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f'nonfinite JSON number {value!r} is not allowed')


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        _invalid_constant(value)
    return number


def _has_symlink(path):
    return any(part.is_symlink() for part in (path, *path.absolute().parents))


def _read(path, errors):
    try:
        if _has_symlink(path):
            raise ValueError('symlink file or parent directory is forbidden')
        mode = path.lstat().st_mode
        if not stat.S_ISREG(mode):
            raise ValueError('require a regular file, not a symlink or special file')
        with path.open('rb') as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError(f'file exceeds {MAX_BYTES}-byte structural validation limit')
        return data
    except (OSError, ValueError) as error:
        errors.append(f'{path}: cannot read artifact: {error}')
        return None


def _json(path, errors):
    raw = _read(path, errors)
    if raw is None:
        return None
    try:
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant, parse_float=_finite_float)
        if not isinstance(data, dict):
            raise ValueError('require a JSON object')
        return data
    except (ValueError, UnicodeError, RecursionError) as error:
        errors.append(f'{path}: invalid JSON: {error}')
        return None


def _tree(root, errors):
    """Fail closed on symlinks, including unused links, without following them."""
    try:
        if _has_symlink(root) or not root.is_dir():
            errors.append(f'{root}: require a real candidate directory, not a symlink')
            return False
        for parent, dirs, files in os.walk(root, followlinks=False,
                                           onerror=lambda e: errors.append(f'{root}: {e}')):
            for name in dirs + files:
                path = Path(parent) / name
                mode = path.lstat().st_mode
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    errors.append(f'{path}: symlinks and special files are forbidden in candidate artifacts')
        return not errors
    except (OSError, ValueError) as error:
        errors.append(f'{root}: cannot inspect artifact tree: {error}')
        return False


def _report(candidate_dir, repository, errors):
    if not _repo(repository):
        errors.append('repository: require literal OWNER/REPO, without whitespace, URL or traversal')
        return None
    if not _tree(candidate_dir, errors):
        return None
    report = _json(candidate_dir / 'report.json', errors)
    if report is None:
        return None
    _version(report, 'report.json', errors)
    _binding(report.get('repository'), repository, 'report.json', errors)
    if report.get('status') not in ('complete', 'blocked'):
        errors.append('report.json.status: require complete or blocked')
    if not _substantive(report.get('summary')):
        errors.append('report.json.summary: provide a substantive outcome, not an approval or placeholder')
    _strings(report.get('gaps'), 'report.json.gaps', errors,
             nonempty=report.get('status') == 'blocked')
    if report.get('status') == 'blocked' and not report.get('gaps'):
        errors.append('report.json: blocked outcomes require explicit gaps')
    return report


SHA = re.compile(r'[0-9a-f]{40}')
TIMESTAMP = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', re.ASCII)
DISCUSSION = ('review-comment', 'issue-comment', 'review')
EVIDENCE_KINDS = DISCUSSION + ('code', 'commit', 'documentation')


def _relative_path(value):
    if not _text(value) or value != value.strip():
        return False
    if any(ord(c) < 32 or ord(c) == 127 for c in value) or any(c in value for c in '\\:%?#'):
        return False
    return not value.startswith('/') and all(part not in ('', '.', '..') for part in value.split('/'))


def _instant(value):
    """Parse a TIMESTAMP-shaped string; pad the fraction (Python 3.10 accepts only 3 or 6 digits)."""
    text = value.replace('Z', '+00:00')
    match = re.fullmatch(r'(.*T\d{2}:\d{2}:\d{2})\.(\d{1,6})(.*)', text)
    if match:
        text = f'{match[1]}.{match[2].ljust(6, "0")}{match[3]}'
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def _occurred_at(value, at, errors):
    try:
        if not isinstance(value, str) or not TIMESTAMP.fullmatch(value):
            raise ValueError('use an RFC3339 timestamp with seconds and an explicit timezone')
        if value.endswith('-00:00'):
            raise ValueError('unknown timezone -00:00 is not an explicit historical instant')
        # fromisoformat accepts offset minute overflow; check the lexical bounds too.
        if value[-1] != 'Z' and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
            raise ValueError('invalid timezone offset')
        instant = _instant(value)
        if not datetime(2018, 1, 1, tzinfo=timezone.utc) <= instant < datetime(2025, 1, 1, tzinfo=timezone.utc):
            raise ValueError('outside inclusive UTC years 2018-2024')
        return instant
    except (ValueError, OverflowError) as error:
        errors.append(f'{at}.occurred_at: {error}')
        return None


def _source_url(record, repository, at, errors):
    """Validate URL provenance *shape*, never assert remote existence or visibility."""
    value, kind = record.get('url'), record.get('kind')
    try:
        if not _text(value) or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError('require a whitespace-free original GitHub HTTPS URL')
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or parsed.netloc != 'github.com' or parsed.query:
            raise ValueError('require https://github.com with no credentials, port or query')
        decoded = unquote(parsed.path, errors='strict')
        if not decoded.startswith('/') or not _relative_path(decoded[1:]):
            raise ValueError('URL path must not contain traversal, encoded separators or unsafe characters')
        # Encoded slashes can disguise path components before normalization.
        if re.search(r'%2f|%5c', parsed.path, re.I):
            raise ValueError('URL path must not encode separators')
        parts = decoded[1:].split('/')
        if len(parts) < 4 or '/'.join(parts[:2]).casefold() != repository.casefold():
            raise ValueError(f'URL repository must be {repository}')
        route, target = parts[2:4]
        anchor = None
        if kind in ('code', 'documentation'):
            if route != 'blob' or not SHA.fullmatch(target) or len(parts) < 5:
                raise ValueError('code/documentation URL must use /blob/<full lowercase 40-character SHA>/<path>')
            path = '/'.join(parts[4:])
            if kind == 'code' or 'commit_sha' in record:
                if record.get('commit_sha') != target:
                    raise ValueError('commit_sha must exactly match URL full SHA')
            if kind == 'code' or 'path' in record:
                if record.get('path') != path:
                    raise ValueError('path must exactly match the decoded URL source path')
            if parsed.fragment and not re.fullmatch(r'L[1-9]\d*(?:-L[1-9]\d*)?', parsed.fragment):
                raise ValueError('source URL fragment must identify GitHub source lines')
            if '-' in parsed.fragment:
                start, end = (int(n) for n in re.findall(r'\d+', parsed.fragment))
                if start > end:
                    raise ValueError('source URL line range is reversed')
            anchor = ('commit', target)
        elif kind == 'commit':
            if route != 'commit' or not SHA.fullmatch(target) or len(parts) != 4:
                raise ValueError('commit URL must pin one full lowercase 40-character SHA')
            if 'commit_sha' in record and record['commit_sha'] != target:
                raise ValueError('commit_sha must match URL')
            if parsed.fragment and not re.fullmatch(r'diff-[0-9a-f]+(?:[LR][1-9]\d*)?', parsed.fragment):
                raise ValueError('unexpected commit URL fragment')
            anchor = ('commit', target)
        elif kind in DISCUSSION:
            if route not in ('pull', 'issues') or len(parts) != 4 or not re.fullmatch(r'[1-9]\d*', target):
                raise ValueError('discussion URL must identify one PR/issue and its exact comment/review')
            fragment = {'review-comment': r'discussion_r[1-9]\d*',
                        'issue-comment': r'issuecomment-[1-9]\d*',
                        'review': r'pullrequestreview-[1-9]\d*'}[kind]
            if (kind != 'issue-comment' and route != 'pull') or not re.fullmatch(fragment, parsed.fragment):
                raise ValueError(f'{kind} URL must have its exact GitHub comment/review fragment')
            if route == 'pull':
                anchor = ('pull', int(target))
            if 'pull_number' in record and (type(record['pull_number']) is not int or record['pull_number'] != int(target)):
                raise ValueError('pull_number must match the URL PR number')
        return anchor
    except (ValueError, UnicodeError) as error:
        errors.append(f'{at}.url: {error}')
        return None


def _validate_evidence(evidence, repository, errors):
    anchors, dates = {}, {}
    urls = set()
    for identifier, record in evidence.items():
        at = f'evidence[{identifier}]'
        _binding(record.get('repository'), repository, at, errors)
        if record.get('kind') not in EVIDENCE_KINDS:
            errors.append(f'{at}.kind: require one of {", ".join(EVIDENCE_KINDS)}')
        dates[identifier] = _occurred_at(record.get('occurred_at'), at, errors)
        anchors[identifier] = _source_url(record, repository, at, errors)
        excerpt = record.get('excerpt')
        if not _text(excerpt) or len(excerpt) > 1600:
            errors.append(f'{at}.excerpt: require a short attributable quotation (1-1600 characters)')
        if not _substantive(record.get('interpretation')):
            errors.append(f'{at}.interpretation: explain what this source supports, separately from the excerpt')
        if record.get('kind') in DISCUSSION:
            if not _substantive(excerpt):
                errors.append(f'{at}.excerpt: discussion must contain substantive reasoning, not approval-only text')
            if not _text(record.get('author')):
                errors.append(f'{at}.author: require attributed GitHub author; do not invent identity')
            if record.get('role_basis') != 'unknown' and not _substantive(record.get('role_basis')):
                errors.append(f'{at}.role_basis: supply a substantive historical role basis or explicitly unknown, not a role label')
        if record.get('kind') == 'code':
            if not isinstance(record.get('commit_sha'), str) or not SHA.fullmatch(record['commit_sha']):
                errors.append(f'{at}.commit_sha: require full lowercase 40-character SHA')
            if not _relative_path(record.get('path')):
                errors.append(f'{at}.path: require a safe repository-relative source/test path')
        url = record.get('url')
        if isinstance(url, str):
            if url in urls:
                errors.append(f'{at}.url: duplicate source URL cannot inflate independent evidence')
            urls.add(url)
    return anchors, dates


# Discussion kind -> (cached PR artifact group, URL fragment prefix, timestamp field).
CACHED_DISCUSSION = {'review-comment': ('review_comments', 'discussion_r', 'created_at'),
                     'issue-comment': ('issue_comments', 'issuecomment-', 'created_at'),
                     'review': ('reviews', 'pullrequestreview-', 'submitted_at')}
MAX_CORPUS_BYTES = 64 * 1024 * 1024
ELLIPSIS = re.compile(r'\s*(?:\[\.\.\.\]|\.\.\.|\u2026)\s*')


def _normalized(text):
    return ' '.join(text.split())


def _corpus_pull(corpus_dir, numbers, errors):
    """PR number -> cached collector artifacts, for the cited numbers only."""
    index = _json(corpus_dir / 'index.json', errors)
    found = {}
    if index is None:
        return found
    for entry in (index.get('pulls') or []) + (index.get('activity_pulls') or []):
        if (not isinstance(entry, dict) or entry.get('number') not in numbers
                or type(entry.get('number')) is not int or not _relative_path(entry.get('path'))):
            continue
        path = corpus_dir / entry['path']
        try:
            if _has_symlink(path) or path.stat().st_size > MAX_CORPUS_BYTES:
                raise ValueError('symlinked or oversized cached artifact')
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError, UnicodeError) as error:
            errors.append(f'corpus {entry["path"]}: cannot read cached PR artifact: {error}')
            continue
        if isinstance(data, dict):
            found.setdefault(entry['number'], []).append(data)
    return found


def _corpus_evidence(evidence, anchors, dates, corpus_dir, errors):
    """Cross-check discussion evidence against cached PR artifacts when they exist.

    Evidence for a PR outside the cached sample is left to the independent reviewer.
    """
    cited = {}
    for identifier, record in evidence.items():
        anchor = anchors.get(identifier)
        if record.get('kind') in CACHED_DISCUSSION and anchor and anchor[0] == 'pull':
            cited.setdefault(anchor[1], []).append(identifier)
    if not cited:
        return
    artifacts = _corpus_pull(Path(corpus_dir), set(cited), errors)
    for number, identifiers in sorted(cited.items()):
        for identifier in identifiers if number in artifacts else []:
            record, at = evidence[identifier], f'evidence[{identifier}]'
            group, prefix, field = CACHED_DISCUSSION[record['kind']]
            comment = int(urlsplit(record['url']).fragment.removeprefix(prefix))
            rows = [(artifact, row) for artifact in artifacts[number] for row in artifact.get(group) or []
                    if isinstance(row, dict) and row.get('id') == comment]
            if not rows:
                errors.append(f'{at}: {record["kind"]} {comment} is not in cached PR #{number}; '
                              'cite only retrieved records')
                continue
            artifact, row = rows[0]
            eligible = ((artifact.get('historical') or {}).get('eligible_ids') or {}).get(group) or []
            if comment not in eligible:
                errors.append(f'{at}: cached {record["kind"]} {comment} is outside 2018-2024 or edited after cutoff')
            body = _normalized(row.get('body') or '') if isinstance(row.get('body'), str) else ''
            fragments = [_normalized(part) for part in ELLIPSIS.split(record.get('excerpt') or '') if part.strip()]
            if not fragments or any(part not in body for part in fragments):
                errors.append(f'{at}.excerpt: not a quotation of the cached {record["kind"]} body')
            try:
                cached = _instant(row[field]) if isinstance(row.get(field), str) else None
            except ValueError:
                cached = None
            if dates.get(identifier) is not None and cached is not None and dates[identifier] != cached:
                errors.append(f'{at}.occurred_at: cached {field} is {row[field]}')
            login = (row.get('user') or {}).get('login') if isinstance(row.get('user'), dict) else None
            author = record.get('author')
            if isinstance(login, str) and isinstance(author, str) and author.lstrip('@').casefold() != login.casefold():
                errors.append(f'{at}.author: cached author is {login}')


def _claim_basis(claims, evidence, errors):
    for identifier, claim in claims.items():
        refs = claim.get('evidence_ids', [])
        records = [evidence[item] for item in refs if isinstance(item, str) and item in evidence] if isinstance(refs, list) else []
        discussion = any(e.get('kind') in DISCUSSION and _substantive(e.get('excerpt')) for e in records)
        words = ' '.join(claim.get(key, '') for key in ('rule', 'applicability') if isinstance(claim.get(key), str))
        preference = (claim.get('kind') == 'review-preference' or claim.get('review_preference') is True
                      or re.search(r'\b(?:reviewers?|maintainers?|creators?)\b.{0,80}\b(?:prefer\w*|require\w*|recommend\w*|insist\w*|expect\w*|ask\w*|reject\w*)\b', words, re.I))
        if preference and not discussion:
            errors.append(f'claims[{identifier}]: review-preference claims require substantive review/discussion evidence')
        if not discussion and not re.search(r'\b(?:inference|inferred)\b', words, re.I):
            errors.append(f'claims[{identifier}]: label source-only rules as inference in rule or applicability')


def _coverage(coverage, evidence, anchors, dates, errors):
    if not isinstance(coverage, dict):
        return
    for key in ('examined_prs', 'years_sampled'):
        values = coverage.get(key)
        if not isinstance(values, list) or any(type(v) is not int for v in values):
            errors.append(f'coverage.{key}: require an array of integers, not booleans or counts')
            continue
        if len(values) != len(set(values)) or any(v < 1 for v in values):
            errors.append(f'coverage.{key}: require unique positive integers')
        if key == 'years_sampled' and any(not 2018 <= v <= 2024 for v in values):
            errors.append('coverage.years_sampled: years must be within 2018-2024')
        needed = ({a[1] for a in anchors.values() if a and a[0] == 'pull'} if key == 'examined_prs'
                  else {d.year for d in dates.values() if d is not None})
        if not needed <= set(values):
            errors.append(f'coverage.{key}: omitted cited values {sorted(needed - set(values))}')
    paths = _strings(coverage.get('inspected_source_paths'), 'coverage.inspected_source_paths', errors)
    if any(not _relative_path(p) for p in paths):
        errors.append('coverage.inspected_source_paths: unsafe repository-relative path')
    needed_paths = {e['path'] for e in evidence.values() if e.get('kind') == 'code' and isinstance(e.get('path'), str)}
    if not needed_paths <= set(paths):
        errors.append(f'coverage.inspected_source_paths: omitted cited paths {sorted(needed_paths - set(paths))}')
    discussions = {key: value for key, value in evidence.items() if value.get('kind') in DISCUSSION}
    _references(coverage.get('substantive_reviewer_exchanges'), discussions,
                'coverage.substantive_reviewer_exchanges', errors, nonempty=False)
    _strings(coverage.get('gaps'), 'coverage.gaps', errors)


def _validate_report(report, repository, errors):
    evidence = _records(report.get('evidence'), 'report.json.evidence', errors)
    claims = _records(report.get('claims'), 'report.json.claims', errors)
    skills = _records(report.get('skills'), 'report.json.skills', errors)
    if report.get('status') == 'complete':
        for name, records in (('evidence', evidence), ('claims', claims), ('skills', skills)):
            if not records:
                errors.append(f'report.json.{name}: complete candidates require nonempty {name}')
    seen = set()
    for records in (evidence, claims, skills):
        for identifier in records:
            if identifier.casefold() in seen:
                errors.append(f'report.json: duplicate ID across record types: {identifier!r}')
            seen.add(identifier.casefold())
    for identifier, record in evidence.items():
        _binding(record.get('repository'), repository, f'evidence[{identifier}]', errors)
    for identifier, claim in claims.items():
        for field in ('rule', 'applicability', 'counterexample'):
            if not _substantive(claim.get(field)):
                errors.append(f'claims[{identifier}].{field}: provide a concrete decision, boundary or example')
        _references(claim.get('evidence_ids'), evidence, f'claims[{identifier}].evidence_ids', errors)
    for identifier, skill in skills.items():
        if not SKILL_ID.fullmatch(identifier) or len(identifier) > 100:
            errors.append(f'skills[{identifier}].id: use a focused lowercase scala- name, no paths')
        if skill.get('kind') not in ('development', 'review', 'refactoring', 'hardening', 'organization'):
            errors.append(f'skills[{identifier}].kind: unknown skill kind')
        _references(skill.get('claim_ids'), claims, f'skills[{identifier}].claim_ids', errors)
    if not isinstance(report.get('coverage'), dict):
        errors.append('report.json.coverage: require an object describing examined PRs, exchanges, years, paths and gaps')
    return evidence, claims, skills


REQUIRED_SECTIONS = ('When to Use', 'When Not to Use', 'Prerequisites', 'Workflow',
                     'Review and Refactoring Checks', 'Validation', 'Examples',
                     'Output Contract', 'Limitations', 'Sources')


def _decode(path, errors):
    raw = _read(path, errors)
    if raw is None:
        return None
    try:
        return raw.decode('utf-8').replace('\r\n', '\n')
    except UnicodeError as error:
        errors.append(f'{path}: require UTF-8 text: {error}')
        return None


def _prose(text):
    """Mask fenced code while preserving positions for heading and link scans."""
    text = re.sub(r'<!--.*?(?:-->|\Z)', lambda m: re.sub(r'[^\n]', ' ', m[0]), text, flags=re.S)
    result, fence = [], None
    for line in text.splitlines(keepends=True):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            result.append(' ' * (len(line) - int(line.endswith('\n'))) + ('\n' if line.endswith('\n') else ''))
        elif match:
            fence = match[1]
            result.append(' ' * (len(line) - int(line.endswith('\n'))) + ('\n' if line.endswith('\n') else ''))
        else:
            result.append(line)
    return ''.join(result)


def _sections(text, level, at, errors):
    headings = list(re.finditer(r'^ {0,3}' + '#' * level + r'[ \t]+([^\n]+)\n?', _prose(text), re.M))
    sections = {}
    for index, match in enumerate(headings):
        title = match[1].rstrip('#').strip().casefold()
        if title in sections:
            errors.append(f'{at}: duplicate heading {title!r}')
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        sections[title] = text[match.end():end]
    return sections


def _local_file(base, value, at, errors):
    """Resolve relative artifact paths without permitting any symlink component."""
    if not _relative_path(value):
        errors.append(f'{at}: unsafe relative path {value!r}; no traversal, absolute paths, encodings or schemes')
        return None
    path = base.joinpath(*PurePosixPath(value).parts)
    try:
        current = base
        for part in PurePosixPath(value).parts:
            current /= part
            if current.is_symlink():
                raise ValueError('symlink path components are forbidden')
        path.resolve(strict=True).relative_to(base.resolve(strict=True))
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('linked artifact must be a regular file')
        return path
    except (ValueError, OSError, RuntimeError) as error:
        errors.append(f'{at}: missing or unsafe linked file {value!r}: {error}')
        return None


def _links(text, path, skill_root, errors):
    prose = _prose(text)
    definitions = {}
    destinations = []
    for match in re.finditer(r'^ {0,3}\[([^]\n]+)\]:\s*(<[^>]+>|\S+)', prose, re.M):
        label = match[1].casefold()
        if label in definitions:
            errors.append(f'{path}: duplicate link definition {label!r}')
        definitions[label] = match[2].strip('<>')
        destinations.append((definitions[label], False))
    for match in re.finditer(r'!?\[[^]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"\'][^\n]*?[\"\'])?\s*\)', prose):
        destinations.append((match[1].strip('<>'), True))
    for match in re.finditer(r'!?\[([^]\n]+)\]\[([^]\n]*)\]', prose):
        label = (match[2] or match[1]).casefold()
        if label not in definitions:
            errors.append(f'{path}: undefined reference link {label!r}')
        else:
            destinations.append((definitions[label], True))
    for match in re.finditer(r'\[([^]\n]+)\](?![\[(:])', prose):
        label = match[1].casefold()
        if label in definitions:
            destinations.append((definitions[label], True))
    # HTML href/src should not offer an escape hatch around Markdown checks.
    destinations.extend((m[1], True) for m in re.finditer(r'(?:href|src)\s*=\s*[\"\']([^\"\']+)[\"\']', prose, re.I))
    resolved = set()
    for target, used in destinations:
        try:
            parsed = urlsplit(target)
            if parsed.scheme in ('http', 'https') and parsed.netloc:
                continue
            if parsed.scheme or parsed.netloc or parsed.query:
                raise ValueError('local link must be relative and contain no scheme, host or query')
            if not parsed.path and parsed.fragment:
                continue
            value = unquote(parsed.path, errors='strict')
            if re.search(r'%2f|%5c', parsed.path, re.I):
                raise ValueError('encoded link separators are forbidden')
            linked = _local_file(path.parent, value, f'{path}: link', errors)
            if linked is not None:
                linked.resolve().relative_to(skill_root.resolve())
                if used:
                    resolved.add(linked.resolve())
        except (ValueError, UnicodeError, OSError, RuntimeError) as error:
            errors.append(f'{path}: unsafe link {target!r}: {error}')
    return resolved


def _skill_markdown(path, identifier, errors):
    text = _decode(path, errors)
    if text is None:
        return
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        errors.append(f'{path}: require terminated YAML frontmatter')
        return
    head, _, body = text[4:].partition('\n---\n')
    keys = re.findall(r'^([A-Za-z_][\w-]*):', head, re.M)
    if len(keys) != len(set(keys)):
        errors.append(f'{path}: duplicate frontmatter keys')
    try:
        metadata = frontmatter(path)
        if metadata['name'] != identifier:
            errors.append(f'{path}: frontmatter name must match directory and skill ID {identifier!r}')
        if not _substantive(metadata['description']) or metadata['description'].startswith(('|', '>')):
            errors.append(f'{path}: description must be a precise single-line scalar trigger, not a YAML block')
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(f'{path}: invalid frontmatter: {error}')
    sections = _sections(body, 2, str(path), errors)
    for heading in REQUIRED_SECTIONS:
        if not _substantive(_prose(sections.get(heading.casefold(), ''))):
            errors.append(f'{path}: ## {heading} must contain actionable, non-placeholder content')
    prerequisites = sections.get('prerequisites', '')
    if not re.search(r'\b(?:versions?|Scala [23]|ZIO [12]|Cats Effect [23])\b', prerequisites, re.I):
        errors.append(f'{path}: Prerequisites must explain version detection/applicability')
    checks = sections.get('review and refactoring checks', '')
    if not re.search(r'\b(?:invariant|preserv\w*)\b', checks, re.I):
        errors.append(f'{path}: Review and Refactoring Checks must identify preserved invariants')
    if not re.search(r'false[- ]positives?', body, re.I):
        errors.append(f'{path}: include explicit false-positive warnings')
    validation = sections.get('validation', '')
    if ('`' not in validation or not re.search(r'\b(?:sbt|millw?|scala(?:-cli)?|mvn|gradlew?)\b', validation)
            or not re.search(r'\b(?:test\w*|check\w*|compile\w*|verify)\b', validation, re.I)):
        errors.append(f'{path}: Validation must show concrete repository build/test commands; reviewer must verify them')
    output = sections.get('output contract', '')
    for token in ('file:line', 'severity', 'evidence', 'test'):
        if token not in output.casefold():
            errors.append(f'{path}: Output Contract must include {token}')
    examples = _sections(sections.get('examples', ''), 3, f'{path}: Examples', errors)
    example_titles = set()
    for label, pattern in (('happy', r'\b(?:happy|good|positive)\b'),
                           ('broken with correction', r'\b(?:broken|bad|repair)\b'),
                           ('negative / should-not-trigger', r'\bnegative\b|should.not.trigger|non.trigger')):
        matching = [(title, content) for title, content in examples.items() if re.search(pattern, title, re.I)]
        example_titles.update(title for title, _ in matching)
        if not matching or not any(_substantive(content) for _, content in matching):
            errors.append(f'{path}: Examples require a substantive ### {label} case')
        elif label.startswith('broken') and not any(re.search(r'\b(?:correction|corrected|correct|fix(?:ed|es|ing)?|repair(?:ed|s|ing)?)\b', content, re.I) for _, content in matching):
            errors.append(f'{path}: broken example must show an explicit correction/repair')
    if len(example_titles) < 3:
        errors.append(f'{path}: Examples require three distinct happy/broken/negative cases')
    linked = _links(body, path, path.parent, errors)
    if (path.parent / 'references/evidence.json').resolve() not in linked:
        errors.append(f'{path}: include a relative link to references/evidence.json')
    for extra in sorted(path.parent.rglob('*.md')):
        if extra != path:
            extra_text = _decode(extra, errors)
            if extra_text is not None:
                _links(extra_text, extra, path.parent, errors)


def _skill_sources(skill, claims, evidence):
    refs = skill.get('claim_ids', [])
    used_claims = {key: claims[key] for key in refs if isinstance(key, str) and key in claims} if isinstance(refs, list) else {}
    used_evidence = {}
    for claim in used_claims.values():
        refs = claim.get('evidence_ids', [])
        if isinstance(refs, list):
            used_evidence.update({key: evidence[key] for key in refs if isinstance(key, str) and key in evidence})
    return used_claims, used_evidence


def _skill_artifacts(candidate_dir, repository, skills, claims, evidence, anchors, errors):
    root = candidate_dir / 'skills'
    try:
        if root.exists():
            for path in sorted(root.iterdir()):
                if path.name not in skills or not path.is_dir():
                    errors.append(f'{path}: unreported skill artifact; every skill directory must occur in report.json')
    except OSError as error:
        errors.append(f'{root}: cannot inspect skill directories: {error}')
    for identifier, skill in skills.items():
        if not SKILL_ID.fullmatch(identifier) or len(identifier) > 100:
            continue  # Never use unvalidated identifiers as local paths.
        directory = root / identifier
        _skill_markdown(directory / 'SKILL.md', identifier, errors)
        used_claims, used_evidence = _skill_sources(skill, claims, evidence)
        if len(used_evidence) < 3:
            errors.append(f'skills[{identifier}]: cite at least three distinct evidence records through claims')
        histories = {anchors[key] for key in used_evidence if anchors.get(key) is not None}
        if len(histories) < 2:
            errors.append(f'skills[{identifier}]: evidence must span at least two historical PRs/commits')
        if not any(e.get('kind') == 'code' and isinstance(e.get('path'), str)
                   and PurePosixPath(e['path']).suffix in ('.scala', '.sc', '.java', '.sbt') for e in used_evidence.values()):
            errors.append(f'skills[{identifier}]: include actual source/test code evidence, not just discussion or documentation')
        path = directory / 'references/evidence.json'
        local = _json(path, errors)
        if local is None:
            continue
        _version(local, str(path), errors)
        _binding(local.get('repository'), repository, str(path), errors)
        for field, wanted in (('claims', used_claims), ('evidence', used_evidence)):
            actual = _records(local.get(field), f'{path}.{field}', errors)
            # JSON equality preserves scalar types (True must not equal 1).
            if json.dumps(actual, sort_keys=True) != json.dumps(wanted, sort_keys=True):
                errors.append(f'{path}.{field}: must exactly match report records used by this skill; no omissions, additions or edits')


def validate_candidate(candidate_dir: Path, repository: str, corpus: Path | None = None) -> list[str]:
    """Return structural errors; [] also permits a well-formed blocked outcome.

    With `corpus` (state/corpus/<repo>), discussion evidence for cached PRs must match
    the cached body, timestamp, author and historical eligibility.
    Callers must check status and obtain independent review before acceptance.
    This function never installs, executes, fetches, or writes artifacts.
    """
    errors = []
    report = _report(Path(candidate_dir), repository, errors)
    if report is not None:
        evidence, claims, skills = _validate_report(report, repository, errors)
        anchors, dates = _validate_evidence(evidence, repository, errors)
        if corpus is not None:
            _corpus_evidence(evidence, anchors, dates, corpus, errors)
        _claim_basis(claims, evidence, errors)
        _coverage(report.get('coverage'), evidence, anchors, dates, errors)
        _skill_artifacts(Path(candidate_dir), repository, skills, claims, evidence, anchors, errors)
    return errors


BLOCKING_SEVERITIES = ('critical', 'high', 'medium', 'blocker', 'blocking', 'error')
SEVERITIES = BLOCKING_SEVERITIES + ('low', 'warning', 'info')
EVALUATION_MODES = ('model-based', 'execution', 'compiled', 'executed', 'mixed')


def _evaluation(value, base, at, errors):
    if not _text(value):
        errors.append(f'{at}: require a substantive evaluation explanation or a relative evidence-file path, not a boolean')
        return ''
    if not any(c.isspace() for c in value):
        path = _local_file(base, value, at, errors)
        value = _decode(path, errors) if path is not None else None
    if not isinstance(value, str) or not _substantive(value):
        errors.append(f'{at}: provide a concrete case, observed/predicted outcome and reasoning; approval-only text is insufficient')
        return ''
    return ' '.join(value.casefold().split())


def _finding_evidence(value, evidence, base, at, errors):
    references = value if isinstance(value, list) else [value]
    if not references:
        errors.append(f'{at}: cite a source ID, original source URL, or substantive local evidence artifact')
    urls = {e['url'] for e in evidence.values()}
    for item in references:
        if not _text(item):
            errors.append(f'{at}: citations must be nonempty strings')
        elif item in evidence or item in urls:
            continue
        elif _substantive(item) and any(re.search(r'(?<![\w.-])' + re.escape(key) + r'(?![\w.-])', item) for key in evidence):
            continue
        else:
            _evaluation(item, base, at, errors)
            # A prose finding must actually identify its source, not merely be long.
            if any(c.isspace() for c in item):
                errors.append(f'{at}: explanatory evidence must cite a report evidence ID')


def _findings(review, skills, evidence, base, errors):
    findings = review.get('findings')
    if not isinstance(findings, list):
        errors.append('review.findings: require an array of finding objects (empty only when justified)')
        return
    if review.get('verdict') in ('revise', 'blocked') and not findings:
        errors.append('review.findings: revise/blocked verdicts must explain at least one actionable blocker or repair')
    for index, finding in enumerate(findings):
        at = f'review.findings[{index}]'
        if not isinstance(finding, dict):
            errors.append(f'{at}: require a finding object')
            continue
        severity = finding.get('severity')
        if severity not in SEVERITIES:
            errors.append(f'{at}.severity: require one of {", ".join(SEVERITIES)}')
        skill_id = finding.get('skill_id')
        if 'skill_id' not in finding or (skill_id is not None and (not isinstance(skill_id, str) or skill_id not in skills)):
            errors.append(f'{at}.skill_id: require a reported skill ID, or null for a report-level finding')
        if not _substantive(finding.get('problem')):
            errors.append(f'{at}.problem: explain a concrete defect, its consequence and needed repair')
        _finding_evidence(finding.get('evidence'), evidence, base, f'{at}.evidence', errors)
        if 'blocking' in finding and type(finding['blocking']) is not bool:
            errors.append(f'{at}.blocking: require a boolean when supplied')
        blocking = severity in BLOCKING_SEVERITIES or finding.get('blocking') is True
        if review.get('verdict') == 'accept' and blocking:
            errors.append(f'{at}: accept cannot contain blocking findings; change verdict to revise or blocked')


def validate_review(review_path: Path, candidate_dir: Path, repository: str) -> list[str]:
    """Validate review structure and binding, NOT its truth or independence.

    Every candidate skill must have four distinct substantive evaluations and
    notes. Accept additionally requires complete candidate status, pass for every
    skill, all used evidence IDs declared verified, and no blocking findings.
    Evaluation paths resolve under review_path.parent; escaping/symlink paths
    are forbidden. A valid revise/blocked review also returns []: inspect verdict.
    """
    review_path, candidate_dir = Path(review_path), Path(candidate_dir)
    errors = validate_candidate(candidate_dir, repository)
    if errors:
        return [f'candidate: {error}' for error in errors]
    review = _json(review_path, errors)
    report = _json(candidate_dir / 'report.json', errors)
    if review is None or report is None:
        return errors
    _version(review, str(review_path), errors)
    _binding(review.get('repository'), repository, str(review_path), errors)
    verdict = review.get('verdict')
    if verdict not in ('accept', 'revise', 'blocked'):
        errors.append('review.verdict: require accept, revise or blocked')
    if verdict == 'accept' and report.get('status') != 'complete':
        errors.append('review.verdict: accept requires a complete candidate, not a blocked outcome')
    raw = _read(candidate_dir / 'report.json', errors)
    digest = review.get('report_sha256')
    if (not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest)
            or raw is None or digest != hashlib.sha256(raw).hexdigest()):
        errors.append('review.report_sha256: must equal SHA-256 of the exact current report.json bytes; re-review changed reports')
    evidence = _records(report.get('evidence'), 'report.evidence', errors)
    claims = _records(report.get('claims'), 'report.claims', errors)
    skills = _records(report.get('skills'), 'report.skills', errors)
    verified = _references(review.get('verified_evidence_ids'), evidence, 'review.verified_evidence_ids', errors)
    _findings(review, skills, evidence, review_path.parent, errors)
    mode = review.get('evaluation_mode')
    if mode not in EVALUATION_MODES:
        errors.append(f'review.evaluation_mode: explicitly require one of {", ".join(EVALUATION_MODES)}; model simulation is not execution')
    if mode in ('execution', 'compiled', 'executed', 'mixed'):
        paths = _strings(review.get('execution_evidence'), 'review.execution_evidence', errors, nonempty=True)
        for value in paths:
            path = _local_file(review_path.parent, value, 'review.execution_evidence', errors)
            if path is not None and not _substantive(_decode(path, errors)):
                errors.append('review.execution_evidence: include substantive command/output logs, not just an execution label')
    evaluations = _records(review.get('evaluated_skills'), 'review.evaluated_skills', errors)
    for identifier in sorted(skills.keys() - evaluations.keys()):
        errors.append(f'review.evaluated_skills: missing evaluation for {identifier}')
    for identifier, evaluation in evaluations.items():
        at = f'review.evaluated_skills[{identifier}]'
        if identifier not in skills:
            errors.append(f'{at}: unknown skill; evaluate exactly the skills in the report')
        texts = []
        for field in ('positive', 'negative', 'repair', 'holdout'):
            text = _evaluation(evaluation.get(field), review_path.parent, f'{at}.{field}', errors)
            if text:
                texts.append(text)
        if len(set(texts)) != len(texts):
            errors.append(f'{at}: positive/negative/repair/holdout must be distinct concrete cases, not repeated text or aliases')
        if not _substantive(evaluation.get('notes')):
            errors.append(f'{at}.notes: explain outcomes and limitations substantively')
        if evaluation.get('result') not in ('pass', 'fail'):
            errors.append(f'{at}.result: require pass or fail')
        if verdict == 'accept' and evaluation.get('result') != 'pass':
            errors.append(f'{at}.result: accept requires pass for every skill')
        if mode == 'mixed' and evaluation.get('evaluation_mode') not in ('model-based', 'execution', 'compiled', 'executed'):
            errors.append(f'{at}.evaluation_mode: mixed reviews must identify each skill as model-based or actual execution')
        if identifier in skills and verdict == 'accept':
            _, used_evidence = _skill_sources(skills[identifier], claims, evidence)
            if not used_evidence.keys() <= verified:
                errors.append(f'{at}: accept requires all used citations in verified_evidence_ids; missing {sorted(used_evidence.keys() - verified)}')
    return errors


def main(argv=None):
    """Print machine-readable structural results; exit 0 valid, 1 invalid, 2 usage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('candidate', 'review'))
    parser.add_argument('path', type=Path)
    parser.add_argument('--repository', required=True, metavar='OWNER/REPO')
    parser.add_argument('--candidate', type=Path, help='candidate directory required for review mode')
    args = parser.parse_args(argv)
    if args.mode == 'review' and args.candidate is None:
        parser.error('review mode requires --candidate PATH')
    if args.mode == 'candidate' and args.candidate is not None:
        parser.error('--candidate is only valid in review mode')
    if args.mode == 'candidate':
        errors = validate_candidate(args.path, args.repository)
    else:
        assert args.candidate is not None  # Guaranteed by the argument check above.
        errors = validate_review(args.path, args.candidate, args.repository)
    print(json.dumps({'scope': 'structural-only', 'structurally_valid': not errors,
                      'source_verified': False, 'mode': args.mode,
                      'repository': args.repository, 'errors': errors}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())

