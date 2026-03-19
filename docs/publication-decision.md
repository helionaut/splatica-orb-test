# Publication Decision

Status: Accepted
Issue: HEL-64
Last Updated: 2026-03-20

## Current Decision

`splatica-orb-test` now has one concrete publishable artifact: the public TUM
RGB-D sanity-run report bundle generated from `manifests/tum_rgbd_fr1_xyz_sanity.json`.

The canonical versioned bundle lives at:

- `reports/published/tum_rgbd_fr1_xyz_sanity/index.html`
- `reports/published/tum_rgbd_fr1_xyz_sanity/artifact-manifest.json`

The deploy target is a static GitHub Pages publication of that same bundle on
`main`. The repo copy remains the audit source of truth; Pages is the review
surface.

## Why This Is The Right Call

- The repo now produces a real ORB-SLAM3 execution artifact rather than only
  dry-run scaffolding.
- The published index shows exactly what ran, what outputs were produced, what
  trajectory artifacts were missing, and whether the lane is a useful
  baseline.
- A static report fits the review need better than a placeholder app or a
  hidden local-only bundle.
- The same checked-in bundle can drive both GitHub review and deployed review
  without introducing a second artifact format.

## Scope Of The Published Artifact

The published bundle includes:

- the repo commit that produced the report
- the pinned ORB-SLAM3 upstream commit under test
- the exact manifest, dataset root, association file, and runtime command
- the run verdict and summary metrics
- the copied markdown report, HTML report, summary JSON, trajectory SVG, and
  log
- the sample RGB frames referenced by the published page
- an artifact manifest that records which expected files were missing

The current published verdict is still `not_useful`. Publication does not mean
the underlying lane passed; it means the result is now inspectable and auditable.

## Deployment Shape

- Source bundle: `reports/published/tum_rgbd_fr1_xyz_sanity/`
- Expected deployed root URL:
  `https://helionaut.github.io/splatica-orb-test/`
- Expected secondary visual report URL:
  `https://helionaut.github.io/splatica-orb-test/reports/out/tum_rgbd_fr1_xyz.html`

## Verification Path

When the `main` branch bundle is deployed, verify all of the following:

1. Run `make verify-production ARTIFACT_URL=https://helionaut.github.io/splatica-orb-test/`.
2. Confirm the deployed root still contains the expected `splatica-orb-test`
   marker.
3. Confirm the deployed page shows the published verdict and links to the
   copied artifacts.
4. Confirm `artifact-manifest.json` matches the checked-in bundle contents and
   records the missing trajectory files when they are absent.
5. Record the final URL in the PR summary and the Linear handoff/completion
   comment.
