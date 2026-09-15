# Evaluation and controlled improvement

The bundled unit/integration tests measure program contracts, not literary quality or semantic accuracy of a real model.
`skills/korean-writing/evals/cases.jsonl` contains authored examples and expected judgments, not measured scores.
`triggers.jsonl` contains positive and negative activation cases for host-level testing.

## Compare fairly

Select real, authorized texts across business, argument, explanation, fiction, technical and short-form writing.
Hold model, version, context, input, output allowance, sampling and tools constant. Compare a plain baseline prompt against this skill.
Separate editing modes and preserve the original source. Include already-good prose where no change is best.
Use blinded A/B judgments and optionally swap order. Annotators should examine meaning/evidence first, elegance second.

Report dimensions separately: factual additions, meaning damage, claim-strength changes, quote/value preservation,
true-error correction, needless change, voice retention, readability, token/call cost and latency.
A single aggregate score can hide a serious failure. Do not score one model's self-praise as independent evaluation.
For a large corpus, report denominators, uncertainty, failure examples, input language and model/tool settings.

## Improve without moving the goalposts

A failure should yield a minimal non-sensitive test. Change one rule or implementation at a time.
Run all regression tests and held-out examples. Propose the change and its tradeoffs before adopting a new release.
Do not weaken protection gates just to get a higher acceptance rate. Do not silently mutate the installed skill during editing.
Do not ingest users' private drafts, logs or style samples into a permanent corpus without their consent.
