# Publication Decision

Status: Accepted
Issue: HEL-45
Last Updated: 2026-03-18

## Current Decision

`splatica-orb-test` does not need a publishable artifact yet, and this repo
should not add a placeholder deployment target.

As of this decision, the tracked repository only contains bootstrap workflow
files and project instructions. It does not contain:

- a generated validation report
- a downloadable results bundle
- a user-facing web app
- a release pipeline that produces a concrete artifact

Because no concrete deliverable exists yet, the correct deployment choice is
"no publication for now."

## Why This Is The Right Call

- The ticket explicitly warns against assuming a user-facing web app.
- The current tracked repo state has no artifact to host or distribute.
- A fake GitHub Pages site or empty release would create a maintenance burden
  without improving validation or review.

## Trigger To Revisit Publication

Open a follow-up publication change only after the repo can generate one of
these concrete outputs from source control:

- a static validation report that summarizes a real ORB-SLAM3 evaluation run
- a downloadable results bundle that contains logs, configs, and outcome data
- both, if the report and raw bundle serve different review needs

Until one of those exists, the release answer remains "no deployment."

## Expected First Artifact

If publication becomes necessary, prefer a downloadable results bundle as the
primary artifact. The bundle should be easier to version and review than a live
site, and it matches the current repo goal better than an interactive
deployment.

The first publishable bundle should include at least:

- the repo commit SHA that produced it
- the ORB-SLAM3 source baseline or upstream commit under test
- the dataset identifier or dataset snapshot reference
- the settings/configuration files used for the run
- the validation logs and a concise pass/fail summary
- a manifest file with generation time and checksum data

If reviewers need a more readable summary, add a static HTML or Markdown report
alongside the bundle instead of replacing it.

## Release Verification Path

Once a concrete artifact exists, verification should require all of the
following:

1. Regenerate the report or bundle from the documented command path on a clean
   checkout.
2. Confirm the manifest captures the producing repo SHA, dataset reference,
   upstream baseline, and config version.
3. Verify the published artifact checksum matches the locally generated output.
4. Confirm the published URL or release asset resolves and downloads correctly.

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
