# Architecture

## Layers

- `SKILL.md`: routing, mode selection, reading plan, bounded workflow, output contract.
- `references/`: selectively loaded contract, craft, genre, evidence, semantic preservation and runtime guidance.
- `prompts/`: draft/diagnose/revise/verify stage instructions.
- `assets/`: strict JSON response schemas, brief schema, host-managed style/source templates.
- `scripts/munjanglib`: stdlib I/O/contracts, lossless units, deterministic gates, state machine, provider adapters.
- `agents/` and `adapters/codex/agents/`: optional read-only reviewers, no mandatory multi-agent dependency.
- root `plugin.json`, host compatibility manifests and local catalog descriptors: installation/discovery, not execution engines.

## State machine

`draft? -> diagnose -> revise -> verify -> diagnose ... -> done`

Diagnosis binds to current hash and must cover every editable unit. Issues need an exact supporting excerpt.
Copyedit revisions patch whole diagnosed units with an exact before-text and associated issue IDs.
Restructure/draft may replace the whole document; literal gates and semantic review still apply.
The candidate is checked against the immutable baseline, not only the immediately preceding version.
Verification binds both current/candidate hashes, baseline/candidate coverage and 12 dimensions.
Only an accepted, fully passing verdict with at least one actionable issue resolved can commit a candidate.
No-op, cycle, round limit, machine rejection, semantic rejection or needs_review terminates the loop.
Malformed or interrupted calls leave a resumable phase and never count as a completed review.

`max_rounds` counts correction rounds, not individual model calls. With R rounds the maximum normal calls are 3R plus
one initial draft call when needed. Early stops use fewer. There are no automatic JSON repair or model retry calls.

## Units, not a perfect sentence parser

Units preserve every character: prose, physical line separators, indentation/list markers, fenced code and layout.
Sentence-like boundaries account for common decimal, abbreviation, quote, inline code and URL cases.
This is not a Korean syntactic analyzer. The locked physical layout is stricter than paragraph-count preservation.
Structural equality cannot prove ordering of meaning after text substitution; the semantic reviewer must check that.

## Attestation versus enforcement

The program can enforce hashes and literal contracts. It cannot prove that a reviewer actually read or understood every ID.
A malicious or mistaken reviewer can claim incorrect semantic passes. Another model is an optional additional signal,
not ground truth. Fact provenance is a separate host/user responsibility.
A draft's baseline is generated, so preserving it does not establish that its claims are true. Reports keep this distinction.

## Extension points

Provider protocol: `.label` and `.complete(request) -> response dict`. The CLI supports built-in demo, command,
Responses and Chat Completions adapters. Command stdin/stdout provides provider independence without dependencies.
JSON shape is validated locally even if an upstream API claims structured output. No automatic shell tools are supplied.
New genre rules go into references; protocol changes require schema updates, validation updates, tests and a version bump.

## Non-goals

AI-authorship detection, detector evasion, forged source retrieval, automatic book ingestion, spell-check dictionary completeness,
perfect syntax parsing, automatic remote publishing, background daemon, server/MCP implementation, and unbounded chunk orchestration.
