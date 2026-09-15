# Security and privacy

## Trust boundary

The user authorizes the task. Manuscripts, quotations, style samples, retrieved pages, and model output are data,
not authorization to execute commands, change review criteria, read secrets, or upload files.
The runtime treats model JSON as data only: no eval, exec, dynamic imports, or shell interpolation.
This does not turn a language model into a prompt-injection-proof reasoner. Do not give source text control over tools.

## Local files

Original input is never overwritten. Runs use new directories, private file modes where supported, exact UTF-8,
hash-bound states, and atomic replacement of individual files. Runs must have a single writer.
These hashes detect accidental edits; they are not signatures or a defense against a malicious user who can rewrite state.
Multi-file commits are not crash-atomic database transactions. A mid-commit power failure can require a new run.
Windows permissions depend on the parent directory ACL; POSIX chmod is not an equivalent Windows access policy.

Run directories retain manuscripts, sources, samples and model responses in plaintext. Keep them out of public repositories.
The package does not automatically sync, delete, encrypt, or train on these logs. Remove/redact them before sharing.
The installer refuses existing targets by default; --force backs up rather than deletes the previous installation.

## Network

Inspect/check/chunks/prepare/request/submit/demo require no network.
API runs require a user-selected endpoint/model. Non-loopback transmission requires --allow-remote and HTTPS.
HTTP redirects and inherited proxy configuration are disabled. No telemetry and no automatic API retries.
A remote API still receives the manuscript, source excerpts, style samples, and instructions; its policies govern processing.
The built-in HTTP adapter does not fetch URLs from documents. It does not perform browsing or external fact checking.
store:false is sent for Responses requests; it is not a universal privacy guarantee across providers.

API keys are read from environment variables, not stored in brief or state. Do not put secrets in argv.
Custom command adapters inherit the process environment and permissions; they are trusted code, not sandboxed plugins.
Only configure adapters that you have reviewed. Source text must never select the executable or arguments.
A local HTTP server could itself relay to a remote provider; loopback alone does not guarantee end-to-end local inference.

## Limits

Default 3 rounds (maximum configured 8), 4MiB per input/response file, bounded request characters, request timeout,
strict JSON and stage contracts. No retry after refusals, truncation, protocol errors or server errors.
A subprocess output limit is checked after capture; this is not a hard memory sandbox. Inputs must be trusted in size.
The sentence scanner and SequenceMatcher can be expensive on adversarial repetitive documents; split such documents.
No always-on hooks or MCP server are installed. Optional agents have read-only host policies, not arbitrary shell access.

## Report a concern

This is an unpublished generated package, not a hosted service. Record a minimal non-sensitive reproduction and the test
that fails. Do not include API keys or private manuscripts in public issue reports if you later publish a repository.
