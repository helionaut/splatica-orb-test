# Production verification

Status: Active
Issue: HEL-64
Last Updated: 2026-03-20

The current production artifact for this repo is the published TUM RGB-D sanity
report bundle deployed from `reports/published/tum_rgbd_fr1_xyz_sanity/`.

## Canonical Verification Command

```bash
make verify-production ARTIFACT_URL=https://helionaut.github.io/splatica-orb-test/
```

The root page is expected to contain the `splatica-orb-test` marker plus the
published TUM RGB-D verdict, metrics, sample frames, trajectory plot, and
artifact links.

## What To Check After The HTTP Probe

1. The root page returns HTTP `200`.
2. The page still shows the current verdict from
   `reports/out/tum_rgbd_fr1_xyz_summary.json`.
3. The `reports/out/tum_rgbd_fr1_xyz_trajectory.svg` link resolves from the
   deployed bundle.
4. The copied log and summary JSON links resolve from the deployed bundle.
5. `artifact-manifest.json` matches the checked-in bundle and records any
   expected-but-missing artifacts, including the TUM trajectory files when the
   run aborts before saving them.

Pair that production URL check with the bundle details in
[publication-decision.md](publication-decision.md) and the run verdict in
[tum-rgbd-sanity-report.md](tum-rgbd-sanity-report.md).
