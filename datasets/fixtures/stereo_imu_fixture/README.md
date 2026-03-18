# Stereo + IMU fixture

This fixture exists to validate the HEL-46 import and normalization contract
from a clean checkout.

The `raw/source/**/*.png` files are tiny synthetic placeholders, not image
quality fixtures for ORB-SLAM3 itself. They are only meant to prove that the
normalization command copies timestamp-indexed stereo files into the canonical
output layout and rejects unsupported path shapes.
