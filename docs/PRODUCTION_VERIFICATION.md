# Production verification

`HEL-45` has not created a published artifact yet, so production verification is
documented in advance.

The current local dry-run outputs under `build/`, `logs/out/`, and
`reports/out/` are not the published artifact for this repo. They are harness
scaffolding only.

When a report or results bundle is published, run:

```bash
make verify-production ARTIFACT_URL=https://<published-artifact-url>
```

The verification script checks that the URL responds successfully and still
contains the expected `splatica-orb-test` marker. For a static report, point the
URL at the published report page; for a downloadable bundle, point it at the
release asset landing page or equivalent artifact index.

Pair that network check with the manifest and checksum review documented in
[publication-decision.md](publication-decision.md).
