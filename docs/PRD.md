# Product Requirements Document: splatica-orb-test

Status: Draft
Issue: HEL-42
Last Updated: 2026-03-18

## Summary

`splatica-orb-test` is a lightweight browser prototype for validating whether a
single "orb" interaction and visual treatment is compelling enough to justify a
larger product investment. The first release is intentionally narrow: one
focused experience, no accounts, no backend, and no production hardening beyond
what is needed for fast internal evaluation.

## Assumptions

- The repository currently contains only bootstrap workflow files and no prior
  product brief or implementation.
- The project name implies a small, shareable experiment centered on a single
  orb interaction in the browser.
- Until stronger product context exists, the primary audience is internal
  product, design, and engineering stakeholders plus a small set of trusted
  pilot testers.

## Target Users

- Product and design stakeholders who need a concrete prototype to evaluate the
  concept.
- Frontend engineers who need a crisp baseline scope before building.
- Trusted pilot testers who can give fast feedback on clarity, delight, and
  responsiveness.

## User Problem

The team currently has no shared definition of what `splatica-orb-test` is
meant to prove. Without a narrow first-release target, implementation can drift
into either an underspecified visual demo or an overbuilt application. The
first users need a simple, shareable prototype that makes the core orb
interaction immediately understandable and testable.

## Goals

- Establish a single, testable first-release scope for the orb experience.
- Make the core visual and interaction idea visible within seconds of page
  load.
- Gather enough feedback to decide whether to continue investing beyond a
  prototype.

## Non-Goals

- User accounts, authentication, profiles, or saved state.
- Backend services, databases, or multi-user collaboration.
- Multiple scenes, content feeds, or a generalized editor.
- Monetization, production analytics, or launch-readiness hardening.
- Broad browser certification beyond a defined modern desktop and mobile
  baseline.

## First Release Scope

- A single page or screen.
- One primary orb element as the focal point.
- A small set of direct interactions, such as hover, tap, drag, or their
  equivalent, with immediate visual response.
- A stable default state so testers can repeatedly evaluate the same
  experience.
- Lightweight instructions or framing so a first-time tester knows what to try.

## Success Metrics

- Comprehension: at least 80% of pilot testers can describe the primary orb
  interaction or value after a first session without a live walkthrough.
- Engagement: at least 60% of pilot testers voluntarily perform more than one
  interaction during the first session.
- Performance: the initial experience becomes interactive in under 2 seconds on
  a modern laptop and a current mobile device on a normal connection.
- Stability: no critical rendering failures or blocking console errors occur
  during the pilot review flow.
- Decision quality: product, design, and engineering can make a clear go or
  no-go decision on the next investment step within one review cycle.

## Acceptance Criteria for First Release

- A reviewer can open the prototype from a documented local or hosted URL
  without logging in.
- The initial screen presents a clearly visible orb within the primary viewport
  on both desktop and mobile widths.
- The orb responds to at least one intentional user action with an obvious
  visual change.
- The experience provides enough context that a first-time tester knows the
  expected action without external coaching.
- The prototype can be reset or reloaded into a known starting state for
  repeated evaluation.
- Basic run instructions live in the repository so another engineer can
  reproduce the experience.
- The team has a defined way to collect structured pilot feedback against the
  success metrics above.

## Open Questions

- What exact orb behavior should count as the core interaction?
- Should the first pilot stay internal, or include a small external cohort?
- Does "splatica" imply a specific brand or art direction beyond the orb motif?
