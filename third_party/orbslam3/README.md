# ORB-SLAM3 baseline checkout

This directory is reserved for the pinned ORB-SLAM3 baseline or maintained
fork chosen for the evaluation lane.

`HEL-51` pins the first reproducible baseline to the official
`UZ-SLAMLab/ORB_SLAM3` repository at tag `v1.0-release`, commit
`0df83dde1c85c7ab91a0d47de7a29685d046f637`.

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
