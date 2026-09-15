"""Fail-closed structural gates; semantic approval remains a separate attestation."""
from __future__ import annotations
from collections import Counter
import re
from .common import CHECK_NAMES, ContractError, digest, object_keys, require, string, strings
from .document import NUMBER, diff_metrics, editable_ids, protected_spans, units


def check_text(original: str, candidate: str, brief: dict) -> dict:
    string(candidate, "candidate", nonempty=bool(original.strip()))
    errors, warnings = [], []
    for protected in brief['protected_strings']:
        before_n = original.count(protected)
        after_n = candidate.count(protected)
        if after_n != max(1, before_n):
            errors.append({"code": "protected_string", "text": protected,
                           "expected_count": max(1, before_n), "actual_count": after_n})
    old = Counter((s['kind'], s['text']) for s in protected_spans(original, brief['quote_policy']))
    new = Counter((s['kind'], s['text']) for s in protected_spans(candidate, brief['quote_policy']))
    for (kind, text), count in (old - new).items():
        errors.append({"code": "protected_span_missing", "kind": kind, "text": text, "count": count})
    # An added quotation, citation or code fragment can be an invented attribution.
    for (kind, text), count in (new - old).items():
        if brief['mode'] == 'copyedit':
            errors.append({"code": "protected_span_added", "kind": kind, "text": text, "count": count})
        else:
            warnings.append({"code": "new_protected_span_needs_review", "kind": kind, "text": text, "count": count})
    if brief['freeze_numbers']:
        a, b = NUMBER.findall(original), NUMBER.findall(candidate)
        if Counter(a) != Counter(b):
            errors.append({"code": "number_inventory", "before": a, "after": b})
        elif brief['mode'] == 'copyedit' and a != b:
            errors.append({"code": "number_order", "before": a, "after": b})
    if brief['mode'] == 'copyedit':
        a, b = units(original), units(candidate)
        shape_a = [(u.kind, None if u.editable else u.text) for u in a]
        shape_b = [(u.kind, None if u.editable else u.text) for u in b]
        if shape_a != shape_b:
            errors.append({"code": "review_unit_or_layout_change",
                           "before_units": len(a), "after_units": len(b),
                           "note": "Lossless unit/layout policy, not a perfect sentence parser"})
    for key, sign in (('min_chars', -1), ('max_chars', 1)):
        target = brief[key]
        if target is not None and (len(candidate) - target) * sign > 0:
            errors.append({"code": key, "target": target, "actual": len(candidate)})
    metrics = diff_metrics(original, candidate)
    limit = brief['max_change_ratio']
    if limit is not None and metrics['change_ratio'] > limit + 1e-12:
        errors.append({"code": "change_budget", "limit": limit, "actual": metrics['change_ratio']})
    # A changed marker is evidence to inspect, not an automatic grammatical verdict.
    for name, pattern in {
        'modality': r'할 수 있|할 수 없|해야|해도|가능|필요|금지|허용',
        'negation': r'않|아니|없|못', 'scope': r'일부|모든|대부분|항상|때때로|적어도|최대|최소',
        'aspect': r'기 시작|고 있|이미|아직',
        'causality': r'관련|상관|원인|때문|초래|일으켰',
    }.items():
        if Counter(re.findall(pattern, original)) != Counter(re.findall(pattern, candidate)):
            warnings.append({"code": "semantic_marker_change", "category": name,
                             "note": "A heuristic warning, not a semantic proof"})
    return {
        'schema_version': 1, 'original_sha256': digest(original), 'candidate_sha256': digest(candidate),
        'deterministic_pass': not errors, 'errors': errors, 'warnings': warnings,
        'metrics': metrics, 'semantic_verification': 'not_performed_by_this_check',
        'external_fact_check': 'not_performed',
    }


def validate_diagnosis(value: dict, text: str) -> dict:
    object_keys(value, {'base_sha256', 'reviewed_ids', 'issues'})
    require(value['base_sha256'] == digest(text), 'Diagnosis is for a different document hash')
    reviewed = strings(value['reviewed_ids'], 'reviewed_ids', unique=True)
    require(set(reviewed) == set(editable_ids(text)), 'Diagnosis coverage is incomplete or has unknown IDs')
    require(isinstance(value['issues'], list), 'issues must be a list')
    by_id = {u.id: u for u in units(text) if u.editable}
    known = set()
    for issue in value['issues']:
        object_keys(issue, {'id', 'unit_ids', 'severity', 'category', 'evidence', 'reason', 'suggestion'})
        for key in ('id', 'category', 'evidence', 'reason', 'suggestion'):
            string(issue[key], 'issue.' + key)
        require(issue['id'] not in known, 'Duplicate issue ID')
        known.add(issue['id'])
        require(issue['severity'] in ('error', 'improvement', 'preference'), 'Invalid issue severity')
        ids = strings(issue['unit_ids'], 'unit_ids', unique=True)
        require(bool(ids) and set(ids) <= set(by_id), 'Issue references unknown or locked units')
        require(any(issue['evidence'] in by_id[i].text for i in ids),
                'Issue evidence must be an exact excerpt from a referenced unit')
    return value


def apply_revision(value: dict, text: str, diagnosis: dict, brief: dict) -> str:
    object_keys(value, {'base_sha256', 'patches', 'rewrite', 'skipped_issue_ids'})
    require(value['base_sha256'] == digest(text), 'Revision is stale')
    require(isinstance(value['patches'], list), 'patches must be a list')
    skipped = strings(value['skipped_issue_ids'], 'skipped_issue_ids', unique=True)
    issues = {i['id']: i for i in diagnosis['issues']}
    require(set(skipped) <= set(issues), 'Unknown skipped issue ID')
    if value['rewrite'] is not None:
        require(brief['mode'] != 'copyedit', 'Full rewrite is forbidden in copyedit mode')
        require(not value['patches'], 'Use rewrite OR patches, not both')
        string(value['rewrite'], 'rewrite')
        require(any(i['severity'] != 'preference' and i['id'] not in skipped for i in issues.values()),
                'Rewrite needs an actionable, unskipped issue')
        return value['rewrite']
    source_units = units(text)
    by_id = {u.id: u for u in source_units}
    replacements = {}
    handled = set()
    for patch in value['patches']:
        object_keys(patch, {'unit_id', 'before', 'after', 'issue_ids', 'reason'})
        uid = string(patch['unit_id'], 'unit_id')
        require(uid in by_id and by_id[uid].editable, 'Cannot patch an unknown or locked unit')
        require(uid not in replacements, 'Overlapping/duplicate patches')
        require(patch['before'] == by_id[uid].text, 'Patch before-text does not match exactly')
        string(patch['after'], 'after')
        string(patch['reason'], 'reason')
        ids = strings(patch['issue_ids'], 'issue_ids', unique=True)
        require(bool(ids) and set(ids) <= set(issues), 'Patch needs valid issue IDs')
        require(not set(ids) & set(skipped), 'An issue cannot be both patched and skipped')
        require(all(uid in issues[i]['unit_ids'] for i in ids), 'Patch is outside diagnosed locations')
        require(any(issues[i]['severity'] != 'preference' for i in ids), 'Preference-only rewrites are not admitted')
        if brief['mode'] == 'copyedit':
            require(patch['after'] == patch['after'].strip(), 'Copyedit cannot alter unit boundary whitespace')
            require('\n' not in patch['after'] and '\r' not in patch['after'], 'Copyedit cannot insert line breaks')
        replacements[uid] = patch['after']
        handled.update(ids)
    require(handled | set(skipped) == set(issues), 'Every issue must be patched or explicitly skipped')
    return ''.join(replacements.get(u.id, u.text) for u in source_units)


def validate_verdict(value: dict, baseline: str, current: str, candidate: str, diagnosis: dict) -> dict:
    object_keys(value, {'base_sha256', 'candidate_sha256', 'decision', 'reviewed_original_ids',
                       'reviewed_candidate_ids', 'checks', 'resolved_issue_ids', 'unresolved_issue_ids',
                       'new_issues', 'reason'})
    require(value['base_sha256'] == digest(current), 'Verification has stale base hash')
    require(value['candidate_sha256'] == digest(candidate), 'Verification has stale candidate hash')
    require(value['decision'] in ('accept', 'reject', 'needs_review'), 'Invalid verdict')
    string(value['reason'], 'reason')
    for field, target in (('reviewed_original_ids', baseline), ('reviewed_candidate_ids', candidate)):
        ids = strings(value[field], field, unique=True)
        require(set(ids) == set(editable_ids(target)), f'{field}: incomplete or unknown coverage')
    require(isinstance(value['checks'], list), 'checks must be a list')
    names = set()
    for check in value['checks']:
        object_keys(check, {'name', 'status', 'evidence'})
        require(isinstance(check['name'], str) and check['name'] in CHECK_NAMES and check['name'] not in names,
                'Unknown or duplicate verification check')
        names.add(check['name'])
        require(check['status'] in ('pass', 'fail', 'uncertain'), 'Invalid check status')
        string(check['evidence'], 'check.evidence')
    require(names == set(CHECK_NAMES), 'Missing verification dimensions')
    known = {i['id'] for i in diagnosis['issues']}
    resolved = set(strings(value['resolved_issue_ids'], 'resolved_issue_ids', unique=True))
    unresolved = set(strings(value['unresolved_issue_ids'], 'unresolved_issue_ids', unique=True))
    require(not resolved & unresolved and resolved | unresolved == known, 'Issue dispositions must partition diagnosed IDs')
    strings(value['new_issues'], 'new_issues')
    if value['decision'] == 'accept':
        actionable = {i['id'] for i in diagnosis['issues'] if i['severity'] != 'preference'}
        require(bool(resolved & actionable), 'Acceptance requires a resolved actionable issue')
        require(all(c['status'] == 'pass' for c in value['checks']), 'Acceptance requires every semantic check to pass')
        require(not value['new_issues'], 'Acceptance cannot introduce new issues')
    return value
