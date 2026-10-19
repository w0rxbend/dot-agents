"""Offline structural tests. All historical-looking examples here are SYNTHETIC.

No fixture claims to reproduce a real GitHub event or a verified Scala rule.
"""
import copy
import hashlib
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'fixture/scala-library'
SKILL_ID = 'scala-fixture-resource-checks'
SHA_A = 'a' * 40
SHA_B = 'b' * 40

# SYNTHETIC documentation used only to test structural validation, not Scala.
SKILL = '''---
name: scala-fixture-resource-checks
description: Use when reviewing synthetic resource ownership changes in Scala fixtures.
license: MIT
---
# Synthetic resource checks

## When to Use
Use when a changed resource acquisition transfers ownership across a scope boundary.

## When Not to Use
Do not trigger for pure transformations without acquired handles or finalizers.

## Prerequisites
Inspect the synthetic build.sbt and detect the Scala and effect-library versions first.

## Workflow
1. Locate the acquisition and finalizer; trace ownership through every exceptional exit.
2. Add a failing cancellation test before changing the resource ownership boundary.

## Review and Refactoring Checks
Preserve the invariant that every acquired handle closes exactly once. False positives:
a caller-owned handle must not be closed merely because a method accepts it.

## Validation
For this synthetic fixture only, run `sbt 'core/testOnly fixture.ResourceSpec'` and
check that cancellation triggers exactly one finalizer without leaked handles.

## Examples
### Happy path
A scoped fixture acquires one handle and releases it after both success and cancellation.
```scala
val result = withHandle(handle => consume(handle)) // SYNTHETIC pseudocode
```
### Broken example and correction
Broken: the fixture exits on cancellation without releasing its acquired handle.
Correction: move acquisition inside the scope and add a cancellation-finalizer assertion.
```scala
val handle = acquire() // broken SYNTHETIC pseudocode
val fixed = withHandle(handle => consume(handle)) // corrected fixture
```
### Negative / should-not-trigger case
A pure list mapping acquires no external handles; do not introduce resource scopes.
```scala
val doubled = List(1, 2).map(_ * 2) // SYNTHETIC negative example
```

## Output Contract
Report file:line, severity, evidence ID and the regression test; explain which ownership
invariant fails and distinguish actual execution from a model-based prediction.

## Limitations
These synthetic fixtures establish structural behavior only, not historical source truth.

## Sources
Read the [attributed synthetic evidence](references/evidence.json) before applying a rule.
'''


def report_fixture():
    """SYNTHETIC records; these GitHub-shaped URLs are never fetched."""
    return {
        'schema_version': 1, 'repository': REPOSITORY, 'status': 'complete',
        'summary': 'Synthetic structural fixture for a focused resource ownership review skill.',
        'gaps': ['Synthetic inputs do not establish any historical source or semantic facts.'],
        'evidence': [
            {'id': 'review-1', 'kind': 'review-comment', 'repository': REPOSITORY,
             'url': f'https://github.com/{REPOSITORY}/pull/11#discussion_r22',
             'occurred_at': '2022-04-03T12:00:00Z', 'author': 'fixture-reviewer',
             'role_basis': 'unknown',
             'excerpt': 'Synthetic: cancellation must release the acquired handle before returning control.',
             'interpretation': 'Synthetic discussion requests an observable finalizer assertion on cancellation.'},
            {'id': 'source-1', 'kind': 'code', 'repository': REPOSITORY,
             'url': f'https://github.com/{REPOSITORY}/blob/{SHA_A}/core/src/Resource.scala#L3-L9',
             'commit_sha': SHA_A, 'path': 'core/src/Resource.scala',
             'occurred_at': '2021-01-02T00:00:00Z',
             'excerpt': 'Synthetic: acquire a handle inside a scope and attach its finalizer.',
             'interpretation': 'Synthetic source demonstrates that ownership belongs to the acquisition scope.'},
            {'id': 'test-1', 'kind': 'code', 'repository': REPOSITORY,
             'url': f'https://github.com/{REPOSITORY}/blob/{SHA_B}/core/test/ResourceSpec.scala',
             'commit_sha': SHA_B, 'path': 'core/test/ResourceSpec.scala',
             'occurred_at': '2023-05-06T00:00:00Z',
             'excerpt': 'Synthetic: assert that cancellation executes the registered release exactly once.',
             'interpretation': 'Synthetic test distinguishes successful return from cancellation cleanup behavior.'},
        ],
        'claims': [{'id': 'claim-1',
                    'rule': 'Inference: when acquisition changes scope, trace exceptional exits and assert exactly one release.',
                    'evidence_ids': ['review-1', 'source-1', 'test-1'],
                    'applicability': 'Synthetic Scala resource APIs with explicit ownership; detect library versions first.',
                    'counterexample': 'A pure list transformation acquires no resource and must not introduce finalizers.'}],
        'skills': [{'id': SKILL_ID, 'kind': 'review', 'claim_ids': ['claim-1']}],
        'coverage': {'examined_prs': [11], 'substantive_reviewer_exchanges': ['review-1'],
                     'years_sampled': [2021, 2022, 2023],
                     'inspected_source_paths': ['core/src/Resource.scala', 'core/test/ResourceSpec.scala'],
                     'gaps': ['Synthetic fixtures cannot establish empirical historical coverage.']},
    }


class CandidateQualityTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(os.environ.get('TMPDIR', Path.home() / '.hermes/cache/scratch'))
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='scala-quality-', dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        # Resolve: candidates behind a symlinked ancestor (macOS /var -> /private/var) are rejected.
        self.root = Path(self.tmp.name).resolve()

    def quality(self):
        self.assertTrue((ROOT / 'scripts/scala_research/quality.py').is_file(),
                        'The candidate validator must exist before its interface can be exercised')
        return importlib.import_module('scripts.scala_research.quality')

    def write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

    def write_candidate(self, report=None, skill=SKILL):
        report = copy.deepcopy(report_fixture() if report is None else report)
        candidate = self.root / 'candidate'
        self.write_json(candidate / 'report.json', report)
        for item in report.get('skills', []):
            if not isinstance(item, dict) or item.get('id') != SKILL_ID:
                continue
            selected_claims = [c for c in report['claims'] if isinstance(c, dict)
                               and c.get('id') in item.get('claim_ids', [])]
            used = {eid for c in selected_claims for eid in c.get('evidence_ids', [])
                    if isinstance(eid, str)}
            local = {'schema_version': 1, 'repository': report['repository'],
                     'claims': selected_claims,
                     'evidence': [e for e in report['evidence'] if isinstance(e, dict)
                                  and e.get('id') in used]}
            directory = candidate / 'skills' / SKILL_ID
            self.write_json(directory / 'references/evidence.json', local)
            (directory / 'SKILL.md').write_text(skill, encoding='utf-8')
        return candidate

    def assert_invalid(self, candidate, expected, repository=REPOSITORY):
        errors = self.quality().validate_candidate(candidate, repository)
        self.assertTrue(errors, f'expected a structural error containing {expected!r}')
        self.assertIn(expected.casefold(), '\n'.join(errors).casefold())

    def test_valid_complete_synthetic_candidate(self):
        self.assertEqual(self.quality().validate_candidate(self.write_candidate(), REPOSITORY), [])

    def test_fractional_seconds_of_any_supported_width_parse(self):
        for value in ('2022-04-03T12:00:00.5Z', '2022-04-03T12:00:00.12345+02:00', '2022-04-03T12:00:00.123456Z'):
            with self.subTest(value=value):
                report = report_fixture()
                report['evidence'][0]['occurred_at'] = value
                candidate = self.write_candidate(report)
                self.assertEqual([], self.quality().validate_candidate(candidate, REPOSITORY))

    def write_corpus(self, **changes):
        """SYNTHETIC cached PR artifact in the collector layout; never fetched."""
        comment = dict(id=22, body='Synthetic:  cancellation must release the acquired handle\nbefore returning control.',
                       created_at='2022-04-03T12:00:00Z', user={'login': 'fixture-reviewer'})
        comment.update(changes.pop('comment', {}))
        artifact = dict(schema_version=1, repository=REPOSITORY, number=11, review_comments=[comment],
                        issue_comments=[], reviews=[],
                        historical={'eligible_ids': {'review_comments': changes.pop('eligible', [22]),
                                                     'issue_comments': [], 'reviews': []}})
        corpus = self.root / 'corpus'
        self.write_json(corpus / 'pulls/11-synthetic.json', artifact)
        self.write_json(corpus / 'index.json', {'repository': REPOSITORY, 'activity_pulls': [],
                                                'pulls': [{'number': 11, 'path': 'pulls/11-synthetic.json'}]})
        return corpus

    def test_corpus_cross_check_accepts_a_faithful_quotation(self):
        corpus = self.write_corpus()
        self.assertEqual([], self.quality().validate_candidate(self.write_candidate(), REPOSITORY, corpus=corpus))
        report = report_fixture()
        report['evidence'][0]['excerpt'] = 'Synthetic: cancellation must release ... before returning control.'
        self.assertEqual([], self.quality().validate_candidate(self.write_candidate(report), REPOSITORY, corpus=corpus))

    def test_corpus_cross_check_rejects_invented_or_misdated_evidence(self):
        cases = [
            (dict(comment={'body': 'Synthetic: a different remark entirely, about naming.'}), 'not a quotation'),
            (dict(comment={'created_at': '2025-02-01T00:00:00Z'}), 'occurred_at'),
            (dict(comment={'user': {'login': 'someone-else'}}), 'author'),
            (dict(eligible=[]), 'outside 2018-2024'),
            (dict(comment={'id': 23}), 'not in cached PR #11'),
        ]
        for changes, expected in cases:
            with self.subTest(expected=expected):
                corpus = self.write_corpus(**copy.deepcopy(changes))
                errors = self.quality().validate_candidate(self.write_candidate(), REPOSITORY, corpus=corpus)
                self.assertIn(expected.casefold(), '\n'.join(errors).casefold())

    def test_corpus_cross_check_skips_pulls_outside_the_cached_sample(self):
        corpus = self.write_corpus()
        self.write_json(corpus / 'index.json', {'repository': REPOSITORY, 'pulls': [], 'activity_pulls': []})
        self.assertEqual([], self.quality().validate_candidate(self.write_candidate(), REPOSITORY, corpus=corpus))

    def test_report_schema_and_reference_failures(self):
        cases = [
            ('schema_version', True, 'schema_version'),
            ('repository', 'other/library', 'repository'),
            ('status', 'accepted', 'status'),
            ('summary', '', 'summary'),
            ('gaps', 'none', 'gaps'),
            ('evidence', {}, 'evidence'),
            ('claims', {}, 'claims'),
            ('skills', {}, 'skills'),
            ('coverage', [], 'coverage'),
        ]
        for key, value, error in cases:
            with self.subTest(key=key):
                candidate = self.write_candidate()
                report = report_fixture()
                report[key] = value
                self.write_json(candidate / 'report.json', report)
                self.assert_invalid(candidate, error)
        for collection in ('evidence', 'claims', 'skills'):
            with self.subTest(duplicate=collection):
                report = report_fixture()
                report[collection].append(copy.deepcopy(report[collection][0]))
                self.assert_invalid(self.write_candidate(report), 'duplicate')
        report = report_fixture()
        report['claims'][0]['evidence_ids'] = ['missing-evidence']
        self.assert_invalid(self.write_candidate(report), 'missing-evidence')
        report = report_fixture()
        report['skills'][0]['claim_ids'] = ['missing-claim']
        self.assert_invalid(self.write_candidate(report), 'missing-claim')

    def test_blocked_report_is_a_valid_outcome_not_an_accepted_skill(self):
        report = report_fixture()
        report.update(status='blocked', evidence=[], claims=[], skills=[])
        report['coverage'] = {key: [] for key in report['coverage']}
        candidate = self.write_candidate(report)
        self.assertEqual(self.quality().validate_candidate(candidate, REPOSITORY), [])
        report['gaps'] = []
        self.write_json(candidate / 'report.json', report)
        self.assert_invalid(candidate, 'blocked')

    def test_invalid_repository_identifiers_are_not_repaired(self):
        for repository in (' ../owner/repo', 'owner/repo/', 'owner//repo', 'owner',
                           'https://github.com/a/b', ' owner/repo', 'owner/..', ''):
            with self.subTest(repository=repository):
                self.assert_invalid(self.write_candidate(), 'repository', repository)

    def test_invalid_json_duplicate_keys_and_nonfinite_values(self):
        candidate = self.write_candidate()
        for text in ('{', '[]', '{"schema_version":1,"schema_version":1}',
                     '{"score":NaN}', '{"score":Infinity}'):
            with self.subTest(text=text):
                (candidate / 'report.json').write_text(text, encoding='utf-8')
                self.assert_invalid(candidate, 'report.json')

    def test_dates_are_real_timezone_aware_instants_within_utc_window(self):
        invalid = ('2017-12-31T23:59:59Z', '2025-01-01T00:00:00Z', '2024-02-30T12:00:00Z',
                   '2023-02-29T12:00:00Z', '2022-04-03', '2022-04-03T12:00:00',
                   '2022-04-03T25:00:00Z', '2022-04-03T12:00:00+25:00',
                   '2024-12-31T23:30:00-01:00', '2018-01-01T00:30:00+01:00',
                   '20220101T120000Z', '2022-W01-1T12:00:00Z', None, 2022)
        for value in invalid:
            with self.subTest(value=value):
                report = report_fixture()
                report['evidence'][0]['occurred_at'] = value
                self.assert_invalid(self.write_candidate(report), 'occurred_at')
        for value in ('2018-01-01T00:00:00Z', '2024-12-31T23:59:59.999999Z',
                      '2024-02-29T00:00:00+00:00', '2025-01-01T00:30:00+01:00'):
            with self.subTest(valid=value):
                report = report_fixture()
                report['evidence'][0]['occurred_at'] = value
                report['coverage']['years_sampled'] = list(range(2018, 2025))
                self.assertEqual(self.quality().validate_candidate(self.write_candidate(report), REPOSITORY), [])

    def test_source_urls_bind_original_github_repository_and_full_sha(self):
        base = f'https://github.com/{REPOSITORY}'
        invalid = ('https://example.com/a', base.replace('https:', 'http:') + '/pull/11',
                   base.replace('github.com', 'github.com.evil.test') + '/pull/11#discussion_r22',
                   base.replace('github.com', 'user@github.com') + '/pull/11#discussion_r22',
                   base.replace('github.com', 'github.com:443') + '/pull/11#discussion_r22',
                   'https://github.com/other/repo/pull/11#discussion_r22',
                   base + '/pull/11', base + '/pull/11#issuecomment-22',
                   base + '/pull/11?token=anything#discussion_r22',
                   base + '/pull/11#discussion_r0', base + '/pull/../11#discussion_r22',
                   '\n' + base + '/pull/11#discussion_r22')
        for value in invalid:
            with self.subTest(value=value):
                report = report_fixture()
                report['evidence'][0]['url'] = value
                self.assert_invalid(self.write_candidate(report), 'url')
        for suffix in ('blob/main/core/src/Resource.scala', 'blob/abcdef0/core/src/Resource.scala',
                       f'blob/{SHA_A}/../Resource.scala', f'blob/{SHA_A}/%2e%2e/Resource.scala',
                       f'blob/{SHA_A}/core/src/Other.scala', f'blob/{SHA_B}/core/src/Resource.scala'):
            with self.subTest(source=suffix):
                report = report_fixture()
                report['evidence'][1]['url'] = base + '/' + suffix
                self.assert_invalid(self.write_candidate(report), 'url')

    def test_evidence_fields_and_review_substance(self):
        cases = [('kind', 'approval'), ('repository', 'unrelated/library'),
                 ('excerpt', ''), ('interpretation', 'approved'), ('author', ''),
                 ('role_basis', ''), ('excerpt', 'LGTM'), ('excerpt', 'Approved. ' * 20)]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                report = report_fixture()
                report['evidence'][0][field] = value
                self.assert_invalid(self.write_candidate(report), field)
        for field in ('commit_sha', 'path'):
            with self.subTest(missing=field):
                report = report_fixture()
                del report['evidence'][1][field]
                self.assert_invalid(self.write_candidate(report), field)

    def test_source_only_claims_must_mark_inference(self):
        report = report_fixture()
        report['claims'][0]['evidence_ids'] = ['source-1', 'test-1']
        report['claims'][0]['rule'] = 'When acquisition changes scope, trace exceptional exits and assert exactly one release.'
        self.assert_invalid(self.write_candidate(report), 'inference')
        report['claims'][0]['rule'] = 'Maintainers prefer that acquisition changes always include a finalizer assertion.'
        report['claims'][0]['applicability'] += ' This is an inference, not an observed reviewer preference.'
        self.assert_invalid(self.write_candidate(report), 'review')

    def test_coverage_requires_typed_lists_and_cited_sources(self):
        for field in report_fixture()['coverage']:
            with self.subTest(missing=field):
                report = report_fixture()
                del report['coverage'][field]
                self.assert_invalid(self.write_candidate(report), 'coverage')
        for field, value in [('examined_prs', [True]), ('years_sampled', [2017]),
                             ('years_sampled', [2021, 2023]), ('inspected_source_paths', ['../outside']),
                             ('substantive_reviewer_exchanges', ['missing-review'])]:
            with self.subTest(field=field, value=value):
                report = report_fixture()
                report['coverage'][field] = value
                self.assert_invalid(self.write_candidate(report), 'coverage')

    def test_skill_frontmatter_required_sections_and_examples(self):
        cases = [
            ('missing frontmatter', SKILL.partition('---\n#')[2], 'frontmatter'),
            ('name mismatch', SKILL.replace(f'name: {SKILL_ID}', 'name: scala-other'), 'name'),
            ('duplicate frontmatter', SKILL.replace('license: MIT', f'name: {SKILL_ID}\nlicense: MIT'), 'duplicate'),
            ('empty description', SKILL.replace('description: Use when reviewing synthetic resource ownership changes in Scala fixtures.', 'description:'), 'description'),
            ('missing workflow', SKILL.replace('## Workflow', '## Background'), 'workflow'),
            ('empty checks', SKILL.replace('Preserve the invariant that every acquired handle closes exactly once. False positives:\na caller-owned handle must not be closed merely because a method accepts it.', 'LGTM'), 'checks'),
            ('missing happy case', SKILL.replace('### Happy path', '### Miscellaneous'), 'happy'),
            ('missing correction', SKILL.replace('correction', 'reason').replace('Correction:', 'Reason:').replace('corrected', 'changed').replace('fixed', 'changed'), 'correction'),
            ('missing negative case', SKILL.replace('### Negative / should-not-trigger case', '### Miscellaneous'), 'negative'),
            ('missing output', SKILL.replace('file:line, severity, evidence ID and the regression test', 'a short summary with no finding details'), 'output'),
            ('no command', SKILL.replace("`sbt 'core/testOnly fixture.ResourceSpec'`", 'the tests'), 'validation'),
            ('missing evidence link', SKILL.replace('[attributed synthetic evidence](references/evidence.json)', 'attributed synthetic evidence'), 'evidence.json'),
            ('fenced fake sections', SKILL.replace('## Workflow', '```text\n## Workflow') + '\n```', 'workflow'),
        ]
        for label, text, expected in cases:
            with self.subTest(label=label):
                self.assert_invalid(self.write_candidate(skill=text), expected)

    def test_relative_links_and_reference_definitions_resolve_inside_skill(self):
        for target in ('references/missing.md', '../outside.md', '%2e%2e/outside.md',
                       '/etc/passwd', 'file:///etc/passwd', 'references/%252e%252e/outside.md',
                       'references\\outside.md', 'references/evidence.json?secret=1'):
            with self.subTest(target=target):
                self.assert_invalid(self.write_candidate(skill=SKILL + f'\n[extra]({target})\n'), 'link')
        text = SKILL.replace('[attributed synthetic evidence](references/evidence.json)',
                             '[attributed synthetic evidence][evidence]')
        text += '\n[evidence]: references/evidence.json\n'
        self.assertEqual(self.quality().validate_candidate(self.write_candidate(skill=text), REPOSITORY), [])
        self.assert_invalid(self.write_candidate(skill=SKILL + '\n[extra][missing]\n'), 'link')

    def test_evidence_manifest_exactly_matches_claims_and_sources(self):
        for mutation in ('missing', 'extra', 'changed', 'repository', 'schema_version', 'duplicate', 'claim'):
            with self.subTest(mutation=mutation):
                candidate = self.write_candidate()
                path = candidate / 'skills' / SKILL_ID / 'references/evidence.json'
                local = json.loads(path.read_text())
                if mutation == 'missing':
                    local['evidence'].pop()
                elif mutation == 'extra':
                    item = copy.deepcopy(local['evidence'][0])
                    item['id'] = 'unused-evidence'
                    local['evidence'].append(item)
                elif mutation == 'changed':
                    local['evidence'][0]['excerpt'] += ' Not in the report.'
                elif mutation == 'repository':
                    local['repository'] = 'other/library'
                elif mutation == 'schema_version':
                    local['schema_version'] = True
                elif mutation == 'duplicate':
                    local['claims'].append(copy.deepcopy(local['claims'][0]))
                else:
                    local['claims'][0]['counterexample'] += ' Different boundary.'
                self.write_json(path, local)
                self.assert_invalid(candidate, 'evidence.json')

    def test_each_skill_requires_three_evidence_records_with_source_and_multiple_anchors(self):
        report = report_fixture()
        report['claims'][0]['evidence_ids'] = ['review-1', 'source-1']
        self.assert_invalid(self.write_candidate(report), 'three')
        report = report_fixture()
        for index, record in enumerate(report['evidence']):
            record.update(kind='review-comment', author='fixture-author', role_basis='unknown',
                          url=f'https://github.com/{REPOSITORY}/pull/11#discussion_r{index + 10}')
        self.assert_invalid(self.write_candidate(report), 'source/test')
        report = report_fixture()
        for index, record in enumerate(report['evidence']):
            path = f'src/Fixture{index}.scala'
            record.update(kind='code', commit_sha=SHA_A, path=path,
                          url=f'https://github.com/{REPOSITORY}/blob/{SHA_A}/{path}')
        report['coverage']['inspected_source_paths'] = [r['path'] for r in report['evidence']]
        report['coverage']['substantive_reviewer_exchanges'] = []
        self.assert_invalid(self.write_candidate(report), 'two historical')

    def test_extra_skill_directory_and_unsafe_ids_are_rejected(self):
        candidate = self.write_candidate()
        (candidate / 'skills/scala-unreported').mkdir()
        self.assert_invalid(candidate, 'unreported')
        (candidate / 'skills/scala-unreported').rmdir()
        for identifier in ('../outside', '/absolute', 'generic', 'scala-UPPER'):
            with self.subTest(identifier=identifier):
                report = report_fixture()
                report['skills'][0]['id'] = identifier
                self.write_json(candidate / 'report.json', report)
                self.assert_invalid(candidate, 'id')

    def test_symlinks_and_special_files_fail_closed_even_when_unreferenced(self):
        candidate = self.write_candidate()
        outside = self.root / 'outside.json'
        outside.write_text('do not read this file', encoding='utf-8')
        link = candidate / 'unused-link'
        for target in (outside, candidate / 'report.json', candidate / 'missing', candidate):
            with self.subTest(target=target):
                link.symlink_to(target)
                self.assert_invalid(candidate, 'symlink')
                link.unlink()
        directory_link = self.root / 'candidate-link'
        directory_link.symlink_to(candidate, target_is_directory=True)
        self.assert_invalid(directory_link, 'symlink')
        if hasattr(os, 'mkfifo'):
            os.mkfifo(candidate / 'pipe')
            self.assert_invalid(candidate, 'special')

    def test_artifact_read_errors_and_nested_reference_links(self):
        candidate = self.write_candidate()
        markdown = candidate / 'skills' / SKILL_ID / 'SKILL.md'
        markdown.unlink()
        self.assert_invalid(candidate, 'SKILL.md')
        candidate = self.write_candidate()
        markdown.write_bytes(b'\xff\xfe')
        self.assert_invalid(candidate, 'utf-8')
        candidate = self.write_candidate()
        nested = candidate / 'skills' / SKILL_ID / 'references/extra.md'
        nested.write_text('[unsafe](../../../../outside.json)\n', encoding='utf-8')
        self.assert_invalid(candidate, 'link')

    def test_validation_does_not_mutate_candidate_artifacts(self):
        candidate = self.write_candidate()
        def snapshot():
            return {p.relative_to(candidate).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                    for p in candidate.rglob('*') if p.is_file()}
        before = snapshot()
        self.assertEqual(self.quality().validate_candidate(candidate, REPOSITORY), [])
        self.assertEqual(before, snapshot())

    def write_review(self, candidate, review=None):
        if review is None:
            review = {
                'schema_version': 1, 'repository': REPOSITORY, 'verdict': 'accept',
                'report_sha256': hashlib.sha256((candidate / 'report.json').read_bytes()).hexdigest(),
                'findings': [], 'verified_evidence_ids': ['review-1', 'source-1', 'test-1'],
                'evaluation_mode': 'model-based',
                'evaluated_skills': [{
                    'id': SKILL_ID, 'result': 'pass',
                    'positive': 'Synthetic positive case: a scoped acquisition closes its handle after cancellation; the skill preserves that assertion.',
                    'negative': 'Synthetic negative case: a pure mapping owns no resource; applying the trigger correctly leaves that function unchanged.',
                    'repair': 'Synthetic repair case: move the leaked acquisition inside its owner scope and add a finalizer-count assertion to the fixture.',
                    'holdout': 'Synthetic held-out case: an independently authored early-return scenario still releases its owned handle without closing borrowed values.',
                    'notes': 'Model-based evaluation of synthetic fixtures only; no Scala was compiled or executed and no remote citation was actually verified.',
                }],
            }
        path = self.root / 'reviews/review.json'
        self.write_json(path, review)
        return path

    def assert_bad_review(self, review, candidate, expected):
        path = self.write_review(candidate, review)
        errors = self.quality().validate_review(path, candidate, REPOSITORY)
        self.assertTrue(errors, f'expected review error containing {expected!r}')
        self.assertIn(expected.casefold(), '\n'.join(errors).casefold())

    def test_valid_review_and_report_byte_hash(self):
        candidate = self.write_candidate()
        path = self.write_review(candidate)
        self.assertTrue(hasattr(self.quality(), 'validate_review'), 'Expose validate_review alongside candidate validation')
        self.assertEqual(self.quality().validate_review(path, candidate, REPOSITORY), [])
        with (candidate / 'report.json').open('a', encoding='utf-8') as stream:
            stream.write('\n')
        errors = self.quality().validate_review(path, candidate, REPOSITORY)
        self.assertIn('report_sha256', '\n'.join(errors))

    def test_review_schema_unknown_duplicate_and_missing_skill_evaluations(self):
        candidate = self.write_candidate()
        review = json.loads(self.write_review(candidate).read_text())
        for field, value in [('schema_version', True), ('repository', 'other/library'),
                             ('verdict', 'approved'), ('report_sha256', 'a' * 63),
                             ('findings', {}), ('verified_evidence_ids', []),
                             ('verified_evidence_ids', ['missing-evidence']),
                             ('verified_evidence_ids', ['review-1', 'review-1']),
                             ('evaluated_skills', []), ('evaluation_mode', 'proven')]:
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(review)
                changed[field] = value
                self.assert_bad_review(changed, candidate, field)
        changed = copy.deepcopy(review)
        changed['evaluated_skills'].append(copy.deepcopy(changed['evaluated_skills'][0]))
        self.assert_bad_review(changed, candidate, 'duplicate')
        changed['evaluated_skills'][1]['id'] = 'scala-unreported'
        self.assert_bad_review(changed, candidate, 'unknown')

    def test_each_evaluation_dimension_requires_substance_or_readable_artifact(self):
        candidate = self.write_candidate()
        review = json.loads(self.write_review(candidate).read_text())
        for field in ('positive', 'negative', 'repair', 'holdout', 'notes'):
            for value in (True, False, {}, [], '', 'pass', 'LGTM', 'passed ' * 50):
                with self.subTest(field=field, value=value):
                    changed = copy.deepcopy(review)
                    changed['evaluated_skills'][0][field] = value
                    self.assert_bad_review(changed, candidate, field)
        changed = copy.deepcopy(review)
        changed['evaluated_skills'][0]['negative'] = changed['evaluated_skills'][0]['positive']
        self.assert_bad_review(changed, candidate, 'distinct')
        for value in ('cases/missing.md', '../outside.md', '/etc/passwd', 'file:///etc/passwd'):
            with self.subTest(path=value):
                changed = copy.deepcopy(review)
                changed['evaluated_skills'][0]['positive'] = value
                self.assert_bad_review(changed, candidate, 'positive')
        artifact = self.root / 'reviews/cases/positive.md'
        artifact.parent.mkdir(parents=True)
        artifact.write_text(review['evaluated_skills'][0]['positive'], encoding='utf-8')
        changed = copy.deepcopy(review)
        changed['evaluated_skills'][0]['positive'] = 'cases/positive.md'
        path = self.write_review(candidate, changed)
        self.assertEqual(self.quality().validate_review(path, candidate, REPOSITORY), [])
        artifact.write_text('LGTM', encoding='utf-8')
        self.assert_bad_review(changed, candidate, 'positive')

    def test_accept_requires_pass_all_citations_and_no_blocking_findings(self):
        candidate = self.write_candidate()
        review = json.loads(self.write_review(candidate).read_text())
        changed = copy.deepcopy(review)
        changed['evaluated_skills'][0]['result'] = 'fail'
        self.assert_bad_review(changed, candidate, 'pass')
        changed['evaluated_skills'][0]['result'] = True
        self.assert_bad_review(changed, candidate, 'result')
        changed = copy.deepcopy(review)
        changed['verified_evidence_ids'] = ['review-1']
        self.assert_bad_review(changed, candidate, 'verified')
        finding = {'severity': 'high', 'skill_id': SKILL_ID,
                   'problem': 'Synthetic blocking case: the cancellation rule omits a caller-owned handle boundary.',
                   'evidence': ['source-1']}
        for severity in ('critical', 'high', 'medium', 'blocker', 'blocking', 'error'):
            with self.subTest(severity=severity):
                changed = copy.deepcopy(review)
                changed['findings'] = [dict(finding, severity=severity)]
                self.assert_bad_review(changed, candidate, 'blocking')
        changed['findings'] = [dict(finding, severity='low', blocking=True)]
        self.assert_bad_review(changed, candidate, 'blocking')
        changed['findings'] = [dict(finding, severity='low', blocking=False)]
        self.assertEqual(self.quality().validate_review(self.write_review(candidate, changed), candidate, REPOSITORY), [])

    def test_findings_and_nonaccept_verdicts_require_actionable_evidence(self):
        candidate = self.write_candidate()
        review = json.loads(self.write_review(candidate).read_text())
        review['verdict'] = 'revise'
        self.assert_bad_review(review, candidate, 'findings')
        finding = {'severity': 'high', 'skill_id': SKILL_ID,
                   'problem': 'Synthetic blocking case: the cancellation rule omits a caller-owned handle boundary.',
                   'evidence': ['source-1']}
        for field, value in [('severity', 'meh'), ('skill_id', 'scala-unknown'),
                             ('problem', 'bad'), ('evidence', []), ('evidence', ['unknown-id']),
                             ('blocking', 'false')]:
            with self.subTest(field=field):
                review['findings'] = [dict(finding, **{field: value})]
                self.assert_bad_review(review, candidate, field)
        review['findings'] = [finding]
        review['evaluated_skills'][0]['result'] = 'fail'
        self.assertEqual(self.quality().validate_review(self.write_review(candidate, review), candidate, REPOSITORY), [])
        review['verdict'] = 'blocked'
        self.assertEqual(self.quality().validate_review(self.write_review(candidate, review), candidate, REPOSITORY), [])

    def test_actual_execution_requires_recorded_artifacts_not_a_label(self):
        candidate = self.write_candidate()
        review = json.loads(self.write_review(candidate).read_text())
        review['evaluation_mode'] = 'execution'
        self.assert_bad_review(review, candidate, 'execution_evidence')
        review['execution_evidence'] = ['logs/compile.txt']
        self.assert_bad_review(review, candidate, 'execution_evidence')

    def test_review_cannot_accept_blocked_or_structurally_invalid_candidate(self):
        candidate = self.write_candidate()
        report = report_fixture()
        report['status'] = 'blocked'
        self.write_json(candidate / 'report.json', report)
        review = json.loads(self.write_review(candidate).read_text())
        self.assert_bad_review(review, candidate, 'complete')
        candidate = self.write_candidate(skill=SKILL.replace('## Workflow', '## Background'))
        path = self.write_review(candidate)
        self.assertIn('Workflow', '\n'.join(self.quality().validate_review(path, candidate, REPOSITORY)))

    def test_review_artifacts_and_bytes_are_read_only(self):
        candidate = self.write_candidate()
        path = self.write_review(candidate)
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(self.quality().validate_review(path, candidate, REPOSITORY), [])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()})
        alternate = path.with_name('symlink.json')
        alternate.symlink_to(path)
        self.assertIn('symlink', '\n'.join(self.quality().validate_review(alternate, candidate, REPOSITORY)))

    def test_cli_json_output_exit_status_and_required_arguments(self):
        candidate = self.write_candidate()
        review = self.write_review(candidate)
        prefix = [sys.executable, '-m', 'scripts.scala_research.quality']
        for mode, path, extra in [('candidate', candidate, []),
                                  ('review', review, ['--candidate', str(candidate)])]:
            with self.subTest(mode=mode):
                result = subprocess.run(prefix + [mode, str(path), '--repository', REPOSITORY] + extra,
                                        cwd=ROOT, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                output = json.loads(result.stdout)
                self.assertTrue(output['structurally_valid'])
                self.assertFalse(output['source_verified'])
                self.assertEqual(output['scope'], 'structural-only')
        result = subprocess.run(prefix + ['review', str(review), '--repository', REPOSITORY],
                                cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--candidate', result.stderr)
        result = subprocess.run(prefix + ['candidate', str(candidate), '--repository', '../invalid'],
                                cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['structurally_valid'])

    def test_nested_wrong_types_fail_closed_instead_of_crashing(self):
        candidate = self.write_candidate()
        # All inputs below are SYNTHETIC mutations.
        targets = [('evidence', 0, key) for key in ('id', 'kind', 'repository', 'url', 'occurred_at',
                                                   'excerpt', 'interpretation', 'author', 'role_basis')]
        targets += [('claims', 0, key) for key in ('id', 'rule', 'applicability', 'counterexample', 'evidence_ids')]
        targets += [('skills', 0, key) for key in ('id', 'kind', 'claim_ids')]
        for target in targets:
            for value in (None, {}, [], True, 0):
                with self.subTest(target=target, value=value):
                    report = report_fixture()
                    report[target[0]][target[1]][target[2]] = value
                    self.write_json(candidate / 'report.json', report)
                    self.assertTrue(self.quality().validate_candidate(candidate, REPOSITORY))
        candidate = self.write_candidate()
        original = json.loads(self.write_review(candidate).read_text())
        for field in ('schema_version', 'repository', 'verdict', 'report_sha256',
                      'findings', 'verified_evidence_ids', 'evaluated_skills', 'evaluation_mode'):
            for value in (None, {}, True, 0):
                with self.subTest(review_field=field, value=value):
                    review = copy.deepcopy(original)
                    review[field] = value
                    self.assert_bad_review(review, candidate, field)

    def test_nonfinite_exponent_and_role_labels_are_not_evidence(self):
        candidate = self.write_candidate()
        report = json.dumps(report_fixture())
        (candidate / 'report.json').write_text(report[:-1] + ', "extra": 1e999}', encoding='utf-8')
        self.assert_invalid(candidate, 'nonfinite')
        report = report_fixture()
        report['evidence'][0]['role_basis'] = 'maintainer'
        self.assert_invalid(self.write_candidate(report), 'role_basis')

    def test_all_supported_original_source_kinds_and_inference_only_rules(self):
        for kind, suffix in [('review', 'pull/11#pullrequestreview-22'),
                             ('issue-comment', 'issues/11#issuecomment-22'),
                             ('commit', f'commit/{SHA_A}'),
                             ('documentation', f'blob/{SHA_A}/docs/resource.md')]:
            with self.subTest(kind=kind):
                report = report_fixture()
                record = report['evidence'][0]
                record.update(kind=kind, url=f'https://github.com/{REPOSITORY}/{suffix}')
                if kind in ('commit', 'documentation'):
                    report['coverage']['substantive_reviewer_exchanges'] = []
                self.assertEqual(self.quality().validate_candidate(self.write_candidate(report), REPOSITORY), [])

    def test_hidden_headings_empty_workflows_and_collapsed_examples_fail(self):
        hidden = SKILL.replace('## Workflow', '<!--\n## Workflow').replace('## Review and Refactoring Checks', '-->\n## Review and Refactoring Checks')
        self.assert_invalid(self.write_candidate(skill=hidden), 'Workflow')
        empty = SKILL.replace('## Workflow\n1.', '## Workflow\n<!--\n1.').replace('## Review and Refactoring Checks', '-->\n## Review and Refactoring Checks')
        self.assert_invalid(self.write_candidate(skill=empty), 'Workflow')
        empty = SKILL.replace('## Workflow', '##\nWorkflow')
        self.assert_invalid(self.write_candidate(skill=empty), 'Workflow')
        start, end = SKILL.index('## Examples'), SKILL.index('## Output Contract')
        combined = ('## Examples\n### Happy broken negative\n'
                    'A synthetic resource leaks its acquired handle on cancellation; correction moves the acquisition inside its owner scope.\n\n')
        self.assert_invalid(self.write_candidate(skill=SKILL[:start] + combined + SKILL[end:]), 'distinct')

    def test_execution_logs_and_mixed_modes_are_structural_not_execution_proof(self):
        candidate = self.write_candidate()
        path = self.write_review(candidate)
        review = json.loads(path.read_text())
        review['evaluation_mode'] = 'execution'
        review['execution_evidence'] = ['logs/run.txt']
        log = path.parent / 'logs/run.txt'
        log.parent.mkdir()
        log.write_text('SYNTHETIC log: command sbt core/test; expected fixture output and exit status recorded for structural testing only.', encoding='utf-8')
        self.assertEqual(self.quality().validate_review(self.write_review(candidate, review), candidate, REPOSITORY), [])
        review['evaluation_mode'] = 'mixed'
        self.assert_bad_review(review, candidate, 'evaluation_mode')
        review['evaluated_skills'][0]['evaluation_mode'] = 'model-based'
        self.assertEqual(self.quality().validate_review(self.write_review(candidate, review), candidate, REPOSITORY), [])
        real = log.with_suffix('.real')
        log.rename(real)
        log.symlink_to(real)
        self.assert_bad_review(review, candidate, 'symlink')

    def test_source_length_limits_duplicate_urls_and_reference_ids(self):
        report = report_fixture()
        report['evidence'][0]['excerpt'] = 'substantive synthetic words explaining a cancellation resource failure ' * 40
        self.assert_invalid(self.write_candidate(report), 'excerpt')
        report = report_fixture()
        report['evidence'][2] = dict(report['evidence'][1], id='test-1')
        self.assert_invalid(self.write_candidate(report), 'duplicate source URL')
        for where, field, duplicate in [('claims', 'evidence_ids', 'source-1'), ('skills', 'claim_ids', 'claim-1')]:
            report = report_fixture()
            report[where][0][field].append(duplicate)
            self.assert_invalid(self.write_candidate(report), 'duplicate reference')

    def test_approval_fluff_and_unused_evidence_link_do_not_satisfy_gates(self):
        report = report_fixture()
        report['evidence'][0]['excerpt'] = 'LGTM! Thanks for the contribution, everything looks great and ready to merge.'
        self.assert_invalid(self.write_candidate(report), 'excerpt')
        text = SKILL.replace('[attributed synthetic evidence](references/evidence.json)',
                             'attributed synthetic evidence') + '\n[unused]: references/evidence.json\n'
        self.assert_invalid(self.write_candidate(skill=text), 'relative link')
        text = SKILL.replace('[attributed synthetic evidence](references/evidence.json)', '[evidence]')
        text += '\n[evidence]: references/evidence.json\n'
        self.assertEqual(self.quality().validate_candidate(self.write_candidate(skill=text), REPOSITORY), [])

    def test_symlinked_parent_directories_are_not_followed(self):
        candidate = self.write_candidate()
        path = self.write_review(candidate)
        link = self.root / 'review-alias'
        link.symlink_to(path.parent, target_is_directory=True)
        self.assertIn('symlink', '\n'.join(self.quality().validate_review(link / path.name, candidate, REPOSITORY)))
        alias = self.root / 'root-alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assert_invalid(alias / 'candidate', 'symlink')

    def test_missing_report_returns_actionable_errors_without_writing(self):
        errors = self.quality().validate_candidate(self.root, 'fixture/scala-library')
        self.assertTrue(errors)
        self.assertIn('report.json', '\n'.join(errors))
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
