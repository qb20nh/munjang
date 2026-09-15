# Test report - Munjang 1.0.0

Recorded during package creation on 2026-09-15.

## Executed

- Python: 3.13.5.
- OS: Linux-6.18.44-x86_64-with-glibc2.41.
- Command: `python -m unittest discover -s skills/korean-writing/tests -v`.
- Result: 156 tests passed, 0 failed, 0 skipped, 5.917 seconds in this run.
- 250 deterministic generated-text lossless reconstruction examples were also exercised inside one property-style test.
- Package structural lint: passed. JSON files, identity, skill frontmatter, relative Markdown links, Python 3.10 syntax,
  and Codex agent TOML were checked locally. This is not the official host installer or a full universal YAML validator.
- Offline demonstration: 4 fixture responses, 1 admitted correction round, followed by a no-issues stop.
- Responses API and Chat Completions adapters: loopback HTTP mock integration tests, including complete editing loops.
- Command adapter: subprocess fixture integration, Unicode/spaced path, timeout, invalid output, literal shell metacharacters.
- Installer: temporary project/user-like locations, Claude/Codex/generic layouts, no-overwrite, backup replacement,
  preflight conflict prevention, optional reviewers, symlink refusal and installed script execution.

## Contract coverage

UTF-8, CRLF/BOM, code/quote/link/math/citation preservation, numeric values/units/order, manual literals,
layout, length/change budgets, full review-unit coverage, stale hashes, missing/duplicate IDs, malformed JSON,
patch permissions, mandatory verdict dimensions, uncertain/failing review rejection, no-op and cycle termination,
round limits, rejection rollback, interrupted/resumable workflows, altered source/brief/baseline/candidate detection,
request bounds, response provenance, network opt-in, redirects, refusals and truncation.

A role-reversal test deliberately demonstrates that a literal checker can pass a semantically incorrect sentence.
The program does not claim to prove meaning preservation. Synthetic reviewers in tests supply fixtures, not independent judgments.

## Not executed or not established

- No live Codex or Claude Code host installation/load test: neither executable is present in the creation environment.
- No paid or public model API was called. HTTP servers were local fixtures; they did not run an LLM.
- No human-rated or real-model writing-quality benchmark. The 30 semantic evaluation cases and 16 activation cases
  are prepared inputs with expected judgments, not measured performance results.
- No runtime execution on Windows, macOS or Python 3.10 in this session. CI configuration for those environments is included,
  but a CI configuration file is not evidence that those jobs have run.
- No public marketplace submission, publisher verification, account installation, web deployment or MCP server.
- No independent proof of factual truth, perfect Korean sentence boundaries, or superior literary quality.

## Reproduce

From the extracted full package directory:

```sh
python tools/validate_package.py
python -m unittest discover -s skills/korean-writing/tests -v
```

From the standalone skill directory:

```sh
python -m unittest discover -s tests -v
```

The standalone archive intentionally omits the plugin-level installer and will skip its 11 tests.
All runtime and provider tests remain self-contained. Read `tests/test_adapters.py` for which operations are simulated.
Detailed raw output is in the full package's `docs/test-run.txt`.
