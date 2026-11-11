# knowledge-base-integrity (archived)

**Merged into [knowledge-base-kit](https://github.com/danielnaab/knowledge-base-kit) v2.0.0** (2026-11-11), with
the conventions it enforces (formerly meta-knowledge-base). This repository's history continues there; v0.4.0 is its
last release here, and its tags stay so existing pins keep working.

To move a repo that pins this one, follow the kit's
[v2.0.0 migration steps](https://github.com/danielnaab/knowledge-base-kit/blob/v2.0.0/CHANGELOG.md#migration). In
short: replace this input with `knowledge-base-kit = { url = "github:danielnaab/knowledge-base-kit/v2.0.0";
flake = false; };`, and read the checker as `${inputs.knowledge-base-kit}/src`.
