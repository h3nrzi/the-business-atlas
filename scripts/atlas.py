#!/usr/bin/env python3
"""Portable structural checks and navigation for a documentation-first atlas.

Only the standard library is needed. Editorial quality and approval authority
remain human judgments; passing this module cannot establish either.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
KINDS = {
    'business': ('ba', 'businesses'),
    'industry': ('in', 'industries'),
    'business-model': ('bm', 'business-models'),
    'revenue-model': ('rm', 'business-models'),
    'process': ('pr', 'processes'),
    'software-system': ('ss', 'software-systems'),
    'case-study': ('cs', 'businesses'),
}
STATES = ('planned', 'discovery', 'research', 'drafting', 'review', 'published', 'needs-update')
EVIDENCE = ('unresearched', 'partial', 'sufficient', 'conflicted', 'stale')
RELATIONS = {
    'industries': 'industry', 'business_models': 'business-model',
    'revenue_models': 'revenue-model', 'processes': 'process',
    'software_systems': 'software-system', 'case_studies': 'case-study',
    'businesses': 'business',
}
LEVELS = {'section': r'[A-V]', 'division': r'\d{2}', 'group': r'\d{3}', 'class': r'\d{4}'}
DIMENSIONS = {f'{i:02}' for i in range(1, 27)}
ESSENTIAL_DIMENSIONS = DIMENSIONS - {'02', '06', '21', '23', '24'}
REQUIRED = (
    'README.md', 'AGENTS.md', 'CONTRIBUTING.md', 'GLOSSARY.md', 'catalog.json',
    'CONTENTS.md', 'PROGRESS.md', 'docs/charter.md', 'docs/architecture.md',
    'docs/research.md', 'docs/editorial.md', 'docs/learning.md',
    'docs/workflows/wayfinder.md', 'docs/agents/issue-tracker.md',
    'docs/agents/triage-labels.md', 'docs/agents/domain.md',
    'templates/business-chapter.md', 'templates/software-analysis.md',
    'templates/catalog-record.json', 'templates/evidence.md', 'templates/review.md',
    'templates/handoff.md', 'templates/learning-record.md', 'templates/README.md',
    'businesses/README.md', 'industries/README.md', 'business-models/README.md',
    'processes/README.md', 'software-systems/README.md', 'sources/README.md',
    'taxonomy/README.md', 'sources/registry.json', 'sources/isic-rev5-research.md',
    'taxonomy/isic-rev5/manifest.json', 'taxonomy/isic-rev5/records.json',
    'taxonomy/isic-rev5/INDEX.md', 'docs/infrastructure-acceptance.md',
    'scripts/README.md', 'skills-lock.json',
)
RECORD_FIELDS = {
    'id', 'kind', 'title_fa', 'title_en', 'path', 'geography', 'status',
    'evidence_status', 'activities', 'sources', 'gaps', 'unresolved_decisions',
    'last_reviewed', 'next_review_due', 'relations', 'coverage', 'publication',
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_value(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def iso_day(value) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def strings(value, nonempty=False) -> bool:
    return (isinstance(value, list) and (bool(value) or not nonempty)
            and all(text_value(x) for x in value) and len(value) == len(set(value)))


def read_json(root: Path, name: str, array: str | None = None):
    value = json.loads((root / name).read_text(encoding='utf-8'))
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise ValueError(f'{name}: expected object with schema_version 1')
    if array is not None and (not isinstance(value.get(array), list)
                              or not all(isinstance(x, dict) for x in value[array])):
        raise ValueError(f'{name}: {array} must be an array of objects')
    return value if array is None else value[array]


def audit_isic(path: Path, manifest: dict) -> list[dict]:
    """Audit ONLY the pinned UN CSV. Preserve every original decoded label."""
    raw = path.read_bytes()
    if digest(raw) != manifest['source_sha256'] or len(raw) != manifest['source_bytes']:
        raise ValueError('ISIC source checksum/size differs from pinned snapshot; review a new version explicitly')
    reader = csv.DictReader(io.StringIO(raw.decode(manifest['source_encoding'])))
    if reader.fieldnames != ['ISIC Rev 5 Code', 'ISIC Rev 5 Title']:
        raise ValueError('unexpected ISIC CSV headers')
    records, seen = [], set()
    current = {}
    for row in reader:
        code, label = row[reader.fieldnames[0]], row[reader.fieldnames[1]]
        level = next((k for k, pattern in LEVELS.items() if re.fullmatch(pattern, code)), None)
        if not level or not label.strip() or code in seen:
            raise ValueError(f'invalid, duplicate or blank ISIC row: code {code!r}')
        seen.add(code)
        if level == 'section':
            parent = None
            current = {'section': code}
        else:
            parent_level = {'division': 'section', 'group': 'division', 'class': 'group'}[level]
            parent = current.get(parent_level)
            if parent is None or (level in ('group', 'class') and not code.startswith(parent)):
                raise ValueError(f'ISIC parent/order mismatch for {code}')
            if level == 'division':
                current = {'section': current['section'], 'division': code}
            elif level == 'group':
                current = {k: v for k, v in current.items() if k != 'class'}
                current['group'] = code
        records.append(dict(id=f'isic-rev5:{code}', code=code, level=level,
                            parent_id=f'isic-rev5:{parent}' if parent else None,
                            label_en=label, label_fa=None, translation_status='missing'))
    counts = dict(Counter(x['level'] for x in records))
    if counts != manifest['expected_counts']:
        raise ValueError(f'ISIC count mismatch: {counts}')
    return records


def safe_path(root: Path, value, suffix='.md') -> Path | None:
    if not text_value(value) or Path(value).is_absolute() or '..' in Path(value).parts:
        return None
    target = (root / value).resolve()
    if not target.is_relative_to(root.resolve()) or target.suffix != suffix:
        return None
    return target


def strip_code(text: str) -> str:
    text = re.sub(r'^\s*```[^\n]*\n.*?^\s*```\s*$', '', text, flags=re.M | re.S)
    return re.sub(r'`[^`\n]*`', '', text)


def anchors(text: str) -> set[str]:
    found = set(re.findall(r'<a\s+id=[\"\']([^\"\']+)[\"\']', text))
    counts = Counter()
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.M):
        heading = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', heading).lower()
        slug = ''.join(c for c in heading if c.isalnum() or c in '_- ')
        slug = slug.replace(' ', '-')
        n = counts[slug]
        counts[slug] += 1
        found.add(slug + (f'-{n}' if n else ''))
    return found


def project_markdown(root: Path):
    for path in sorted(root.rglob('*.md')):
        if not any(part.startswith('.') for part in path.relative_to(root).parts):
            yield path


def check_links(root: Path) -> list[str]:
    errors = []
    for path in project_markdown(root):
        body = strip_code(path.read_text(encoding='utf-8'))
        # This project uses inline links, with no whitespace in local targets.
        for raw in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', body):
            raw = raw.strip().split(' "', 1)[0].strip('<>')
            url = urlsplit(raw)
            if url.scheme or url.netloc:
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            label = f'{path.relative_to(root)}: {raw}'
            if not target.is_relative_to(root.resolve()) or not target.exists():
                errors.append(f'broken/outside internal link: {label}')
            elif url.fragment and target.suffix == '.md':
                if unquote(url.fragment) not in anchors(strip_code(target.read_text(encoding='utf-8'))):
                    errors.append(f'missing anchor: {label}')
    return errors


def validate(root: Path, local_taxonomy: Path | None = None) -> list[str]:
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    for name in REQUIRED:
        need((root / name).is_file(), f'missing required file: {name}')
    try:
        catalog = read_json(root, 'catalog.json', 'records')
        sources = read_json(root, 'sources/registry.json', 'sources')
        manifest = read_json(root, 'taxonomy/isic-rev5/manifest.json')
        taxonomy = read_json(root, 'taxonomy/isic-rev5/records.json', 'records')
    except (OSError, ValueError, KeyError) as exc:
        return errors + [str(exc)]
    source_ids = set()
    for source in sources:
        sid = source.get('id')
        if not isinstance(sid, str):
            errors.append('source must have a string id')
            continue
        need(bool(re.fullmatch(r'src-[a-z0-9-]+', sid)) and sid not in source_ids,
             f'duplicate/invalid source id: {sid}')
        source_ids.add(sid)
        for key in ('title', 'publisher', 'url', 'locator', 'limitations', 'rights'):
            need(text_value(source.get(key)), f'{sid}: missing {key}')
        need(isinstance(source.get('url'), str) and source['url'].startswith(('https://', 'http://')),
             f'{sid}: source URL required')
        need(iso_day(source.get('accessed')), f'{sid}: invalid access date')
        published = source.get('published')
        need(published is None or (isinstance(published, str) and
             (iso_day(published) or bool(re.fullmatch(r'\d{4}', published)))), f'{sid}: invalid publication date')
        need(strings(source.get('geography'), True), f'{sid}: geography required')
    need(manifest.get('namespace') == 'isic-rev5' and manifest.get('revision') == '5', 'taxonomy revision/namespace must be explicit')
    need(manifest.get('expected_counts') == {'section': 22, 'division': 87, 'group': 258, 'class': 463}, 'unexpected authoritative ISIC counts')
    need(manifest.get('source_id') in source_ids, 'taxonomy source is not registered')
    need(iso_day(manifest.get('accessed')) and iso_day(manifest.get('audit_date')), 'taxonomy dates required')
    need(bool(re.fullmatch(r'[a-f0-9]{64}', str(manifest.get('source_sha256')))), 'taxonomy checksum required')
    need(manifest.get('repository_import_status') in ('blocked-rights', 'partial', 'complete'), 'unknown taxonomy completeness status')
    need(not taxonomy or manifest.get('rights_status') == 'cleared', 'taxonomy redistribution rights are not cleared')
    need(bool(taxonomy) or text_value(manifest.get('repository_missing')), 'missing taxonomy portions must be explicit')
    tax_ids = {}
    for item in taxonomy:
        ident, code, level = item.get('id'), item.get('code'), item.get('level')
        if not all(isinstance(x, str) for x in (ident, code, level)):
            errors.append('taxonomy id, code and level must be strings')
            continue
        need(ident == f'isic-rev5:{code}' and ident not in tax_ids, f'invalid/duplicate taxonomy identity: {ident}')
        tax_ids[ident] = item
        need(level in LEVELS and bool(re.fullmatch(LEVELS.get(level, r'(?!)'), code)), f'{ident}: invalid level/code')
        need(text_value(item.get('label_en')), f'{ident}: English label required')
        ts, fa = item.get('translation_status'), item.get('label_fa')
        need(ts in ('missing', 'provisional', 'verified'), f'{ident}: invalid translation status')
        need((ts == 'missing' and fa is None) or (ts != 'missing' and text_value(fa)), f'{ident}: inconsistent Persian translation')
        if ts in ('provisional', 'verified'):
            note = item.get('translation', {})
            need(isinstance(note, dict) and text_value(note.get('by')) and iso_day(note.get('date')), f'{ident}: translation provenance required')
            if ts == 'verified':
                need(isinstance(note, dict) and text_value(note.get('reviewed_by')) and text_value(note.get('reference')), f'{ident}: translation verification required')
    for ident, item in tax_ids.items():
        parent_id = item.get('parent_id')
        level = item.get('level')
        parent = tax_ids.get(parent_id) if isinstance(parent_id, str) else None
        if level == 'section':
            need(item.get('parent_id') is None, f'{ident}: section cannot have a parent')
        else:
            previous = {'division': 'section', 'group': 'division', 'class': 'group'}.get(level)
            need(parent is not None and parent.get('level') == previous, f'{ident}: missing/wrong parent')
            if parent and level in ('group', 'class'):
                need(item['code'].startswith(parent['code']), f'{ident}: parent prefix mismatch')
    counts = Counter(x.get('level') for x in taxonomy)
    for level, expected in manifest.get('expected_counts', {}).items():
        need(counts[level] <= expected, f'too many imported {level} records')
    if manifest.get('repository_import_status') == 'complete':
        need(dict(counts) == manifest.get('expected_counts'), 'complete taxonomy status has incomplete counts')
    if local_taxonomy:
        try:
            local = {r['id']: r for r in audit_isic(local_taxonomy, manifest)}
            for ident, record in tax_ids.items():
                need(ident in local and all(record.get(k) == local[ident][k] for k in ('code', 'level', 'parent_id', 'label_en')), f'{ident}: differs from official snapshot')
            tax_ids.update(local)
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f'local taxonomy audit: {exc}')
    by_id, paths = {}, set()
    for record in catalog:
        ident, kind = record.get('id'), record.get('kind')
        if not isinstance(ident, str) or not isinstance(kind, str):
            errors.append('catalog id and kind must be strings')
            continue
        need(RECORD_FIELDS <= record.keys(), f'{ident}: missing fields {sorted(RECORD_FIELDS - record.keys())}')
        need(not (record.keys() - RECORD_FIELDS - {'aliases', 'redirect_to'}), f'{ident}: unknown metadata fields')
        need(kind in KINDS and bool(re.fullmatch(KINDS.get(kind, ('INVALID',))[0] + r'-\d{6}', ident)), f'{ident}: invalid kind/id')
        need(ident not in by_id, f'duplicate business/canonical id: {ident}')
        by_id[ident] = record
        for key in ('title_fa', 'title_en'):
            need(text_value(record.get(key)) and '{{' not in str(record.get(key)), f'{ident}: real {key} required')
        for key in ('geography', 'sources', 'gaps', 'unresolved_decisions'):
            need(strings(record.get(key), key == 'geography'), f'{ident}: {key} must be a unique string array')
        if 'aliases' in record:
            need(strings(record['aliases']), f'{ident}: aliases must be a unique string array')
        state = record.get('status')
        need(state in STATES, f'{ident}: invalid editorial state {state}')
        need(record.get('evidence_status') in EVIDENCE, f'{ident}: invalid evidence state')
        for key in ('last_reviewed', 'next_review_due'):
            need(record.get(key) is None or iso_day(record[key]), f'{ident}: invalid {key}')
        raw_path = record.get('path')
        path = safe_path(root, raw_path) if raw_path is not None else None
        if raw_path is not None:
            need(path is not None and path.is_file(), f'{ident}: chapter path missing/unsafe')
            if isinstance(raw_path, str):
                need(raw_path not in paths, f'{ident}: duplicate canonical path')
                paths.add(raw_path)
            prefix = KINDS.get(kind, ('', 'INVALID'))[1] + '/'
            need(isinstance(raw_path, str) and raw_path.startswith(prefix), f'{ident}: path in wrong content domain')
            if kind == 'business':
                need(raw_path == f'businesses/{ident}/index.md', f'{ident}: business path must use stable ID')
        if state in ('drafting', 'review', 'published', 'needs-update'):
            need(path is not None and path.is_file(), f'{ident}: {state} requires a chapter')
        activities = record.get('activities')
        need(isinstance(activities, list), f'{ident}: activities must be an array')
        seen_activities = set()
        for activity in activities if isinstance(activities, list) else []:
            if not isinstance(activity, dict):
                errors.append(f'{ident}: activity must be an object')
                continue
            aid = activity.get('id')
            need(isinstance(aid, str) and aid not in seen_activities, f'{ident}: duplicate/invalid activity')
            if isinstance(aid, str):
                seen_activities.add(aid)
                need(aid in tax_ids and tax_ids[aid].get('level') == 'class', f'{ident}: unknown/unavailable ISIC class {aid}; provide audited local source if not distributed')
            need(activity.get('role') in ('primary', 'secondary') and text_value(activity.get('rationale')), f'{ident}: activity role/rationale required')
        declared = record.get('sources') if strings(record.get('sources')) else []
        for sid in declared:
            need(sid in source_ids, f'{ident}: unknown source {sid}')
        if path and path.is_file():
            body = path.read_text(encoding='utf-8')
            for sid in re.findall(r'\[@(src-[a-z0-9-]+)\]', strip_code(body)):
                need(sid in source_ids and sid in declared, f'{ident}: undeclared/unknown citation {sid}')
        coverage = record.get('coverage')
        need(isinstance(coverage, dict), f'{ident}: coverage must be an object')
        if isinstance(coverage, dict):
            need(not (coverage.keys() - DIMENSIONS), f'{ident}: unknown coverage dimension')
            for dim, value in coverage.items():
                need(isinstance(value, dict) and value.get('state') in ('complete', 'partial', 'not-applicable')
                     and text_value(value.get('reason')), f'{ident}: invalid coverage {dim}')
                if isinstance(value, dict) and dim in ESSENTIAL_DIMENSIONS:
                    need(value.get('state') != 'not-applicable', f'{ident}: core dimension {dim} cannot be not-applicable')
            if kind == 'business' and state in ('review', 'published', 'needs-update'):
                need(coverage.keys() == DIMENSIONS, f'{ident}: all 26 coverage decisions required')
            if kind != 'business':
                need(not coverage, f'{ident}: 26-dimension coverage belongs to business chapters')
        publication = record.get('publication')
        need(publication is None or isinstance(publication, dict), f'{ident}: publication must be null or an object')
        if state == 'needs-update':
            need(isinstance(publication, dict), f'{ident}: needs-update requires prior publication')
        if state == 'published':
            need(record.get('evidence_status') == 'sufficient' and bool(declared), f'{ident}: publication needs sufficient evidence and sources')
            need(not record.get('gaps') and not record.get('unresolved_decisions'), f'{ident}: publication has unresolved gaps/decisions')
            need(iso_day(record.get('last_reviewed')) and iso_day(record.get('next_review_due')), f'{ident}: publication review dates required')
            if iso_day(record.get('last_reviewed')) and iso_day(record.get('next_review_due')):
                need(record['next_review_due'] > record['last_reviewed'], f'{ident}: next review must follow last review')
            if kind == 'business':
                need(bool(activities) and any(a.get('role') == 'primary' for a in activities if isinstance(a, dict)), f'{ident}: publication needs a primary activity mapping')
                for dim, value in (coverage.items() if isinstance(coverage, dict) else []):
                    if isinstance(value, dict):
                        need(value.get('state') in ('complete', 'not-applicable'), f'{ident}: partial coverage {dim} prevents publication')
                        if value.get('state') == 'complete' and path and path.is_file():
                            need(f'dimension-{dim}' in anchors(path.read_text(encoding='utf-8')), f'{ident}: missing published dimension-{dim}')
            need(isinstance(publication, dict), f'{ident}: human publication approval record required')
            if isinstance(publication, dict):
                review = safe_path(root, publication.get('review_path'))
                need(text_value(publication.get('approved_by')) and iso_day(publication.get('approved_on')), f'{ident}: approval identity/date required')
                if iso_day(publication.get('approved_on')):
                    need(publication['approved_on'] <= date.today().isoformat(), f'{ident}: approval date is in the future')
                need(review is not None and review.is_file(), f'{ident}: approval review document missing')
                if path and path.is_file():
                    need(publication.get('content_sha256') == digest(path.read_bytes()), f'{ident}: approval hash differs; return to review')
                    need(bool(re.search(r'\[@src-[a-z0-9-]+\]', strip_code(path.read_text(encoding='utf-8')))), f'{ident}: published chapter needs inline source references')
    for ident, record in by_id.items():
        relations = record.get('relations')
        need(isinstance(relations, dict), f'{ident}: relations must be an object')
        for relation, targets in relations.items() if isinstance(relations, dict) else []:
            expected = record.get('kind') if relation == 'related' else RELATIONS.get(relation)
            need(expected is not None and strings(targets), f'{ident}: invalid relation {relation}')
            for target in targets if strings(targets) else []:
                need(target != ident and target in by_id and by_id[target].get('kind') == expected, f'{ident}: unknown/wrong-kind relation {relation} -> {target}')
        if record.get('kind') == 'software-system':
            need(isinstance(relations, dict) and bool(relations.get('businesses')), f'{ident}: software analysis must link to business archetype')
        redirect = record.get('redirect_to')
        if redirect is not None:
            dest = by_id.get(redirect) if isinstance(redirect, str) else None
            need(dest is not None and redirect != ident and dest.get('kind') == record.get('kind') and not dest.get('redirect_to'), f'{ident}: invalid/chained redirect')
    candidates = list((root / 'businesses').glob('*/index.md'))
    for folder in {folder for _, folder in KINDS.values()}:
        candidates.extend(p for p in (root / folder).glob('*.md') if p.name != 'README.md')
    for path in candidates:
        need(path.relative_to(root).as_posix() in paths, f'canonical chapter not registered: {path.relative_to(root)}')
    # Citations can occur in evidence, decisions, and other prose, not just main chapters.
    for path in project_markdown(root):
        for sid in re.findall(r'\[@(src-[a-z0-9-]+)\]', strip_code(path.read_text(encoding='utf-8'))):
            need(sid in source_ids, f'{path.relative_to(root)}: unknown citation {sid}')
    errors.extend(check_links(root))
    return errors


def cell(value) -> str:
    return str(value).replace('|', '\\|').replace('\n', ' ')


def generated(root: Path) -> dict[str, str]:
    records = read_json(root, 'catalog.json', 'records')
    manifest = read_json(root, 'taxonomy/isic-rev5/manifest.json')
    taxonomy = read_json(root, 'taxonomy/isic-rev5/records.json', 'records')
    active = [r for r in records if not r.get('redirect_to')]
    businesses = [r for r in active if r['kind'] == 'business']
    header = '<!-- Generated by scripts/atlas.py generate; edit canonical metadata instead. -->\n\n'
    contents = header + '# فهرست کتاب — Table of contents\n\n'
    contents += ('مسیر مطالعه: [واژگان](GLOSSARY.md) ← [صنایع](industries/README.md) ← '
                 '[گونه‌ها](businesses/README.md) ← [مدل‌ها](business-models/README.md) و '
                 '[فرایندها](processes/README.md) ← [تحلیل نرم‌افزار](software-systems/README.md).\n\n'
                 'ترتیب پژوهش مستقل از این مسیر و تابع اولویت انسانی است. '
                 '[طبقه‌بندی](taxonomy/isic-rev5/INDEX.md) و [پیشرفت](PROGRESS.md) مسیرهای مکمل‌اند.\n\n')
    for kind in KINDS:
        group = sorted((r for r in active if r['kind'] == kind), key=lambda r: r['id'])
        contents += f'## {kind}\n\n'
        if not group:
            contents += 'هنوز رکوردی ثبت نشده است.\n\n'
        else:
            contents += '| شناسه | عنوان | English | وضعیت |\n| --- | --- | --- | --- |\n'
            for r in group:
                title = f"[{cell(r['title_fa'])}]({r['path']})" if r['path'] else cell(r['title_fa'])
                contents += f"| {r['id']} | {title} | {cell(r['title_en'])} | {r['status']} |\n"
            contents += '\n'
    redirects = [r for r in records if r.get('redirect_to')]
    if redirects:
        contents += '## هویت‌های ادغام‌شده\n\n'
        contents += '\n'.join(f"- {r['id']} → {r['redirect_to']}" for r in redirects) + '\n'
    counts = Counter(r['level'] for r in taxonomy)
    progress = header + '# پیشرفت و پوشش — Progress\n\n'
    progress += '## پوشش طبقه‌بندی، مستقل از فصل‌ها\n\n'
    progress += '| سطح | رکورد قابل توزیع در مخزن | شمار رسمی | audit فایل رسمی |\n| --- | --- | --- | --- |\n'
    for level, expected in manifest['expected_counts'].items():
        progress += f"| {level} | {counts[level]} | {expected} | {manifest['audited_source_counts'][level]} |\n"
    progress += (f"\nوضعیت واردسازی: **{manifest['repository_import_status']}**. "
                 f"{len(taxonomy)}/{sum(manifest['expected_counts'].values())} رکورد توزیع‌شده. "
                 f"audit در {manifest['audit_date']}؛ این audit واردسازی عمومی نیست. "
                 '[محدودیت‌ها و منشأ](taxonomy/README.md).\n\n')
    published = sum(r['status'] == 'published' for r in businesses)
    progress += ('## پوشش تحریریهٔ فهرست شناخته‌شده\n\n'
                 f'گونه‌های شناسایی‌شده: **{len(businesses)}**؛ فصل منتشرشده: **{published}**. '
                 + (f'نسبت انتشار در فهرست فعلی: {published}/{len(businesses)}. ' if businesses else 'نسبت انتشار: تعریف‌نشده، چون مخرج صفر است. ')
                 + 'جامعیت جهانی گونه‌ها نامعلوم و باز است.\n\n'
                 '| وضعیت | تعداد گونه |\n| --- | --- |\n')
    states = Counter(r['status'] for r in businesses)
    progress += ''.join(f'| {state} | {states[state]} |\n' for state in STATES)
    industries = [r for r in active if r['kind'] == 'industry']
    progress += f'\nصنایع شناخته‌شده: {len(industries)}؛ صنایع منتشرشده: {sum(r["status"] == "published" for r in industries)}.\n\n'
    progress += '## موارد نیازمند اقدام\n\n'
    issues = []
    for r in sorted(active, key=lambda x: x['id']):
        reasons = []
        if r['status'] == 'needs-update':
            reasons.append('needs-update')
        if r['evidence_status'] != 'sufficient':
            reasons.append('evidence: ' + r['evidence_status'])
        if r['unresolved_decisions']:
            reasons.append('تصمیم باز: ' + '؛ '.join(r['unresolved_decisions']))
        if r['gaps']:
            reasons.append('شکاف: ' + '؛ '.join(r['gaps']))
        if r['next_review_due'] and r['next_review_due'] <= date.today().isoformat():
            reasons.append('موعد مرور گذشته: ' + r['next_review_due'])
        if reasons:
            issues.append(f"- {r['id']} — {cell(r['title_fa'])}: " + '؛ '.join(reasons))
    progress += '\n'.join(issues) + '\n\n' if issues else 'هنوز فصلی نیست؛ نبود ایراد فصل به معنی کامل‌بودن دانشنامه نیست.\n\n'
    progress += '## پوشش فعالیت با گونه‌های شناخته‌شده\n\n'
    mapped = Counter(a['id'] for r in businesses for a in r['activities'])
    imported_classes = {r['id'] for r in taxonomy if r['level'] == 'class'}
    progress += (f'کلاس‌های دارای نگاشتِ گونهٔ شناخته‌شده: {len(mapped)}؛ '
                 f'کلاس‌های واردشده بدون نگاشت: {len(imported_classes - mapped.keys())}. '
                 'وقتی واردسازی ناقص است، صفرِ این کمبود به معنی نبود شکاف جهانی نیست.\n\n')
    if mapped:
        progress += '| فعالیت | گونه‌های شناخته‌شده |\n| --- | --- |\n'
        progress += ''.join(f'| {code} | {n} |\n' for code, n in sorted(mapped.items())) + '\n'
    progress += '## اقدام پیشنهادی بعدی\n\n'
    if not taxonomy:
        progress += ('- محدودیت بازنشر ISIC را با مجوز اختصاصی/اجازهٔ معتبر روشن کنید؛ '
                     'تا آن زمان برای بررسی کدها از audit محلی استفاده کنید.\n')
    if businesses:
        priority = {'needs-update': 0, 'review': 1, 'research': 2, 'drafting': 3, 'discovery': 4, 'planned': 5, 'published': 6}
        nxt = min(businesses, key=lambda r: (priority[r['status']], r['next_review_due'] or '9999', r['id']))
        progress += f"- پیشنهاد تحریریه با اولویت مرور/اصلاح و سپس شناسه: {nxt['id']} — {cell(nxt['title_fa'])}. انتخاب نهایی با مالک است.\n"
    else:
        progress += ('- مالک انسانی نخستین گونه را انتخاب کند، سپس '
                     '[متن نمونهٔ Wayfinder](docs/workflows/wayfinder.md) استفاده شود؛ '
                     'هیچ موضوعی خودکار انتخاب یا آغاز نشده است.\n')
    index = header + '# ISIC Rev.5 — نمای طبقه‌بندی\n\n'
    index += ('[صفحهٔ رسمی و فایل‌ها](https://unstats.un.org/unsd/classifications/Econ/isic) · '
              '[رکورد رسمی](https://unstats.un.org/unsd/classifications/Family/Detail/2095) · '
              '[وضعیت و روش](../README.md) · [manifest](manifest.json)\n\n')
    index += f"وضعیت: **{manifest['repository_import_status']}**؛ رکورد مخزن: **{len(taxonomy)}/830**.\n\n"
    if not taxonomy:
        index += ('تمام section، division، group و classها و عنوان‌هایشان در این نمای قابل '
                  'توزیع غایب‌اند؛ هیچ ترجمهٔ فارسی وارد نشده است. برای پیمایش فعلاً از '
                  'فایل رسمی استفاده کنید. audit کامل منبع به معنی نمایش hierarchy در مخزن نیست.\n')
    else:
        index += '| شناسه | سطح | والد | English label | فارسی و وضعیت |\n| --- | --- | --- | --- | --- |\n'
        for r in taxonomy:
            index += f"| {r['id']} | {r['level']} | {r['parent_id'] or '—'} | {cell(r['label_en'])} | {cell(r['label_fa'] or '—')} ({r['translation_status']}) |\n"
    return {'CONTENTS.md': contents, 'PROGRESS.md': progress, 'taxonomy/isic-rev5/INDEX.md': index}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('check', help='validate structure and generated files')
    check.add_argument('--local-taxonomy', type=Path, help='official pinned CSV, read locally only')
    commands.add_parser('generate', help='regenerate navigation from canonical metadata')
    audit = commands.add_parser('audit-isic', help='audit pinned CSV without writing or redistributing it')
    audit.add_argument('path', type=Path)
    hashing = commands.add_parser('hash', help='SHA256 of chapter bytes for human approval record')
    hashing.add_argument('path', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'hash':
            print(digest(args.path.read_bytes()))
        elif args.command == 'audit-isic':
            manifest = read_json(ROOT, 'taxonomy/isic-rev5/manifest.json')
            records = audit_isic(args.path, manifest)
            print('PASS official snapshot: ' + json.dumps(dict(Counter(r['level'] for r in records))))
            print(f'{len(records)} unique records; zero parent/order errors; SHA256 {manifest["source_sha256"]}')
            print('Source audit only; repository redistribution coverage unchanged.')
        elif args.command == 'generate':
            # Generate is a view operation; check remains the validation gate.
            for name, body in generated(ROOT).items():
                (ROOT / name).write_text(body, encoding='utf-8')
                print(f'generated {name}')
        elif args.command == 'check':
            errors = validate(ROOT, args.local_taxonomy)
            if not errors:
                for name, body in generated(ROOT).items():
                    if (ROOT / name).read_text(encoding='utf-8') != body:
                        errors.append(f'stale generated index: {name}; run generate')
            if errors:
                for error in errors:
                    print(f'FAIL {error}', file=sys.stderr)
                return 1
            print('PASS metadata, identity, relationships, taxonomy, publication structure, citations, links, generated indexes')
            print('Human factual/editorial review and approval authority are not automated.')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
