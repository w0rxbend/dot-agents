"""Resumable, read-only GitHub evidence collection; never execute fetched files.

Successful API pages are immutable local observations, not live truth. Delete a
specific cache entry deliberately to refresh it. Failed requests are not cached
as successes. POSIX advisory locks coordinate threads/processes sharing --state.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import argparse
import base64
import binascii
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import parse_qs, quote, urlencode, urlsplit

WINDOW = {'start': '2018-01-01T00:00:00Z', 'end': '2024-12-31T23:59:59Z'}
WINDOW_START = datetime(2018, 1, 1, tzinfo=timezone.utc)
WINDOW_STOP = datetime(2025, 1, 1, tzinfo=timezone.utc)
DEFAULT_STATE = Path('~/.local/share/dot-agents/scala-history-2018-2024')
REPO_RE = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}\Z')
SHA_RE = re.compile(r'[0-9a-f]{40}\Z')
MAX_ATTEMPTS = 3
MAX_WAIT = 65
REQUEST_TIMEOUT = 60
SEARCH_INTERVAL = 2.2
CORE_INTERVAL = 0.25
MAX_LIST_PAGES = 100
SAFE_HEADERS = {'link', 'etag', 'last-modified', 'date', 'retry-after',
                'x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset',
                'x-ratelimit-resource', 'x-github-request-id'}


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def validate_repo(repo):
    if not isinstance(repo, str) or not REPO_RE.fullmatch(repo) or repo.split('/')[1] in {'.', '..'}:
        raise ValueError('repository must be a literal public GitHub owner/name identifier')
    return repo


def contained(root, relative):
    """Reject traversal and symlinks before either reading or writing state."""
    root = Path(root).resolve()
    relative = str(relative)
    parts = PurePosixPath(relative).parts
    if not parts or relative.startswith('/') or '\\' in relative or any(p in {'.', '..'} for p in relative.split('/')):
        raise ValueError('unsafe relative state path')
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('symlinks are not permitted in collector state paths')
    if not path.resolve().is_relative_to(root):
        raise ValueError('state path escapes root')
    return path


def state_root(state):
    root = Path(state).expanduser().resolve()
    if root.is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError('raw research state must be outside the public repository')
    root.mkdir(parents=True, exist_ok=True)
    return root


def atomic_bytes(root, relative, content):
    path = contained(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def atomic_json(root, relative, data):
    return atomic_bytes(root, relative, (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode())


@contextmanager
def file_lock(root, relative):
    # Lockfiles have stable inodes and are never replaced; payloads are atomic.
    path = contained(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def endpoint_url(path, **parameters):
    return path + ('?' + urlencode(parameters) if parameters else '')


def body_hash(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


class APIError(RuntimeError):
    def __init__(self, endpoint, kind, *, status=None, attempts=0, retryable=False, retry_after=None):
        self.record = {'endpoint': endpoint, 'kind': kind, 'status': status,
                       'attempts': attempts, 'retryable': retryable, 'retry_after': retry_after}
        super().__init__(f'{kind}: {endpoint}' + (f' (HTTP {status})' if status else ''))


def parse_response(output):
    """gh --include uses LF status lines and sometimes CRLF header lines."""
    text = output.replace('\r\n', '\n')
    status, headers = None, {}
    while text.startswith('HTTP/'):
        header, separator, text = text.partition('\n\n')
        if not separator:
            raise ValueError('invalid HTTP envelope')
        status = int(header.splitlines()[0].split()[1])
        headers = {}
        for line in header.splitlines()[1:]:
            key, colon, value = line.partition(':')
            if colon and key.lower() in SAFE_HEADERS:
                headers[key.lower()] = value.strip()
    if status is None:
        raise ValueError('missing HTTP status')
    return status, headers, json.loads(text)


class GitHubAPI:
    def __init__(self, state):
        self.state = state_root(state)
        self.events = []
        self.cache_hits = 0
        self.network_requests = 0

    def cache_relative(self, endpoint):
        return 'cache/api/' + hashlib.sha256(endpoint.encode()).hexdigest() + '.json'

    def _pace(self, resource):
        interval = SEARCH_INTERVAL if resource == 'search' else CORE_INTERVAL
        with file_lock(self.state, f'coord/{resource}.lock'):
            path = contained(self.state, f'coord/{resource}.json')
            saved = json.loads(path.read_text()) if path.exists() else {}
            wait = max(0, saved.get('not_before', 0) - time.time())
            if wait > MAX_WAIT:
                raise APIError(resource, 'shared_rate_limit', retryable=True, retry_after=wait)
            if wait:
                time.sleep(wait)
            atomic_json(self.state, f'coord/{resource}.json', {'not_before': time.time() + interval})

    def _defer(self, resource, delay):
        with file_lock(self.state, f'coord/{resource}.lock'):
            path = contained(self.state, f'coord/{resource}.json')
            saved = json.loads(path.read_text()) if path.exists() else {}
            atomic_json(self.state, f'coord/{resource}.json',
                        {'not_before': max(saved.get('not_before', 0), time.time() + delay)})

    def get(self, endpoint):
        if not isinstance(endpoint, str) or not endpoint.startswith(('repos/', 'users/', 'orgs/', 'search/')) or any(c in endpoint for c in '\r\n#'):
            raise ValueError('unsupported public read-only GitHub endpoint')
        relative = self.cache_relative(endpoint)
        with file_lock(self.state, relative.replace('cache/api/', 'locks/api/') + '.lock'):
            path = contained(self.state, relative)
            if path.exists():
                try:
                    saved = json.loads(path.read_text(encoding='utf-8'))
                    if saved['endpoint'] != endpoint or saved['body_sha256'] != body_hash(saved['body']) or saved['status'] != 200:
                        raise ValueError('invalid cached envelope')
                    self.cache_hits += 1
                    return saved
                except (ValueError, KeyError, TypeError):
                    self.events.append({'kind': 'cache_corrupt', 'endpoint': endpoint, 'recovered_by': 'refetch'})
            resource = 'search' if endpoint.startswith('search/') else 'core'
            failures = []
            for attempt in range(1, MAX_ATTEMPTS + 1):
                status, headers, body = None, {}, None
                try:
                    self._pace(resource)
                    self.network_requests += 1
                    result = subprocess.run(
                        ['gh', 'api', '--hostname', 'github.com', '--method', 'GET',
                         '-H', 'Accept: application/vnd.github+json',
                         '-H', 'X-GitHub-Api-Version: 2022-11-28', '--include', endpoint],
                        capture_output=True, text=True, timeout=REQUEST_TIMEOUT, check=False)
                    try:
                        status, headers, body = parse_response(result.stdout)
                    except (ValueError, TypeError):
                        raise APIError(endpoint, 'invalid_response', attempts=attempt, retryable=True) from None
                    if isinstance(body, dict) and body.get('private') is True:
                        body = None
                        raise APIError(endpoint, 'private_repository_refused', attempts=attempt)
                    if result.returncode == 0 and status == 200:
                        saved = {'schema_version': 1, 'endpoint': endpoint, 'fetched_at': utc_now(),
                                 'status': status, 'headers': headers, 'body': body,
                                 'body_sha256': body_hash(body), 'prior_attempt_errors': failures}
                        atomic_json(self.state, relative, saved)
                        return saved
                    retryable = status in {403, 408, 429, 500, 502, 503, 504}
                    delay = 2 ** attempt
                    if status in {403, 429}:
                        delay = 60
                        try:
                            if 'retry-after' in headers:
                                delay = max(delay, float(headers['retry-after']))
                            elif headers.get('x-ratelimit-remaining') == '0':
                                delay = max(delay, float(headers['x-ratelimit-reset']) - time.time() + 1)
                        except (ValueError, KeyError):
                            pass
                        self._defer(resource, delay)
                    raise APIError(endpoint, 'rate_limit' if status in {403, 429} else 'http_error',
                                   status=status, attempts=attempt, retryable=retryable, retry_after=delay)
                except (subprocess.TimeoutExpired, OSError) as exc:
                    error = APIError(endpoint, 'timeout' if isinstance(exc, subprocess.TimeoutExpired) else 'process_error',
                                     attempts=attempt, retryable=True, retry_after=2 ** attempt)
                except APIError as exc:
                    error = exc
                record = dict(error.record, observed_at=utc_now(), headers=headers, response=body)
                failures.append(record)
                self.events.append(record)
                atomic_json(self.state, relative.replace('cache/api/', 'failures/api/'),
                            {'endpoint': endpoint, 'attempt_errors': failures})
                delay = error.record['retry_after'] or 2 ** attempt
                if not error.record['retryable'] or attempt == MAX_ATTEMPTS or delay > MAX_WAIT:
                    raise error
                if status not in {403, 429}:
                    time.sleep(delay)
            raise AssertionError('unreachable retry state')


def gap(kind, *, scope=None, severity='incomplete', **details):
    return dict(kind=kind, severity=severity, scope=scope, **details)


def page_reference(api, endpoint, envelope):
    return {'endpoint': endpoint, 'cache_path': api.cache_relative(endpoint),
            'fetched_at': envelope.get('fetched_at'), 'body_sha256': envelope.get('body_sha256')}


def paginated(api, endpoint, *, parameters=None, max_pages=MAX_LIST_PAGES, api_cap=None, expected=None):
    """Retain every response page; never conflate an error with an empty list."""
    items, pages, gaps = [], [], []
    complete = False
    for number in range(1, max_pages + 1):
        url = endpoint_url(endpoint, **dict(parameters or {}, per_page=100, page=number))
        try:
            response = api.get(url)
            batch = response['body']
            if not isinstance(batch, list):
                raise APIError(url, 'invalid_list_response')
        except APIError as exc:
            gaps.append(gap('endpoint_failed', scope=endpoint, error=exc.record))
            break
        pages.append(page_reference(api, url, response))
        items.extend(batch)
        has_next = 'rel="next"' in response['headers'].get('link', '')
        if api_cap is not None and len(items) >= api_cap:
            # At an endpoint ceiling, lack of a Link is not proof of completeness.
            complete = expected is not None and len(items) == expected
            if not complete:
                gaps.append(gap('api_cap', scope=endpoint, limit=api_cap, retrieved=len(items), expected=expected))
            break
        if not has_next and len(batch) < 100:
            complete = True
            break
    else:
        gaps.append(gap('pagination_cap', scope=endpoint, max_pages=max_pages, retrieved=len(items)))
    if expected is not None and len(items) != expected:
        complete = False
        gaps.append(gap('count_mismatch', scope=endpoint, expected=expected, retrieved=len(items)))
    return {'items': items, 'coverage': {'complete': complete, 'pages': pages, 'retrieved': len(items),
                                       'max_pages': max_pages, 'api_cap': api_cap, 'expected': expected}, 'gaps': gaps}


CORE_REPOSITORIES = {
    'zio/zio': 'zio', 'zio/zio-kafka': 'zio', 'zio/zio-http': 'zio',
    'typelevel/cats': 'typelevel', 'typelevel/cats-effect': 'typelevel',
    'http4s/http4s': 'http4s', 'typelevel/fs2': 'typelevel',
    'playframework/playframework': 'play',
}
# Historical owner URLs are resolved by GitHub's redirect, not assumed canonical.
# scala-js-dom is an attributable transfer outside both enumerated namespaces.
ALIASES = tuple('lihaoyi/' + name for name in (
    'acyclic', 'Ammonite', 'cask', 'castor', 'fansi', 'fastparse', 'geny',
    'mainargs', 'mill', 'os-lib', 'PPrint', 'requests-scala', 'scalatags',
    'sourcecode', 'upickle', 'utest', 'scala-js-dom'))


class DiscoveryError(RuntimeError):
    pass


def parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except ValueError:
        return None


def in_window(value):
    value = parse_date(value)
    return value is not None and WINDOW_START <= value < WINDOW_STOP


def repository_entry(metadata, family, origin):
    repo = validate_repo(metadata['full_name'])
    if metadata.get('private') is not False:
        raise ValueError('public repository status was not verified')
    language = metadata.get('language')
    description = metadata.get('description') or ''
    created = parse_date(metadata.get('created_at'))
    classification, included, reason = 'library_or_tool', True, 'Scala library/tool candidate from enumerated owner; requires historical review'
    if family != 'lihaoyi':
        reason = 'Required core repository'
    elif created is not None and created >= WINDOW_STOP:
        classification, included, reason = 'post_window', False, 'Repository created after historical cutoff'
    elif metadata.get('fork'):
        classification, included, reason = 'fork', False, 'Personal fork; not evidence of original library authorship'
    elif language == 'Scala':
        pass
    elif language is None or re.search(r'scala|mill|ammonite', description, re.I):
        classification, reason = 'unknown', 'Uncertain Scala/library scope; retained for research rather than silently excluded'
    else:
        classification, included, reason = 'non_scala', False, f'Primary language {language}; no Scala/tooling signal in description'
    return {'repo': repo, 'family': family, 'included': included, 'reason': reason,
            'classification': classification, 'aliases': [], 'origins': [origin],
            'archived': metadata.get('archived'), 'fork': metadata.get('fork'),
            'language': language, 'description': description, 'created_at': metadata.get('created_at'),
            'html_url': metadata.get('html_url', 'https://github.com/' + repo),
            'metadata_is_current_observation': True}


def discover(state: Path) -> dict:
    """Publish inventory only if every required enumeration/alias fetch succeeds."""
    state = state_root(state)
    with file_lock(state, 'locks/discover.lock'):
        api, entries, coverage, gaps = GitHubAPI(state), {}, {}, []

        def include(metadata, family, origin, alias=None):
            entry = repository_entry(metadata, family, origin)
            key = entry['repo'].casefold()
            if key in entries:
                entry = entries[key]
                if origin not in entry['origins']:
                    entry['origins'].append(origin)
            else:
                entries[key] = entry
            if alias and alias.casefold() != key and alias not in entry['aliases']:
                entry['aliases'].append(alias)

        try:
            for endpoint, parameters in [('users/lihaoyi/repos', {'type': 'owner', 'sort': 'full_name'}),
                                          ('orgs/com-lihaoyi/repos', {'type': 'public', 'sort': 'full_name'})]:
                result = paginated(api, endpoint, parameters=parameters)
                coverage[endpoint] = result['coverage']
                gaps.extend(result['gaps'])
                if not result['coverage']['complete']:
                    raise DiscoveryError('owner enumeration incomplete: ' + endpoint)
                for metadata in result['items']:
                    include(metadata, 'lihaoyi', endpoint)
            resolutions = []
            for repo, family in list(CORE_REPOSITORIES.items()) + [(alias, 'lihaoyi') for alias in ALIASES]:
                endpoint = 'repos/' + validate_repo(repo)
                response = api.get(endpoint)
                include(response['body'], family, endpoint, alias=repo)
                resolutions.append(dict(page_reference(api, endpoint, response), requested=repo,
                                        canonical=response['body']['full_name']))
            coverage['resolutions'] = resolutions
        except (APIError, ValueError, KeyError, TypeError, DiscoveryError) as exc:
            if isinstance(exc, APIError):
                gaps.append(gap('endpoint_failed', error=exc.record))
            atomic_json(state, 'inventory.failure.json', {
                'schema_version': 1, 'observed_at': utc_now(), 'status': 'failed',
                'coverage': coverage, 'gaps': gaps, 'error': str(exc),
                'previous_inventory_preserved': contained(state, 'inventory.json').exists()})
            raise DiscoveryError('discovery failed; previous inventory preserved: ' + str(exc)) from exc
        repositories = sorted(entries.values(), key=lambda item: item['repo'].casefold())
        inventory = {
            'schema_version': 1, 'window': dict(WINDOW), 'generated_at': utc_now(),
            'repositories': repositories, 'gaps': gaps,
            'coverage': dict(coverage, enumeration_complete=True, repositories=len(repositories),
                             included=sum(x['included'] for x in repositories),
                             transfer_discovery='Known former-owner URLs resolved via GitHub; arbitrary unknown transfers/deletions are not exhaustively discoverable',
                             unknowns_retained=True, archived_not_excluded=True),
            'api_events': api.events,
        }
        atomic_json(state, 'inventory.json', inventory)
        return inventory


SEARCH_PAGE_LIMIT = 2
# A per-repository supplement, independent of the historical per-year sample.
ACTIVITY_PULL_LIMIT = 6


def search_pulls(api, repo, year, outcome, limit):
    """Bounded candidate scan, not an exhaustive PR search; counts stay explicit."""
    validate_repo(repo)
    if year not in range(2018, 2025) or outcome not in {'merged', 'closed_unmerged'}:
        raise ValueError('invalid historical search stratum')
    dates = f'{year}-01-01..{year}-12-31'
    qualifier = f'is:merged merged:{dates}' if outcome == 'merged' else f'is:closed is:unmerged closed:{dates}'
    query = f'repo:{repo} is:pr {qualifier}'
    # Mix discussion-rich examples and early chronology, not only popular merges.
    sort, order = ('comments', 'desc') if year % 2 == 0 else ('created', 'asc')
    def eligible(item):
        occurred_at = (item.get('pull_request') or {}).get('merged_at') if outcome == 'merged' else item.get('closed_at')
        occurred = parse_date(occurred_at)
        return occurred is not None and in_window(occurred_at) and occurred.year == year
    return search_pull_candidates(api, query, limit, sort, order, eligible,
                                  scope=f'search/{year}/{outcome}', year=year, outcome=outcome)


def activity_stratum(detail):
    created = parse_date(detail.get('created_at'))
    if created is None or created >= WINDOW_STOP:
        return None
    merged = detail.get('merged_at') or (detail.get('pull_request') or {}).get('merged_at')
    if detail.get('state') == 'open' and not detail.get('closed_at') and not merged:
        return 'open'
    closed, merged_date = parse_date(detail.get('closed_at')), parse_date(merged)
    if (detail.get('state') == 'closed' and closed is not None and closed >= WINDOW_STOP
            and (not merged or (merged_date is not None and merged_date >= WINDOW_STOP))):
        return 'closed_after_window'
    return None


def search_activity_pulls(api, repo, stratum, limit=ACTIVITY_PULL_LIMIT):
    """Find candidates only; creation/update/closure dates do not prove activity."""
    validate_repo(repo)
    if stratum not in {'open', 'closed_after_window'}:
        raise ValueError('invalid activity search stratum')
    if type(limit) is not int or not 1 <= limit <= ACTIVITY_PULL_LIMIT:
        raise ValueError('activity candidate limit outside hard budget')
    qualifier = 'is:open' if stratum == 'open' else 'is:closed closed:>=2025-01-01'
    query = f'repo:{repo} is:pr created:<2025-01-01 {qualifier}'
    return search_pull_candidates(api, query, limit, 'comments', 'desc',
                                  lambda item: activity_stratum(item) == stratum,
                                  scope=f'search/activity/{stratum}', stratum=stratum)


def search_pull_candidates(api, query, limit, sort, order, eligible, *, scope, **stratum):
    candidates, pages, gaps, excluded, seen = [], [], [], [], set()
    totals, scanned, incomplete, endpoint_failed = [], 0, False, False
    for page in range(1, SEARCH_PAGE_LIMIT + 1):
        endpoint = endpoint_url('search/issues', q=query, sort=sort, order=order, per_page=100, page=page)
        try:
            response = api.get(endpoint)
            body = response['body']
            if (not isinstance(body, dict) or not isinstance(body.get('items'), list)
                    or type(body.get('total_count')) is not int or type(body.get('incomplete_results')) is not bool):
                raise APIError(endpoint, 'invalid_search_response')
        except APIError as exc:
            gaps.append(gap('endpoint_failed', scope=scope, error=exc.record))
            endpoint_failed = True
            break
        pages.append(page_reference(api, endpoint, response))
        totals.append(body['total_count'])
        incomplete |= body['incomplete_results']
        scanned += len(body['items'])
        for item in body['items']:
            number = item.get('number')
            if type(number) is not int or number <= 0 or not eligible(item):
                excluded.append(number)
                continue
            if number not in seen:
                candidates.append(item)
                seen.add(number)
        if len(candidates) >= limit or len(body['items']) < 100 or scanned >= min(body['total_count'], 1000):
            break
    total = max(totals) if totals else None
    coverage = {**stratum, 'query': query, 'sort': sort, 'order': order,
                'total_count': total, 'page_total_counts': totals, 'incomplete_results': incomplete,
                'endpoint_failed': endpoint_failed, 'pages': pages, 'page_limit': SEARCH_PAGE_LIMIT,
                'search_api_cap': 1000, 'search_cap_limited': total is not None and total > 1000,
                'scanned': scanned, 'eligible_candidates': len(candidates), 'excluded_dates': excluded,
                'scan_limited': total is not None and scanned < total,
                'selection_limit': limit, 'sampled': True, 'returned_candidates': min(limit, len(candidates)),
                'selection_limited': len(candidates) > limit,
                'query_pages_complete': not endpoint_failed and not incomplete}
    if incomplete:
        gaps.append(gap('search_incomplete', scope=query, reported_total=total))
    if total is not None and total > 1000:
        gaps.append(gap('search_api_cap', scope=query, limit=1000, reported_total=total))
    if len(set(totals)) > 1:
        gaps.append(gap('search_count_changed', scope=query, counts=totals))
    if excluded:
        gaps.append(gap('date_guard_rejected', scope=query, numbers=excluded))
    return {'items': candidates[:limit], 'coverage': coverage, 'gaps': gaps}


def historical_records(groups):
    eligible, excluded = {}, []
    for name, rows in groups.items():
        eligible[name] = []
        for row in rows:
            identifier = row.get('id', row.get('sha'))
            occurred_at = row.get('submitted_at') if name == 'reviews' else row.get('created_at')
            if name == 'commits':
                occurred_at = (row.get('commit') or {}).get('committer', {}).get('date')
            reason = None
            if not in_window(occurred_at):
                reason = 'missing_or_outside_window_timestamp'
            elif row.get('updated_at') and not in_window(row['updated_at']):
                reason = 'body_edited_outside_window'
            if reason:
                excluded.append({'group': name, 'id': identifier, 'occurred_at': occurred_at,
                                 'updated_at': row.get('updated_at'), 'reason': reason})
            else:
                eligible[name].append(identifier)
    return {'eligible_ids': eligible, 'excluded': excluded,
            'policy': 'Retain full raw discussion, but only window-eligible records support historical claims. Bodies edited after cutoff are excluded; undated edits cannot be reconstructed.',
            'maintainer_role': 'unknown; author_association is a present-day API observation, not verified historical role'}


def collect_pull(api, repo, number, *, activity=False) -> dict:
    """Cache raw observations; the activity mode never certifies a historical diff."""
    validate_repo(repo)
    if type(number) is not int or number <= 0:
        raise ValueError('PR number must be a positive integer')
    endpoint = f'repos/{repo}/pulls/{number}'
    response = api.get(endpoint)
    detail = response['body']
    if not isinstance(detail, dict) or detail.get('number') != number:
        raise APIError(endpoint, 'invalid_pull_response')
    occurred_at = detail.get('merged_at') or detail.get('closed_at')
    if activity and activity_stratum(detail) is None:
        raise APIError(endpoint, 'pull_outside_activity_strata')
    if not activity and not in_window(occurred_at):
        raise APIError(endpoint, 'pull_outside_window')
    groups, coverage, gaps = {}, {}, []
    endpoints = [('reviews', endpoint + '/reviews', None, None),
                 ('review_comments', endpoint + '/comments', None, detail.get('review_comments')),
                 ('issue_comments', f'repos/{repo}/issues/{number}/comments', None, detail.get('comments')),
                 ('files', endpoint + '/files', 3000, detail.get('changed_files')),
                 ('commits', endpoint + '/commits', 250, detail.get('commits'))]
    for name, url, cap, expected in endpoints:
        result = paginated(api, url, api_cap=cap, expected=expected)
        groups[name] = result['items']
        coverage[name] = result['coverage']
        gaps.extend(result['gaps'])
    historical = historical_records({key: value for key, value in groups.items() if key != 'files'})
    historical['activity_counts'] = {}
    for name, eligible_ids in historical['eligible_ids'].items():
        qualifying = set()
        for row in groups[name]:
            identifier = row.get('sha') if name == 'commits' else row.get('id')
            if name == 'commits':
                substantive = isinstance(identifier, str) and bool(SHA_RE.fullmatch(identifier))
            else:
                substantive = (type(identifier) is int and identifier > 0
                               and isinstance(row.get('body'), str) and bool(row['body'].strip()))
            if substantive and identifier in eligible_ids:
                qualifying.add(identifier)
        historical['activity_counts'][name] = len(qualifying)
    historical['activity_eligible'] = any(historical['activity_counts'].values())
    historical['activity_evaluation_complete'] = all(coverage[name]['complete'] for name in historical['activity_counts'])
    historical['adopted_in_window'] = in_window(detail.get('merged_at'))
    head_sha = (detail.get('head') or {}).get('sha')
    historical['diff_eligible'] = (
        not activity and coverage['commits']['complete'] and coverage['files']['complete']
        and isinstance(head_sha, str) and bool(SHA_RE.fullmatch(head_sha))
        and head_sha in historical['eligible_ids']['commits']
        and all((date := parse_date((row.get('commit') or {}).get('committer', {}).get('date'))) is not None
                and date < WINDOW_STOP for row in groups['commits']))
    historical['contextual_only'] = not historical['diff_eligible']
    if activity:
        historical['activity_limitation'] = (
            'Contextual-only in-window discussion and commit metadata, not observed/adopted implementation. '
            'Current head/base, files and any later merge are not historical code evidence. '
            'Inspect source at an independently date-verified historical SHA before making implementation claims. '
            'Current outcome is not a reconstructed cutoff state; closed-unmerged does not establish why a proposal was rejected.')
    historical['pull_body_eligible'] = in_window(detail.get('created_at')) and in_window(detail.get('updated_at'))
    historical['diff_caveat'] = (
        'Files are the API-observed PR diff, not a reconstruction of every review revision; '
        'patches may be absent for binary or oversized files. diff_eligible requires a window-closed PR, '
        'a verified in-window head commit, no later/undated commits and complete commits/files responses. '
        'Eligibility permits inspection, not a claim that every hunk originated in-window. '
        'adopted_in_window describes only the merge event, not implementation provenance or reviewer endorsement.')
    if historical['excluded']:
        gaps.append(gap('nonhistorical_records_retained', scope=endpoint, severity='limitation', count=len(historical['excluded'])))
    return dict(schema_version=1, repository=repo, window=dict(WINDOW), number=number,
                detail=detail, detail_response=page_reference(api, endpoint, response),
                outcome='merged' if detail.get('merged_at') else 'open' if detail.get('state') == 'open' else 'closed_unmerged',
                occurred_at=occurred_at, historical=historical, coverage=coverage, gaps=gaps, **groups)


MAX_FILE_BYTES = 256_000
FILES_PER_CATEGORY = 3


def source_category(path):
    lower, name = path.lower(), PurePosixPath(path).name.lower()
    if name in {'build.sbt', 'build.sc', 'build.mill', 'package.mill', 'build.properties', 'plugins.sbt', 'pom.xml'} or lower.startswith('project/'):
        return 'build'
    if lower.endswith(('.scala', '.java')):
        return 'test' if re.search(r'(^|/)(test[^/]*|spec[^/]*)(/|$)|(?:test|spec|suite)\.(scala|java)$', lower) else 'source'
    return None


def choose_snapshot_commit(api, repo, year):
    target = f'{year}-12-31T23:59:59Z'
    endpoint = f'repos/{repo}/commits'
    params = {'since': WINDOW['start'], 'until': target, 'per_page': 1, 'page': 1}
    pages = []

    def fetch(parameters):
        url = endpoint_url(endpoint, **parameters)
        response = api.get(url)
        pages.append(page_reference(api, url, response))
        if not isinstance(response['body'], list):
            raise APIError(url, 'invalid_commits_response')
        return response

    response = fetch(params)
    method = 'latest default-branch commit at or before target, within window'
    if not response['body'] and year != 2024:
        params['until'] = WINDOW['end']
        response = fetch(params)
        method = 'no earlier historical commit; oldest available default-branch commit in window via final API page'
        # Never follow a server-controlled URL. Extract only its bounded page number.
        links = re.findall(r'<([^>]+)>;\s*rel="last"', response['headers'].get('link', ''))
        if links:
            link = urlsplit(links[0])
            last = int(parse_qs(link.query).get('page', ['0'])[0])
            if link.hostname != 'api.github.com' or link.path != '/' + endpoint or not 1 <= last <= 10_000_000:
                raise APIError(endpoint, 'invalid_pagination_link')
            params['page'] = last
            response = fetch(params)
    if not response['body']:
        return None, {'target': target, 'method': method, 'pages': pages}
    commit = response['body'][0]
    date = commit.get('commit', {}).get('committer', {}).get('date')
    if not SHA_RE.fullmatch(commit.get('sha', '')) or not in_window(date):
        raise APIError(endpoint, 'snapshot_commit_outside_window_or_invalid')
    occurred, target_date = parse_date(date), parse_date(target)
    if occurred is None or target_date is None or (method.startswith('latest') and occurred > target_date):
        raise APIError(endpoint, 'snapshot_commit_after_target')
    return commit, {'target': target, 'method': method, 'pages': pages,
                    'limitation': 'Current default-branch ancestry only; deleted branches and nonmonotonic commit dates may hide other historical states'}


def collect_snapshot(api, repo, year):
    validate_repo(repo)
    if year not in {2020, 2022, 2024}:
        raise ValueError('unsupported snapshot year')
    snapshot = {'schema_version': 1, 'repository': repo, 'year': year, 'window': dict(WINDOW),
                'files': [], 'gaps': [], 'coverage': {'sampled': True, 'files_per_category': FILES_PER_CATEGORY,
                                                     'max_file_bytes': MAX_FILE_BYTES}}
    gaps = snapshot['gaps']
    try:
        commit, selection = choose_snapshot_commit(api, repo, year)
        snapshot['selection'] = selection
        if commit is None:
            gaps.append(gap('no_historical_commit', scope=str(year), severity='unavailable'))
            snapshot['status'] = 'unavailable'
            return snapshot
        sha = commit['sha']
        snapshot.update(commit_sha=sha, commit_date=commit['commit']['committer']['date'], commit=commit)
        tree_sha = commit.get('commit', {}).get('tree', {}).get('sha', '')
        if not SHA_RE.fullmatch(tree_sha):
            raise APIError(f'repos/{repo}/commits/{sha}', 'missing_tree_sha')
        endpoint = endpoint_url(f'repos/{repo}/git/trees/{tree_sha}', recursive=1)
        response = api.get(endpoint)
        tree = response['body']
        if not isinstance(tree, dict) or not isinstance(tree.get('tree'), list) or type(tree.get('truncated')) is not bool:
            raise APIError(endpoint, 'invalid_tree_response')
        snapshot['tree_response'] = page_reference(api, endpoint, response)
        snapshot['tree_sha'] = tree_sha
        snapshot['tree_paths'] = [entry.get('path') for entry in tree['tree']]
        snapshot['coverage']['tree_complete'] = not tree['truncated']
        if tree['truncated']:
            gaps.append(gap('tree_truncated', scope=endpoint, retrieved_paths=len(tree['tree'])))
        categories = {'build': [], 'source': [], 'test': []}
        for entry in tree['tree']:
            path = entry.get('path', '')
            try:
                contained(api.state, path)
            except (ValueError, TypeError):
                gaps.append(gap('unsafe_source_path', scope=str(year), path=path))
                continue
            category = source_category(path)
            if category is None or entry.get('type') != 'blob':
                continue
            if entry.get('mode') not in {'100644', '100755'}:
                gaps.append(gap('nonregular_source_skipped', scope=path, severity='limitation'))
                continue
            if type(entry.get('size')) is not int or not 0 <= entry['size'] <= MAX_FILE_BYTES:
                gaps.append(gap('source_size_limit', scope=path, severity='limitation', bytes=entry.get('size'), limit=MAX_FILE_BYTES))
                continue
            categories[category].append(entry)
        for category, candidates in categories.items():
            # Favor real shallow library files over example/generated trees.
            candidates.sort(key=lambda e: (bool(re.search(r'(^|/)(examples?|generated|benchmarks?)(/|$)', e['path'], re.I)),
                                           e['path'].count('/'), len(e['path']), e['path']))
            snapshot['coverage'][category] = {'candidates': len(candidates), 'selected': 0}
            for entry in candidates[:FILES_PER_CATEGORY]:
                path, blob_sha = entry['path'], entry.get('sha', '')
                try:
                    if not SHA_RE.fullmatch(blob_sha):
                        raise APIError(path, 'invalid_blob_sha')
                    endpoint = f'repos/{repo}/git/blobs/{blob_sha}'
                    response = api.get(endpoint)
                    blob = response['body']
                    if blob.get('encoding') != 'base64' or blob.get('sha') != blob_sha:
                        raise APIError(endpoint, 'invalid_blob_response')
                    try:
                        content = base64.b64decode(''.join(blob['content'].split()), validate=True)
                        git_hash = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
                        if len(content) > MAX_FILE_BYTES or git_hash != blob_sha:
                            raise ValueError('blob integrity or size mismatch')
                        text = content.decode('utf-8')
                    except (ValueError, KeyError, binascii.Error, UnicodeDecodeError):
                        raise APIError(endpoint, 'invalid_blob_content') from None
                    snapshot['files'].append({'path': path, 'category': category, 'blob_sha': blob_sha,
                                              'commit_sha': sha, 'occurred_at': snapshot['commit_date'],
                                              'url': f'https://github.com/{repo}/blob/{sha}/{quote(path)}',
                                              'content': text, 'bytes': len(content),
                                              'sha256': hashlib.sha256(content).hexdigest(),
                                              'response': page_reference(api, endpoint, response)})
                    snapshot['coverage'][category]['selected'] += 1
                except APIError as exc:
                    gaps.append(gap('endpoint_failed', scope=path, error=exc.record))
            if not snapshot['coverage'][category]['selected']:
                gaps.append(gap('representative_category_unavailable', scope=str(year), category=category, severity='unavailable'))
        snapshot['status'] = 'partial' if any(g['severity'] == 'incomplete' for g in gaps) else 'sampled'
    except APIError as exc:
        gaps.append(gap('endpoint_failed', scope=f'snapshot/{year}', error=exc.record))
        snapshot['status'] = 'partial'
    return snapshot


def publish_artifact(state, directory, category, identifier, data):
    # Content addressing means a crash cannot mutate files referenced by old index.
    relative = f'{category}/{identifier}-{body_hash(data)[:20]}.json'
    atomic_json(state, f'{directory}/{relative}', data)
    return relative


def collect_repository(state: Path, repo: str, *, per_year: int = 6) -> dict:
    """Persist a bounded historical sample; failed endpoints remain explicit gaps.

    Schema v1 remains additive: ``pulls`` keeps merge/closure-year semantics;
    ``activity_pulls`` contains disjoint, contextual-only open/later-closed PRs
    with verified window activity, not a synthetic ``year`` or adoption claim.
    Each entry resolves to the same full raw artifact shape. Inspect its
    ``historical.eligible_ids``, ``activity_counts``, ``diff_eligible`` and
    ``adopted_in_window`` independently before making evidence claims.
    ``coverage.activity_discovery.searches`` also references excluded probes,
    reports unknown totals as null on search failure, and exposes scan/selection
    limits. A successful subset never implies exhaustive discovery/discussion.
    """
    validate_repo(repo)
    if type(per_year) is not int or not 1 <= per_year <= 100:
        raise ValueError('per_year must be an integer from 1 through 100')
    state = state_root(state)
    directory = 'corpus/' + repo.replace('/', '--')
    with file_lock(state, 'locks/repos/' + repo.casefold().replace('/', '--') + '.lock'):
        api = GitHubAPI(state)
        index = {'schema_version': 1, 'repository': repo, 'window': dict(WINDOW),
                 'pulls': [], 'activity_pulls': [], 'snapshots': [], 'gaps': [], 'coverage': {'years': [], 'per_year': per_year,
                 'sampled': True, 'exhaustive': False,
                 'policy': 'By merged/closed year; alternate comment-rich and chronological searches, stratified merged and closed-unmerged. With one per year alternate outcome preference. Separate bounded activity discovery supplements the year sample; undiscovered/deleted records remain outside this sample.'}}
        try:
            existing = contained(state, directory + '/index.json')
            if existing.exists():
                old = json.loads(existing.read_text())
                if old.get('repository', '').casefold() != repo.casefold():
                    raise ValueError('repository directory key collision')
            metadata = api.get('repos/' + repo)
            if metadata['body'].get('private') is not False:
                raise ValueError('collection is restricted to verified public repositories')
            canonical = validate_repo(metadata['body']['full_name'])
            index['canonical_repository'] = canonical
            index['metadata'] = metadata['body']
            index['metadata_response'] = page_reference(api, 'repos/' + repo, metadata)
            seen = set()
            for year in range(2018, 2025):
                results = {outcome: search_pulls(api, canonical, year, outcome, per_year)
                           for outcome in ('merged', 'closed_unmerged')}
                for result in results.values():
                    index['gaps'].extend(result['gaps'])
                first = 'merged' if year % 2 == 0 else 'closed_unmerged'
                other = 'closed_unmerged' if first == 'merged' else 'merged'
                chosen, queues = [], {key: list(value['items']) for key, value in results.items()}
                while len(chosen) < per_year and any(queues.values()):
                    for outcome in (first, other):
                        if queues[outcome] and len(chosen) < per_year:
                            item = queues[outcome].pop(0)
                            if item['number'] not in seen:
                                chosen.append((outcome, item['number']))
                                seen.add(item['number'])
                for outcome, result in results.items():
                    result['coverage']['selected_numbers'] = [number for selected_outcome, number in chosen if selected_outcome == outcome]
                year_coverage = {'year': year, 'searches': {key: value['coverage'] for key, value in results.items()},
                                 'selected': [number for _, number in chosen], 'retrieved': []}
                for outcome, number in chosen:
                    try:
                        pull = collect_pull(api, canonical, number)
                        occurred = parse_date(pull['occurred_at'])
                        if occurred is None or occurred.year != year or pull['outcome'] != outcome:
                            raise APIError(f'repos/{canonical}/pulls/{number}', 'search_detail_mismatch')
                        path = publish_artifact(state, directory, 'pulls', number, pull)
                        index['pulls'].append({'number': number, 'path': path, 'year': year,
                                               'outcome': pull['outcome'], 'body_sha256': body_hash(pull)})
                        index['gaps'].extend(dict(g, pull_number=number) for g in pull['gaps'])
                        year_coverage['retrieved'].append(number)
                    except APIError as exc:
                        index['gaps'].append(gap('pull_failed', scope=str(number), error=exc.record))
                if not chosen:
                    index['gaps'].append(gap('year_without_selected_pulls', scope=str(year), severity='unavailable',
                                             reason='No eligible returned candidates; consult search counts/errors'))
                if len(chosen) < per_year:
                    index['gaps'].append(gap('sample_underfilled', scope=str(year), severity='sampling',
                                             requested=per_year, selected=len(chosen)))
                index['coverage']['years'].append(year_coverage)
            activity_coverage = {'searches': {}, 'candidate_limit_per_stratum': ACTIVITY_PULL_LIMIT,
                                 'inspection_limit': 2 * ACTIVITY_PULL_LIMIT,
                                 'search_page_limit': 2 * SEARCH_PAGE_LIMIT,
                                 'sampled': True, 'exhaustive': False,
                                 'policy': 'Pre-cutoff-created open or later-closed PRs, comment-rich first. Candidate budget is independent of per_year; duplicates, failed endpoints and ineligible activity are not backfilled. Require retrieved in-window discussion bodies or commits, not creation/update/closure timestamps. Current state/diff/merge is contextual only; this is not exhaustive historical activity discovery.'}
            index['coverage']['activity_discovery'] = activity_coverage
            activity_network_before, activity_cache_before = api.network_requests, api.cache_hits
            activity_seen = {entry['number'] for entry in index['pulls']}
            for stratum in ('open', 'closed_after_window'):
                result = search_activity_pulls(api, canonical, stratum)
                index['gaps'].extend(result['gaps'])
                search = result['coverage']
                activity_coverage['searches'][stratum] = search
                search.update(selected_numbers=[], inspected=[], retrieved=[], excluded=[], duplicate_numbers=[])
                for item in result['items']:
                    number = item['number']
                    if number in activity_seen:
                        search['duplicate_numbers'].append(number)
                        continue
                    activity_seen.add(number)
                    search['selected_numbers'].append(number)
                    try:
                        pull = collect_pull(api, canonical, number, activity=True)
                        if activity_stratum(pull['detail']) != stratum:
                            raise APIError(f'repos/{canonical}/pulls/{number}', 'search_detail_mismatch')
                        path = publish_artifact(state, directory, 'pulls', number, pull)
                        entry = {'number': number, 'path': path, 'outcome': pull['outcome'],
                                 'stratum': stratum, 'contextual_only': True, 'body_sha256': body_hash(pull),
                                 'activity_eligible': pull['historical']['activity_eligible']}
                        search['inspected'].append(entry)
                        index['gaps'].extend(dict(g, pull_number=number) for g in pull['gaps'])
                        if not entry['activity_eligible']:
                            reason = ('no_eligible_activity' if pull['historical']['activity_evaluation_complete']
                                      else 'activity_unverified_incomplete_endpoints')
                            search['excluded'].append(dict(entry, reason=reason))
                            continue
                        index['activity_pulls'].append(entry)
                        search['retrieved'].append(number)
                    except APIError as exc:
                        index['gaps'].append(gap('activity_pull_failed', scope=str(number), error=exc.record))
            activity_coverage.update(
                inspected_pulls=sum(len(search['inspected']) for search in activity_coverage['searches'].values()),
                network_requests_this_run=api.network_requests - activity_network_before,
                cache_hits_this_run=api.cache_hits - activity_cache_before)
            for year in (2020, 2022, 2024):
                snapshot = collect_snapshot(api, canonical, year)
                path = publish_artifact(state, directory, 'snapshots', year, snapshot)
                index['snapshots'].append({'year': year, 'path': path, 'status': snapshot['status'],
                                          'commit_sha': snapshot.get('commit_sha'), 'commit_date': snapshot.get('commit_date'),
                                          'files': [{'path': row['path'], 'category': row['category']} for row in snapshot['files']]})
                index['gaps'].extend(dict(g, snapshot_year=year) for g in snapshot['gaps'])
            index['gaps'].append(gap('sample_not_exhaustive', severity='sampling',
                                     policy=index['coverage']['policy']))
            index['coverage'].update(retrieved_pulls=len(index['pulls']),
                                     retrieved_activity_pulls=len(index['activity_pulls']),
                                     retrieved_unique_pulls=len({x['number'] for x in index['pulls'] + index['activity_pulls']}),
                                     retrieved_snapshots=sum(bool(x.get('commit_sha')) for x in index['snapshots']),
                                     network_requests_this_run=api.network_requests, cache_hits_this_run=api.cache_hits)
            index['api_events'] = api.events
            index['status'] = 'partial' if any(g['severity'] == 'incomplete' for g in index['gaps']) else 'sampled'
            index['generated_at'] = utc_now()
            atomic_json(state, directory + '/index.json', index)
            return index
        except (APIError, OSError, ValueError, KeyError, TypeError) as exc:
            atomic_json(state, directory + '/collection.failure.json', {
                'schema_version': 1, 'repository': repo, 'observed_at': utc_now(), 'status': 'failed',
                'error': exc.record if isinstance(exc, APIError) else {'kind': type(exc).__name__, 'message': str(exc)},
                'previous_index_preserved': contained(state, directory + '/index.json').exists()})
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    subcommands = parser.add_subparsers(dest='command', required=True)
    subcommands.add_parser('discover')
    collect = subcommands.add_parser('collect')
    collect.add_argument('repo')
    collect.add_argument('--per-year', type=int, default=6)
    args = parser.parse_args(argv)
    try:
        if args.command == 'discover':
            result = discover(args.state)
            print(json.dumps({'path': str(state_root(args.state) / 'inventory.json'),
                              'repositories': len(result['repositories']),
                              'included': sum(x['included'] for x in result['repositories'])}))
        else:
            result = collect_repository(args.state, args.repo, per_year=args.per_year)
            print(json.dumps({'path': str(state_root(args.state) / 'corpus' / args.repo.replace('/', '--') / 'index.json'),
                              'status': result['status'], 'pulls': len(result['pulls']),
                              'snapshots': len(result['snapshots']), 'gaps': len(result['gaps'])}))
        return 0
    except (DiscoveryError, APIError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'collector failed: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('collector interrupted; cached pages retained for resume', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())

