#!/usr/bin/env python3
"""Install the standalone skill and optional reviewers. No network or config edits."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'korean-writing'


def no_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError(f'Refusing symlink/junction in destination path: {part}')


def plan(host: str, scope: str, project: Path | None = None, destination: Path | None = None,
         with_agents: bool = False, home: Path | None = None) -> list[tuple[Path, Path]]:
    base = (home or Path.home()) if scope == 'user' else (project or Path.cwd())
    base = base.expanduser().absolute()
    if host == 'generic':
        if destination is None:
            raise ValueError('--destination is required for generic hosts')
        if with_agents:
            raise ValueError('Generic installs do not define a host-specific agents directory')
    elif destination is not None:
        raise ValueError('--destination is only for --host generic')
    elif host not in ('codex', 'claude'):
        raise ValueError('Unknown host')
    folder = '.agents' if host == 'codex' else '.claude'
    target = destination.expanduser().absolute() if destination else base / folder / 'skills' / NAME
    if target.name != NAME:
        raise ValueError('The final skill directory must be named korean-writing')
    jobs = [(ROOT / 'skills' / NAME, target)]
    if with_agents:
        src = ROOT / ('adapters/codex/agents' if host == 'codex' else 'agents')
        dst = base / ('.codex' if host == 'codex' else '.claude') / 'agents'
        ext = '*.toml' if host == 'codex' else '*.md'
        jobs += [(p, dst / p.name) for p in sorted(src.glob(ext))]
    return jobs


def install(jobs: list[tuple[Path, Path]], *, force: bool = False, dry_run: bool = False) -> list[dict]:
    """Preflight all paths, then replace each independently with an optional backup."""
    for src, dst in jobs:
        if not src.exists():
            raise ValueError(f'Missing package source: {src}')
        no_links(dst)
        if src.resolve() == dst.resolve() or src.resolve() in dst.resolve().parents:
            raise ValueError('Cannot install inside the source package')
        if dst.exists() and not force:
            raise ValueError(f'Target already exists: {dst}; use --force to preserve a backup and replace it')
        if dst.exists() and dst.is_dir() != src.is_dir():
            raise ValueError(f'Target has the wrong type: {dst}')
    result = []
    for src, dst in jobs:
        entry = {'source': str(src), 'destination': str(dst), 'action': 'would_install' if dry_run else 'installed'}
        if dry_run:
            entry['would_backup'] = dst.exists()
            result.append(entry)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        no_links(dst)
        stage_dir = Path(tempfile.mkdtemp(prefix='.munjang-install-', dir=dst.parent))
        stage = stage_dir / dst.name
        backup = None
        try:
            if src.is_dir():
                # Only bundled source, never follow a symlink introduced into the package.
                if any(p.is_symlink() for p in src.rglob('*')):
                    raise ValueError('Source skill contains a symlink')
                shutil.copytree(src, stage, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
            else:
                shutil.copy2(src, stage)
            if dst.exists():
                stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                backup = dst.with_name(dst.name + '.backup-' + stamp)
                os.replace(dst, backup)
                entry['backup'] = str(backup)
            try:
                os.replace(stage, dst)
            except OSError:
                if backup and not dst.exists():
                    os.replace(backup, dst)
                raise
        finally:
            shutil.rmtree(stage_dir, ignore_errors=True)  # Only our temporary staging directory.
        result.append(entry)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', required=True, choices=['codex', 'claude', 'generic'])
    p.add_argument('--scope', choices=['user', 'project'], default='user')
    p.add_argument('--project', type=Path)
    p.add_argument('--destination', type=Path)
    p.add_argument('--with-agents', action='store_true')
    p.add_argument('--force', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args(argv)
    if a.project is not None and a.scope != 'project':
        raise ValueError('--project requires --scope project')
    result = install(plan(a.host, a.scope, a.project, a.destination, a.with_agents),
                     force=a.force, dry_run=a.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8'); sys.stderr.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(f'munjang installer: {exc}', file=sys.stderr)
        raise SystemExit(2)
