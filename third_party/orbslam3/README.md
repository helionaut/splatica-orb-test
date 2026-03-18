# ORB-SLAM3 baseline checkout

This directory is reserved for the pinned ORB-SLAM3 baseline or maintained
fork chosen for the evaluation lane.

`HEL-48` selects the working baseline as the official
`UZ-SLAMLab/ORB_SLAM3` repository on `master`, pinned to commit
`4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`.

At the time of selection, that `master` pin is only two documentation commits
ahead of `v1.0-release`, so the executable code path remains effectively the
same while the repo now follows the explicit upstream reference line requested
for later tuning work.

Fetch that checkout locally with:

```bash
./scripts/fetch_orbslam3_baseline.sh
./scripts/build_orbslam3_baseline.sh
```

The expected monocular fisheye executable and vocabulary paths under that
checkout are:

- `third_party/orbslam3/upstream/Examples/Monocular/mono_tum_vi`
- `third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt`

The checkout itself stays git-ignored because the repo pins the source commit
and fetch command, not a vendored copy.
