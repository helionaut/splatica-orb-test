# Publication Decision

Status: Accepted
Issue: HEL-45
Last Updated: 2026-03-18

## Current Decision

`splatica-orb-test` still does not need a publishable artifact, and this repo
should not add a placeholder deployment target.

The repo can now generate local dry-run outputs through the harness:

- `build/smoke-plan.md` from `make build`
- dry-run logs under `logs/out/`
- dry-run reports under `reports/out/`
- a future URL verification command via `make verify-production`

Those outputs are local validation scaffolding, not a release-grade
deliverable. They do not yet capture a reviewed ORB-SLAM3 run against a pinned
baseline and dataset snapshot, and they are intentionally disposable. Because
no concrete validation report or results bundle is ready to distribute, the
correct publication choice is still "no deployment for now."

## Why This Is The Right Call

- The ticket explicitly warns against assuming a user-facing web app.
- The current harness only produces dry-run scaffolding and placeholder
  outputs, not a stable artifact worth distributing.
- A fake GitHub Pages site or empty release would create a maintenance burden
  without improving validation or review.
- The repo now has enough structure to define a future publication path without
  pretending that a publishable result already exists.

## Trigger To Revisit Publication

Open a follow-up publication change only after the repo can generate one of
these concrete outputs from source control and a pinned run manifest:

- a downloadable results bundle that contains logs, configs, and outcome data
- a static validation report that summarizes a real ORB-SLAM3 evaluation run
- both, if the report and raw bundle serve different review needs

Until one of those exists, the release answer remains "no deployment."

## Expected First Artifact

If publication becomes necessary, prefer a downloadable results bundle as the
primary artifact. Publish that bundle as a GitHub Release asset tied to the
validating commit or release tag. A bundle is easier to version and review than
a live site, and it matches the current repo goal better than an interactive
deployment.

The first publishable bundle should include at least:

- the repo commit SHA that produced it
- the ORB-SLAM3 source baseline or upstream commit under test
- the dataset identifier or dataset snapshot reference
- the settings/configuration files used for the run
- the validation logs and a concise pass/fail summary
- a manifest file with generation time and checksum data

If reviewers need a more readable summary, add a static HTML or Markdown report
alongside the same release asset set instead of replacing it. A dedicated
static site should remain optional until repeated review needs justify it.

## Release Verification Path

Once a concrete artifact exists, verification should require all of the
following:

1. Regenerate the report or bundle from the documented command path on a clean
   checkout.
2. Confirm the manifest captures the producing repo SHA, dataset reference,
   upstream baseline, and config version.
3. Run `make verify-production ARTIFACT_URL=https://<published-artifact-url>`
   against the published URL and confirm the expected marker resolves over
   HTTPS.
4. Verify the published artifact checksum matches the locally generated output.
5. Confirm the PR summary and Linear handoff/completion comment both record the
   exact final artifact URL or release-asset location.

This ticket does not implement those publication steps yet because there is no
artifact to verify.

## Team Reporting Path

For the current repo state, report the decision as "no publishable artifact
yet" in:

- this document
- the `HEL-45` Linear update comments
- the eventual PR that lands this decision

When a concrete artifact is eventually published, record the final artifact
location in both places:

- the PR body or merge summary that introduced the artifact
- a fresh `## Handoff Update` or `## Completion Update` comment on the Linear
  issue, including the final URL or release-asset location
