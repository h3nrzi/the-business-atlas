"""Disposable contract fixtures. Nothing here is an encyclopedia chapter."""
import copy
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('atlas', Path(__file__).parents[1] / 'atlas.py')
atlas = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(atlas)


class AtlasContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='atlas-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in atlas.REQUIRED:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# TEST FIXTURE ONLY\n')
        self.source = dict(id='src-fixture', title='TEST ONLY', publisher='TEST ONLY',
                           url='https://example.invalid/test-only', published=None,
                           accessed='2000-01-01', geography=['fixture'], locator='fixture',
                           limitations='Synthetic fixture, no factual claims.', rights='Test data only')
        self.manifest = dict(schema_version=1, namespace='isic-rev5', revision='5',
                             source_id='src-fixture', accessed='2000-01-01', audit_date='2000-01-01',
                             source_sha256='0' * 64, expected_counts={'section': 22, 'division': 87, 'group': 258, 'class': 463},
                             repository_import_status='partial', repository_missing='Fixture intentionally empty',
                             rights_status='cleared', audited_source_counts={'section': 22, 'division': 87, 'group': 258, 'class': 463})
        self.save('catalog.json', {'schema_version': 1, 'records': []})
        self.save('sources/registry.json', {'schema_version': 1, 'sources': [self.source]})
        self.save('taxonomy/isic-rev5/manifest.json', self.manifest)
        self.save('taxonomy/isic-rev5/records.json', {'schema_version': 1, 'records': []})
        self.record = dict(id='ba-000001', kind='business', title_fa='آزمونهٔ غیرواقعی',
                           title_en='TEST FIXTURE ONLY', path=None, geography=['fixture'],
                           status='planned', evidence_status='unresearched', activities=[], sources=[],
                           gaps=[], unresolved_decisions=[], last_reviewed=None, next_review_due=None,
                           relations={}, coverage={}, publication=None)

    def save(self, name, value):
        (self.root / name).write_text(json.dumps(value, ensure_ascii=False) + '\n')

    def catalog(self, *records):
        self.save('catalog.json', {'schema_version': 1, 'records': records})

    def errors(self):
        return '\n'.join(atlas.validate(self.root))

    def publish_fixture(self):
        # Four synthetic category rows, not copied UN labels or actual research.
        rows = []
        parent = None
        for level, code in [('section', 'A'), ('division', '01'), ('group', '011'), ('class', '0111')]:
            row = dict(id=f'isic-rev5:{code}', code=code, level=level, parent_id=parent,
                       label_en='SYNTHETIC TEST LABEL', label_fa=None, translation_status='missing')
            rows.append(row)
            parent = row['id']
        self.save('taxonomy/isic-rev5/records.json', {'schema_version': 1, 'records': rows})
        path = 'businesses/ba-000001/index.md'
        chapter = self.root / path
        chapter.parent.mkdir(parents=True)
        chapter.write_text('# TEST ONLY\n[@src-fixture]\n' + '\n'.join(f'<a id="dimension-{d}"></a>' for d in sorted(atlas.DIMENSIONS)))
        (chapter.parent / 'review.md').write_text('# TEST REVIEW — no actual human approval\n')
        self.record.update(path=path, status='published', evidence_status='sufficient',
                           sources=['src-fixture'], last_reviewed='2000-01-01', next_review_due='2099-01-01',
                           activities=[dict(id='isic-rev5:0111', role='primary', rationale='TEST ONLY')],
                           coverage={d: dict(state='complete', reason='Synthetic contract fixture') for d in atlas.DIMENSIONS},
                           publication=dict(approved_by='TEST ONLY', approved_on='2000-01-01',
                                            content_sha256=hashlib.sha256(chapter.read_bytes()).hexdigest(),
                                            review_path='businesses/ba-000001/review.md'))
        self.record['publication']['revision_sha256'] = atlas.revision_digest(self.root, self.record)
        self.catalog(self.record)
        return chapter

    def test_empty_catalog_is_valid_without_claiming_global_coverage(self):
        self.assertEqual(self.errors(), '')
        result = atlas.generated(self.root)['PROGRESS.md']
        self.assertIn('0/830', result)
        self.assertIn('مخرج صفر', result)

    def test_duplicate_identity_rejected(self):
        self.catalog(self.record, copy.deepcopy(self.record))
        self.assertIn('duplicate business/canonical id', self.errors())

    def test_unknown_state_and_unregistered_source_rejected(self):
        self.record.update(status='done', sources=['src-missing'])
        self.catalog(self.record)
        self.assertIn('invalid editorial state', self.errors())
        self.assertIn('unknown source', self.errors())

    def test_unknown_activity_cannot_be_approved_from_its_shape(self):
        self.record['activities'] = [dict(id='isic-rev5:0111', role='primary', rationale='Test')]
        self.catalog(self.record)
        self.assertIn('unknown/unavailable ISIC class', self.errors())

    def test_wrong_kind_relationship_and_unknown_destination_rejected(self):
        other = copy.deepcopy(self.record)
        other.update(id='pr-000001', kind='process')
        self.record['relations'] = {'industries': ['pr-000001'], 'business_models': ['bm-999999']}
        self.catalog(self.record, other)
        self.assertIn('wrong-kind relation', self.errors())

    def test_redirect_cycle_rejected(self):
        other = copy.deepcopy(self.record)
        other.update(id='ba-000002', redirect_to='ba-000001')
        self.record['redirect_to'] = 'ba-000002'
        self.catalog(self.record, other)
        self.assertIn('invalid/chained redirect', self.errors())

    def test_software_analysis_requires_business_relationship(self):
        self.record.update(id='ss-000001', kind='software-system')
        self.catalog(self.record)
        self.assertIn('must link to business archetype', self.errors())

    def test_broken_relative_link_and_anchor_rejected(self):
        (self.root / 'README.md').write_text('[bad](missing.md)\n[anchor](GLOSSARY.md#missing)\n')
        errors = self.errors()
        self.assertIn('broken/outside internal link', errors)
        self.assertIn('missing anchor', errors)

    def test_orphan_chapter_rejected(self):
        path = self.root / 'businesses' / 'ba-000001' / 'index.md'
        path.parent.mkdir(parents=True)
        path.write_text('# TEST ONLY\n')
        self.assertIn('canonical chapter not registered', self.errors())

    def test_published_structure_pass_does_not_authenticate_human_approval(self):
        self.publish_fixture()
        self.assertEqual(self.errors(), '')

    def test_modified_published_text_requires_review(self):
        chapter = self.publish_fixture()
        chapter.write_text(chapter.read_text() + '\nChanged test text\n')
        self.assertIn('approval hash differs', self.errors())

    def test_companion_sources_must_be_declared_by_owning_record(self):
        chapter = self.publish_fixture()
        extra = dict(self.source, id='src-evidence-only')
        self.save('sources/registry.json', {'schema_version': 1, 'sources': [self.source, extra]})
        (chapter.parent / 'evidence.md').write_text('# TEST EVIDENCE\n[@src-evidence-only]\n')
        self.assertIn('undeclared/unknown citation src-evidence-only', self.errors())
        self.record['sources'].append('src-evidence-only')
        # Synthetic reapproval after changing the material evidence, not human authorization.
        self.record['publication']['revision_sha256'] = atlas.revision_digest(self.root, self.record)
        self.catalog(self.record)
        self.assertEqual(self.errors(), '')

    def test_review_document_sources_must_be_declared(self):
        self.publish_fixture()
        extra = dict(self.source, id='src-review-only')
        self.save('sources/registry.json', {'schema_version': 1, 'sources': [self.source, extra]})
        path = self.root / self.record['publication']['review_path']
        path.write_text('# TEST REVIEW\n[@src-review-only]\n')
        self.assertIn('undeclared/unknown citation src-review-only', self.errors())

    def test_publication_requires_coverage_sources_dates_and_review_record(self):
        self.publish_fixture()
        self.record.update(coverage={}, sources=[], publication=None, last_reviewed=None)
        self.catalog(self.record)
        errors = self.errors()
        for expected in ('all 26 coverage', 'sufficient evidence and sources', 'review dates required', 'approval record required'):
            self.assertIn(expected, errors)

    def test_missing_dimension_and_partial_coverage_rejected(self):
        chapter = self.publish_fixture()
        chapter.write_text(chapter.read_text().replace('<a id="dimension-12"></a>', ''))
        self.record['publication']['content_sha256'] = atlas.digest(chapter.read_bytes())
        self.record['coverage']['16']['state'] = 'partial'
        self.catalog(self.record)
        self.assertIn('missing published dimension-12', self.errors())
        self.assertIn('partial coverage 16 prevents publication', self.errors())

    def test_core_dimension_cannot_be_declared_irrelevant(self):
        self.publish_fixture()
        self.record['coverage']['01']['state'] = 'not-applicable'
        self.catalog(self.record)
        self.assertIn('core dimension 01 cannot be not-applicable', self.errors())

    def test_unresolved_decision_prevents_publication(self):
        self.publish_fixture()
        self.record['unresolved_decisions'] = ['A test decision is open']
        self.catalog(self.record)
        self.assertIn('unresolved gaps/decisions', self.errors())

    def test_taxonomy_parent_translation_and_rights_checked(self):
        self.publish_fixture()
        data = json.loads((self.root / 'taxonomy/isic-rev5/records.json').read_text())
        data['records'][-1].update(parent_id='isic-rev5:999', label_fa='آزمون', translation_status='verified')
        self.save('taxonomy/isic-rev5/records.json', data)
        self.manifest['rights_status'] = 'redistribution-not-cleared'
        self.save('taxonomy/isic-rev5/manifest.json', self.manifest)
        errors = self.errors()
        for expected in ('wrong parent', 'translation provenance', 'translation verification', 'rights are not cleared'):
            self.assertIn(expected, errors)

    def test_false_complete_import_rejected(self):
        self.manifest['repository_import_status'] = 'complete'
        self.save('taxonomy/isic-rev5/manifest.json', self.manifest)
        self.assertIn('incomplete counts', self.errors())

    def test_official_csv_auditor_preserves_zeroes_and_nbsp_and_rejects_changed_snapshot(self):
        raw = b'ISIC Rev 5 Code,ISIC Rev 5 Title\r\nA,TEST\r\n01,TEST\r\n011,TEST\r\n0111,TEST\xa0LABEL\r\n'
        path = self.root / 'fixture.csv'
        path.write_bytes(raw)
        manifest = dict(source_sha256=atlas.digest(raw), source_bytes=len(raw), source_encoding='cp1252',
                        expected_counts=dict(section=1, division=1, group=1, **{'class': 1}))
        rows = atlas.audit_isic(path, manifest)
        self.assertEqual(rows[1]['code'], '01')
        self.assertEqual(rows[-1]['parent_id'], 'isic-rev5:011')
        self.assertEqual(rows[-1]['label_en'], 'TEST\u00a0LABEL')
        path.write_bytes(raw + b'\n')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            atlas.audit_isic(path, manifest)

    def test_malformed_record_fields_report_failure(self):
        self.record.update(path=['not', 'a', 'path'], activities='not an array', relations=[], coverage=[], sources={})
        self.catalog(self.record)
        self.assertIn('path missing/unsafe', self.errors())
        self.assertIn('activities must be an array', self.errors())

    def test_generation_is_deterministic_and_uses_only_catalog(self):
        first = atlas.generated(self.root)
        self.assertEqual(first, atlas.generated(self.root))
        for body in first.values():
            self.assertTrue(body.endswith('\n'))
            self.assertFalse(body.endswith('\n\n'))
        self.catalog(self.record)
        self.assertIn('ba-000001', atlas.generated(self.root)['CONTENTS.md'])
        self.assertIn('**1**', atlas.generated(self.root)['PROGRESS.md'])

    def test_legacy_text_only_approval_requires_new_review(self):
        self.publish_fixture()
        del self.record['publication']['revision_sha256']
        self.catalog(self.record)
        self.assertIn('approval revision differs', self.errors())

    def test_scope_exclusion_changes_invalidate_approval(self):
        self.publish_fixture()
        self.record['coverage']['02'] = dict(state='not-applicable', reason='Synthetic scope exclusion')
        self.catalog(self.record)
        self.assertIn('approval revision differs', self.errors())
        self.record['publication']['revision_sha256'] = atlas.revision_digest(self.root, self.record)
        self.catalog(self.record)
        self.assertEqual(self.errors(), '')
        self.record['coverage']['02']['reason'] = 'A different scope exclusion'
        self.catalog(self.record)
        self.assertIn('approval revision differs', self.errors())

    def test_revision_hash_cli_uses_catalog_id_and_does_not_grant_approval(self):
        self.publish_fixture()
        self.record.update(status='review', publication=None)
        self.catalog(self.record)
        before = (self.root / 'catalog.json').read_bytes()
        output = io.StringIO()
        with patch.object(atlas, 'ROOT', self.root), redirect_stdout(output):
            self.assertEqual(atlas.main(['revision-hash', self.record['id']]), 0)
        self.assertEqual(output.getvalue().strip(), atlas.revision_digest(self.root, self.record))
        self.assertEqual((self.root / 'catalog.json').read_bytes(), before)

    def test_material_metadata_changes_invalidate_approval(self):
        self.publish_fixture()
        approved = copy.deepcopy(self.record)
        changes = {
            'geography': ['another fixture region'],
            'activities': [dict(id='isic-rev5:0111', role='primary', rationale='Different scope')],
            'sources': [],
            'relations': {'processes': ['pr-000001']},
            'redirect_to': 'ba-000002',
        }
        process = dict(copy.deepcopy(self.record), id='pr-000001', kind='process', path=None,
                       status='planned', publication=None, coverage={})
        other = dict(copy.deepcopy(self.record), id='ba-000002', path=None,
                     status='planned', publication=None, coverage={})
        for key, value in changes.items():
            with self.subTest(field=key):
                self.record = dict(copy.deepcopy(approved), **{key: value})
                self.catalog(self.record, process, other)
                self.assertIn('approval revision differs', self.errors())

    def test_material_source_definition_changes_invalidate_approval(self):
        self.publish_fixture()
        for key in ('url', 'locator', 'limitations', 'rights', 'published'):
            with self.subTest(field=key):
                value = '2001' if key == 'published' else self.source[key] + '/changed'
                self.save('sources/registry.json', {'schema_version': 1, 'sources': [dict(self.source, **{key: value})]})
                self.assertIn('approval revision differs', self.errors())

    def test_evidence_and_scope_decisions_add_edit_remove_invalidate_approval(self):
        chapter = self.publish_fixture()
        for name in ('evidence.md', 'decisions.md'):
            with self.subTest(companion=name):
                path = chapter.parent / name
                path.write_text('# SYNTHETIC MATERIAL\n')
                self.assertIn('approval revision differs', self.errors())
                self.record['publication']['revision_sha256'] = atlas.revision_digest(self.root, self.record)
                self.catalog(self.record)
                self.assertEqual(self.errors(), '')
                path.write_text('# CHANGED SYNTHETIC MATERIAL\n')
                self.assertIn('approval revision differs', self.errors())
                path.unlink()
                self.assertIn('approval revision differs', self.errors())
                self.record['publication']['revision_sha256'] = atlas.revision_digest(self.root, self.record)
                self.catalog(self.record)

    def test_review_preserves_old_approval_until_synthetic_reapproval(self):
        self.publish_fixture()
        self.record['geography'] = ['changed scope']
        for state in ('review', 'needs-update'):
            self.record['status'] = state
            self.catalog(self.record)
            self.assertEqual(self.errors(), '')
        self.record['status'] = 'published'
        self.catalog(self.record)
        self.assertIn('approval revision differs', self.errors())
        self.record['publication']['revision_sha256'] = atlas.revision_digest(self.root, self.record)
        self.catalog(self.record)
        self.assertEqual(self.errors(), '')

    def test_administrative_and_display_changes_do_not_invalidate_approval(self):
        chapter = self.publish_fixture()
        self.record.update(title_fa='عنوان نمایشی', title_en='Display title', aliases=['Display alias'],
                           last_reviewed='2001-01-01', next_review_due='2098-01-01')
        self.save('sources/registry.json', {'schema_version': 1,
                  'sources': [dict(self.source, accessed='2001-01-01'), dict(self.source, id='src-unrelated')]})
        (chapter.parent / 'review.md').write_text('# TEST REVIEW updated sign-off notes\n')
        (chapter.parent / 'handoff.md').write_text('# TEST administrative handoff\n')
        self.catalog(self.record)
        self.assertEqual(self.errors(), '')

    def test_revision_is_independent_of_json_and_set_order(self):
        self.publish_fixture()
        self.record['geography'] = ['fixture-a', 'fixture-b']
        self.record['relations'] = {'related': ['ba-000002', 'ba-000003']}
        first = atlas.revision_digest(self.root, self.record)
        self.record = dict(reversed(list(self.record.items())))
        self.record['geography'].reverse()
        self.record['relations']['related'].reverse()
        self.record['relations']['processes'] = []
        self.save('sources/registry.json', {'schema_version': 1, 'sources': [dict(reversed(list(self.source.items())))]})
        self.assertEqual(first, atlas.revision_digest(self.root, self.record))


class RestrictedSourceTracking(unittest.TestCase):
    def test_current_repository_index_excludes_restricted_source(self):
        self.assertEqual(atlas.restricted_source_errors(atlas.ROOT), [])

    def test_narrow_ignore_and_force_added_snapshot_detection_preserve_local_copy(self):
        with tempfile.TemporaryDirectory(prefix='atlas-index-test-') as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(['git', '-C', str(root), *args], check=True,
                                      capture_output=True, text=True).stdout
            git('init', '--quiet')
            (root / '.gitignore').write_bytes((atlas.ROOT / '.gitignore').read_bytes())
            raw = root / atlas.RESTRICTED_SOURCE
            raw.parent.mkdir(parents=True)
            raw.write_bytes(b'SYNTHETIC TEST DATA ONLY\n')
            tracker = root / '.scratch' / 'test' / 'spec.md'
            tracker.parent.mkdir()
            tracker.write_text('# TEST tracker\n')
            self.assertEqual(git('check-ignore', atlas.RESTRICTED_SOURCE).strip(), atlas.RESTRICTED_SOURCE)
            self.assertIn('.scratch/test/spec.md', git('ls-files', '--others', '--exclude-standard'))
            self.assertEqual(atlas.restricted_source_errors(root), [])
            git('add', '-f', '--', atlas.RESTRICTED_SOURCE)
            self.assertIn('restricted source is tracked', '\n'.join(atlas.validate(root)))
            git('rm', '--cached', '--', atlas.RESTRICTED_SOURCE)
            self.assertEqual(atlas.restricted_source_errors(root), [])
            self.assertEqual(raw.read_bytes(), b'SYNTHETIC TEST DATA ONLY\n')


if __name__ == '__main__':
    unittest.main()
