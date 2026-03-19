# RGB-D TUM baseline report: tum_rgbd_fr1_xyz

## Result

- Final exit code: `2`
- Raw process exit code: `134`
- Known-good baseline verdict: `not_useful`
- Verdict reason: The run did not finish with the full non-empty trajectory evidence required for a known-good baseline.

## Run Metadata

- Producing repo commit: `70f1990d869f7a5b26080a9f614b00fd00f2649f`
- Manifest: `manifests/tum_rgbd_fr1_xyz_sanity.json`
- Launch script: `scripts/run_orbslam3_sequence.sh`
- Command: `/usr/bin/xvfb-run -a /home/helionaut/workspaces/HEL-64/third_party/orbslam3/upstream/Examples/RGB-D/rgbd_tum /home/helionaut/workspaces/HEL-64/third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt /home/helionaut/workspaces/HEL-64/third_party/orbslam3/upstream/Examples/RGB-D/TUM1.yaml /home/helionaut/workspaces/HEL-64/datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz /home/helionaut/workspaces/HEL-64/third_party/orbslam3/upstream/Examples/RGB-D/associations/fr1_xyz.txt`
- ORB-SLAM3 baseline: `https://github.com/UZ-SLAMLab/ORB_SLAM3` @ `4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4`
- Executable: `third_party/orbslam3/upstream/Examples/RGB-D/rgbd_tum`
- Vocabulary: `third_party/orbslam3/upstream/Vocabulary/ORBvoc.txt`
- Settings bundle: `third_party/orbslam3/upstream/Examples/RGB-D/TUM1.yaml`
- Dataset root: `datasets/public/tum_rgbd/rgbd_dataset_freiburg1_xyz`
- Dataset name: `rgbd_dataset_freiburg1_xyz`
- Association file: `third_party/orbslam3/upstream/Examples/RGB-D/associations/fr1_xyz.txt`
- Associations loaded: `792`
- Diagnostic toggles: `{"disable_viewer": false, "max_frames": null, "skip_frame_trajectory_save": false, "skip_keyframe_trajectory_save": false}`

## Summary Metrics

- Camera trajectory points: `0`
- Keyframe trajectory points: `0`
- Camera / association coverage: `0.0%`
- Keyframe / association coverage: `0.0%`
- Camera path length (m): `0.000`
- Camera displacement (m): `0.000`
- Camera timestamp span (s): `0.000`
- Keyframe path length (m): `0.000`
- Keyframe displacement (m): `0.000`
- Keyframe timestamp span (s): `0.000`
- Camera x/y/z ranges: `x=n/a..n/a`, `y=n/a..n/a`, `z=n/a..n/a`

## Generated Artifacts

- Camera Trajectory: `build/tum_rgbd_fr1_xyz/trajectory/CameraTrajectory.txt` (exists: `False`, size: `0` bytes, sha256: `None`)
- Keyframe Trajectory: `build/tum_rgbd_fr1_xyz/trajectory/KeyFrameTrajectory.txt` (exists: `False`, size: `0` bytes, sha256: `None`)
- Log: `logs/out/tum_rgbd_fr1_xyz.log` (exists: `True`, size: `3132` bytes, sha256: `569a475bfae0ef2c0b9e441f9968234cd9dbbf17574fcdfe47cb0f259a409311`)
- Markdown Report: `reports/out/tum_rgbd_fr1_xyz.md` (exists: `False`, size: `0` bytes, sha256: `None`)
- Summary Json: `reports/out/tum_rgbd_fr1_xyz_summary.json` (exists: `True`, size: `5628` bytes, sha256: `36ffb4144dc25fc9f62f7ba87b2be6b958f645c63a23dc5e824700c8e187f667`)
- Trajectory Plot: `reports/out/tum_rgbd_fr1_xyz_trajectory.svg` (exists: `True`, size: `381` bytes, sha256: `fc0bbea49d17cf0ba2aae797689aa1e6b18920efc5edfe92fea4b4f02c2ae6b3`)
- Visual Report: `reports/out/tum_rgbd_fr1_xyz.html` (exists: `False`, size: `0` bytes, sha256: `None`)

## Result Details

- Raw process exit code: 134
- Diagnostic toggles: max_frames=None, disable_viewer=False, skip_frame_save=False, skip_keyframe_save=False
- Camera trajectory: missing at build/tum_rgbd_fr1_xyz/trajectory/CameraTrajectory.txt
- Keyframe trajectory: missing at build/tum_rgbd_fr1_xyz/trajectory/KeyFrameTrajectory.txt
- Camera trajectory points: 0
- Keyframe trajectory points: 0
- ORB-SLAM3 did not finish with both non-empty trajectory outputs.

## Notes

Public clean-room sanity lane for upstream ORB-SLAM3 using the official TUM RGB-D fr1/xyz pinhole sequence, the upstream TUM1.yaml settings bundle, and the upstream fr1_xyz association file.
