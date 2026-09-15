#!/usr/bin/env python3
"""Dependency-free package structural lint, not a substitute for host installation."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path = ROOT) -> dict:
    errors, warnings = [], []
    skill = root / 'skills/korean-writing'
    required = ['plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json',
                '.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json',
                'README.md', 'LICENSE', 'SECURITY.md', 'skills/korean-writing/SKILL.md',
                'skills/korean-writing/scripts/workbench.py']
    for name in required:
        if not (root / name).is_file(): errors.append('Missing: ' + name)
    for path in root.rglob('*.json'):
        try: json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, OSError) as exc: errors.append(f'{path.relative_to(root)}: {exc}')
    for name in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json'):
        if not (root / name).exists(): continue
        try:
            manifest = json.loads((root / name).read_text(encoding='utf-8'))
            if manifest.get('name') != 'munjang' or manifest.get('version') != '1.0.0':
                errors.append('Manifest identity mismatch: ' + name)
        except ValueError: pass
    if (skill / 'SKILL.md').exists():
        text = (skill / 'SKILL.md').read_text(encoding='utf-8')
        pieces = text.split('---', 2)
        if len(pieces) != 3 or pieces[0]: errors.append('Invalid SKILL frontmatter delimiters')
        else:
            # The package intentionally uses plain one-line top-level scalar values.
            front = dict(re.findall(r'^([a-z-]+): (.+)$', pieces[1], re.M))
            name = front.get('name', '')
            if name != skill.name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
                errors.append('Invalid skill name')
            if not 1 <= len(front.get('description', '')) <= 1024: errors.append('Invalid skill description')
            if not 1 <= len(front.get('compatibility', '')) <= 500: errors.append('Invalid compatibility')
            if len(text.splitlines()) >= 500: warnings.append('SKILL.md is at or above 500 lines')
    link_count = 0
    for path in root.rglob('*.md'):
        for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith(('mailto:', '#')): continue
            dest = (path.parent / unquote(target.split('#')[0])).resolve()
            link_count += 1
            if root.resolve() not in dest.parents and dest != root.resolve(): errors.append('Link escapes package: ' + target)
            elif not dest.exists(): errors.append(f'Broken link in {path.relative_to(root)}: {target}')
    scripts = list(root.rglob('*.py'))
    for path in scripts:
        try: ast.parse(path.read_text(encoding='utf-8'), filename=str(path), feature_version=(3, 10))
        except (SyntaxError, ValueError) as exc: errors.append(f'Python 3.10 syntax: {exc}')
    try:
        import tomllib
    except ImportError:
        warnings.append('Full TOML parser unavailable on Python 3.10; Codex agent TOML parsing not performed')
    else:
        for path in root.rglob('*.toml'):
            try:
                agent = tomllib.loads(path.read_text(encoding='utf-8'))
                if not all(agent.get(k) for k in ('name', 'description', 'developer_instructions')):
                    errors.append('Missing agent key: ' + str(path))
                if agent.get('sandbox_mode') != 'read-only': errors.append('Agent is not read-only: ' + str(path))
            except ValueError as exc: errors.append(f'Invalid TOML {path}: {exc}')
    for stage in ('draft', 'diagnose', 'revise', 'verify'):
        if not (skill / 'prompts' / f'{stage}.md').is_file(): errors.append('Missing stage: ' + stage)
    return {'pass': not errors, 'errors': errors, 'warnings': warnings,
            'python_files_parsed': len(scripts), 'local_markdown_links_checked': link_count,
            'scope': 'Local structural lint; official host install and semantic quality not tested'}


if __name__ == '__main__':
    report = validate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['pass'] else 1)
