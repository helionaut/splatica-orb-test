---
tracker:
  kind: linear
  project_slug: "c30355e13948"
  active_states:
    - Todo
    - In Progress
    - Merging
    - Rework
  terminal_states:
    - Closed
    - Cancelled
    - Canceled
    - Duplicate
    - Done
polling:
  interval_ms: 5000
workspace:
  root: /home/helionaut/workspaces
hooks:
  after_create: |
    git clone --depth 1 --branch main https://github.com/helionaut/splatica-orb-test .
    git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
    git fetch origin --prune
  before_remove: |
    true
agent:
  max_concurrent_agents: 3
  max_turns: 20
codex:
  command: codex --config shell_environment_policy.inherit=all --config model_reasoning_effort=xhigh --model gpt-5.3-codex app-server
  approval_policy: never
  thread_sandbox: danger-full-access
  turn_sandbox_policy:
    type: dangerFullAccess
---

You are working on a Linear ticket `{{ issue.identifier }}` for repository `splatica-orb-test`.

{% if attempt %}
Continuation context:

- This is retry attempt #{{ attempt }} because the ticket is still in an active state.
- Resume from the current workspace state instead of restarting from scratch.
- Do not repeat already-completed investigation or validation unless needed for new code changes.
{% endif %}

Issue context:
Identifier: {{ issue.identifier }}
Title: {{ issue.title }}
Current status: {{ issue.state }}
Labels: {{ issue.labels }}
URL: {{ issue.url }}

Description:
{% if issue.description %}
{{ issue.description }}
{% else %}
No description provided.
{% endif %}

Instructions:

1. This is an unattended orchestration session. Work autonomously end-to-end unless blocked by missing auth, missing secrets, or missing required infrastructure.
2. Keep an append-only execution journal in Linear comments:
   - create a new top-level comment for every meaningful pass instead of editing an older comment in place
   - use a clear heading such as `## Codex Update`, `## Rework Update`, `## Handoff Update`, or `## Completion Update`
   - each new comment should briefly capture what changed in this pass, what evidence was checked, and what next action remains
   - if an older workpad or update comment already exists, treat it as immutable history and leave it untouched
   - when continuing an issue, reference the latest prior comment in prose if useful, but do not overwrite it
   - do not rewrite or overwrite prior progress comments unless there is a truly accidental duplicate created in the same turn
3. Use repo-local skills from `.codex/skills`.
4. Work test-first by default for behavior changes:
   - add or update tests before, or at least in the same change as, the implementation
   - do not hand off behavior changes without explicit test evidence
   - if the task is too ambiguous to write meaningful tests, clarify the acceptance criteria in a new Linear update comment before coding
5. Validate meaningful behavior before handoff.
6. Validate visual behavior before handoff or deploy whenever the task affects UI, layout, styling, responsive behavior, or user-visible interaction:
   - read the issue description and `docs/PRD.md` if it exists before judging the UI result
   - use Playwright MCP or another browser-capable tool from the current environment to open the actual built app or preview
   - capture and inspect at least one desktop screenshot and one mobile screenshot; use more screenshots when the flow has multiple important states
   - visually compare those screenshots against the issue requirements and PRD, not only against your own expectations
   - treat visual verification as required evidence, not optional polish, for UI-facing work
   - if browser tooling or screenshot capture is unavailable, do not silently skip it; record the blocker in a new Linear update comment and keep the issue out of `Human Review` unless the task is clearly non-visual
   - in every `## Handoff Update` or `## Completion Update` for UI work, summarize what desktop/mobile screenshots were checked and whether they matched the requested outcome
7. Treat local validation and remote validation separately:
   - local `npm test` / `npm run build` / `npm run check` prove the workspace head is healthy
   - GitHub PR checks prove the published review artifact is healthy
   - do not treat local green results as sufficient if the linked GitHub PR is still red, stale, or missing the latest head
8. When the workspace head is newer than the linked PR, treat publishing that head as the next required action:
   - re-check `gh auth status`, GitHub DNS, and GitHub HTTPS from the current environment before reusing any earlier blocker note
   - if those checks pass, push the current branch head, refresh or create the PR, and wait for remote checks instead of producing another offline handoff
   - only fall back to offline handoff if the current turn re-verifies that GitHub auth/network/push is still unavailable
   - do not keep repeating the same blocked note across turns without a fresh publish-path recheck
9. If the issue already has a linked branch or PR, treat the published remote branch head as the source of truth before doing more local work:
   - explicitly fetch the issue branch from origin, not just `main`
   - compare the local workspace head to the latest published branch head
   - if the local branch has diverged from the published branch or push is non-fast-forward, repair that divergence first by restacking local work onto the current remote branch before adding more changes
   - do not keep coding on a stale local branch that no longer matches the review artifact
10. Move the issue to `Human Review` only after all of the following are true:
   - implementation is complete
   - local validation and test evidence are complete
   - visual verification is complete for UI-facing work, including desktop and mobile screenshots reviewed against the issue and PRD
   - the linked PR exists and targets the correct branch
   - the linked PR reflects the current head that you want reviewed
   - required GitHub checks on that PR are green
   - add a fresh `## Handoff Update` comment immediately before the state transition that names the branch, PR, validation evidence, and what the reviewer should look at next
11. If local validation passes but the linked PR is still red, stale, or unpublished:
   - keep the issue in `Rework`
   - state clearly in a new Linear update comment that the remaining blocker is remote CI / PR freshness
   - do not describe the issue as ready for review yet
12. Treat `Rework` as a concrete debugging lane, not just a status:
   - at the start of every `Rework` turn, fetch the latest issue comments/workpad plus linked PR/check state before changing code
   - explicitly fetch the linked remote branch head as part of that refresh; a default `git fetch origin` that only updates `main` is not sufficient
   - identify the current blocker in explicit terms: failing check, stale PR head, merge conflict, missing validation, or missing publish step
   - if the issue was moved to `Rework` without a concrete blocker comment, derive that blocker from the PR/check facts and write it into a new Linear update comment before proceeding
   - do not rely on the state name alone as your instruction
13. Leave a useful trace in Linear on every meaningful `Rework` pass:
   - say what blocker you addressed
   - say what next action remains
   - say whether the branch was published and whether remote CI changed
   - if the workspace diverged from the published branch, say that explicitly and record how you repaired it
   - if nothing changed, say that explicitly instead of only bumping status
14. Prefer additive history over mutable history:
   - when in doubt, create a new concise comment rather than editing an older one
   - progress visibility in Linear should make the sequence of passes obvious to a human reader
   - historical workpad comments are immutable; never patch them in place during a later turn
15. When a ticket is actually closing:
   - before moving an issue to `Done`, add a fresh `## Completion Update` comment
   - that completion comment must include the merged PR number when available, the relevant `main` commit SHA when available, deploy result, and the live URL when available
   - for UI work, the completion comment must also say what desktop/mobile screenshots were checked before release and whether they matched the requested outcome
   - do not let a status flip to `Done` be the only visible sign that the work finished

Repo metadata:

- GitHub repo: `https://github.com/helionaut/splatica-orb-test`
- Local repo root: `/home/helionaut/src/projects/splatica-orb-test`
- Symphony workspace root: `/home/helionaut/workspaces`

Default flow:

- `Todo` -> move to `In Progress`
- `In Progress` -> implement and validate
- `Rework` -> address review feedback
- `Merging` -> land the approved PR
- `Done` -> stop
