#!/usr/bin/env python3
"""Munjang Workbench CLI. Python 3.10+, standard library only."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from munjanglib.common import VERSION, ContractError, atomic_text, digest, brief_config, dumps, loads, read_json, read_text, require, write_json
from munjanglib.document import lint, protected_spans, unit_records, units
from munjanglib.engine import Session, run_session
from munjanglib.providers import CommandProvider, DemoProvider, HTTPProvider, Router
from munjanglib.validation import check_text


def make_provider(args):
    if args.backend == 'demo':
        return DemoProvider()
    if args.backend == 'command':
        require(bool(args.command_json), '--command-json is required for command backend')
        return CommandProvider(loads(args.command_json), args.timeout)
    require(bool(args.base_url) and bool(args.model), '--base-url and --model are required')
    kwargs = dict(kind=args.backend, key_env=args.api_key_env, allow_remote=args.allow_remote,
                  timeout=args.timeout, output_tokens=args.max_output_tokens,
                  json_mode=args.json_mode, token_parameter=args.token_parameter)
    primary = HTTPProvider(args.base_url, args.model, **kwargs)
    reviewer = HTTPProvider(args.base_url, args.reviewer_model, **kwargs) if args.reviewer_model else None
    return Router(primary, reviewer)


def backend_options(parser):
    parser.add_argument('--backend', choices=['demo', 'command', 'responses', 'chat-completions'], required=True)
    parser.add_argument('--command-json', help='A JSON array of user-configured argv; never evaluated by a shell')
    parser.add_argument('--base-url', help='API base including /v1, without the endpoint suffix')
    parser.add_argument('--model', help='An actual model ID available in your environment; no default is assumed')
    parser.add_argument('--reviewer-model', help='Optional separate HTTP reviewer model on the same endpoint')
    parser.add_argument('--api-key-env', default='OPENAI_API_KEY')
    parser.add_argument('--allow-remote', action='store_true', help='Explicitly allow source text transmission to a non-loopback HTTPS endpoint')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--max-output-tokens', type=int, default=8192)
    parser.add_argument('--json-mode', action='store_true', help='Request JSON-object mode if the model supports it')
    parser.add_argument('--token-parameter', choices=['max_tokens', 'max_completion_tokens'], default='max_completion_tokens')


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', action='version', version=VERSION)
    sub = p.add_subparsers(dest='action', required=True)
    for name in ('inspect', 'chunks'):
        s = sub.add_parser(name)
        s.add_argument('--input', type=Path, required=True)
        s.add_argument('--output', type=Path)
        if name == 'inspect':
            s.add_argument('--brief', type=Path)
        else:
            s.add_argument('--max-chars', type=int, default=6000)
            s.add_argument('--overlap-units', type=int, default=2)
    s = sub.add_parser('check', help='Deterministic preservation check, NOT a semantic approval')
    s.add_argument('--original', type=Path, required=True)
    s.add_argument('--candidate', type=Path, required=True)
    s.add_argument('--brief', type=Path)
    s.add_argument('--output', type=Path)
    for name in ('prepare', 'run'):
        s = sub.add_parser(name)
        s.add_argument('--input', type=Path, required=True)
        s.add_argument('--brief', type=Path)
        s.add_argument('--output', type=Path, required=True, help='New run directory; original is never overwritten')
        if name == 'run':
            backend_options(s)
    for name in ('request', 'submit', 'status', 'export', 'resume'):
        s = sub.add_parser(name)
        s.add_argument('session', type=Path)
        if name == 'request': s.add_argument('--output', type=Path)
        if name == 'submit': s.add_argument('--response', type=Path, required=True)
        if name == 'resume': backend_options(s)
    args = p.parse_args(argv)
    if hasattr(args, 'timeout'):
        require(0 < args.timeout <= 3600, '--timeout must be positive and at most 3600 seconds')
    config = brief_config(read_json(args.brief) if getattr(args, 'brief', None) else {})
    if args.action == 'inspect':
        text = read_text(args.input)
        value = {'sha256': digest(text), 'units': unit_records(text),
                 'protected_spans': protected_spans(text, config['quote_policy']), 'lint_candidates': lint(text),
                 'notice': 'Boundary detection and lints are heuristics, not semantic or factual verification.'}
    elif args.action == 'chunks':
        require(args.max_chars > 0 and 0 <= args.overlap_units <= 100, 'Invalid chunk size or overlap')
        text = read_text(args.input)
        records = unit_records(text)
        groups, current, size = [], [], 0
        for unit in records:
            if current and size + len(unit['text']) > args.max_chars:
                groups.append(current); current = []; size = 0
            current.append(unit); size += len(unit['text'])
        if current: groups.append(current)
        chunks, offset = [], 0
        for index, group in enumerate(groups):
            a, b = offset, offset + len(group)
            chunks.append({'index': index + 1,
                           'owned_units': group,
                           'context_before_read_only': records[max(0, a-args.overlap_units):a],
                           'context_after_read_only': records[b:b+args.overlap_units],
                           'oversized_unit': any(len(u['text']) > args.max_chars for u in group)})
            offset = b
        value = {'source_sha256': digest(text), 'chunks': chunks,
                 'notice': 'Host-assisted chunk plan only. No model calls or automatic merge; context is read-only.'}
    elif args.action == 'check':
        value = check_text(read_text(args.original), read_text(args.candidate), config)
    elif args.action in ('prepare', 'run'):
        provider = make_provider(args) if args.action == 'run' else None
        session = Session.create(args.output, read_text(args.input), config, provider.label if provider else 'host')
        if provider:
            try:
                value = run_session(session, provider)
            except (ContractError, OSError, ValueError) as exc:
                session.record_error(str(exc))
                raise
        else:
            value = {'session': str(session.directory), 'next_stage': session.phase}
        print(dumps(value), end='')
        return 0
    else:
        session = Session(args.session)
        if args.action == 'request': value = session.request()
        elif args.action == 'submit':
            session.submit(read_json(args.response), responder="host")
            value = {'session': str(session.directory), 'next_stage': session.phase, 'outcome': session.state['outcome']}
        elif args.action == 'status': value = session.state
        elif args.action == 'export': value = session.export(interrupted=session.phase != 'done')
        elif args.action == 'resume':
            provider = make_provider(args)
            require(provider.label == session.state['provider'],
                    'Backend/model differs from session provenance. Continue with request/submit or use the same backend')
            try:
                value = run_session(session, provider)
            except (ContractError, OSError, ValueError) as exc:
                session.record_error(str(exc)); raise
    if getattr(args, 'output', None):
        atomic_text(args.output, dumps(value))
    else:
        print(dumps(value), end='')
    if args.action == 'check' and not value['deterministic_pass']:
        return 1
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ContractError, OSError, ValueError) as exc:
        print(f'munjang: {exc}', file=sys.stderr)
        raise SystemExit(2)
