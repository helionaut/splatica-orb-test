#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import re


def rewrite_function_block(
    text: str,
    *,
    signature: str,
    next_signature: str,
    rewriter,
) -> str:
    start = text.find(signature)
    if start == -1:
        raise ValueError(f"Expected function signature not found: {signature}")
    end = text.find(next_signature, start)
    if end == -1:
        raise ValueError(f"Expected following function signature not found: {next_signature}")
    block = text[start:end]
    rewritten = rewriter(block)
    return text[:start] + rewritten + text[end:]


def normalize_save_trajectory_euroc(block: str) -> str:
    block, count = re.subn(
        r'int numMaxKFs = 0;\n    Map\* pBiggerMap(?: = nullptr)?;\n'
        r'    std::cout << "There are " << std::to_string\(vpMaps.size\(\)\) << " maps in the atlas" << std::endl;\n',
        'int numMaxKFs = 0;\n    Map* pBiggerMap = nullptr;\n'
        '    std::cout << "There are " << std::to_string(vpMaps.size()) << " maps in the atlas" << std::endl;\n',
        block,
        count=1,
    )
    if count == 0:
        raise ValueError("Failed to normalize SaveTrajectoryEuRoC map initialization")

    block, count = re.subn(
        r'(    for\(Map\* pMap :vpMaps\)\n'
        r'    \{\n'
        r'.*?'
        r'    \}\n)'
        r'(?:\n    if\(!pBiggerMap \|\| numMaxKFs == 0\)\n'
        r'    \{\n'
        r'        std::cout << "No keyframes were recorded; skipping trajectory save\." << std::endl;\n'
        r'        return;\n'
        r'    \}\n)*'
        r'\n    vector<KeyFrame\*> vpKFs = pBiggerMap->GetAllKeyFrames\(\);',
        r'\1\n    if(!pBiggerMap || numMaxKFs == 0)\n'
        r'    {\n'
        r'        std::cout << "No keyframes were recorded; skipping trajectory save." << std::endl;\n'
        r'        return;\n'
        r'    }\n'
        r'\n'
        r'    vector<KeyFrame*> vpKFs = pBiggerMap->GetAllKeyFrames();',
        block,
        count=1,
        flags=re.DOTALL,
    )
    if count == 0:
        raise ValueError("Failed to normalize SaveTrajectoryEuRoC guard block")

    return block


def normalize_save_keyframe_trajectory_euroc(block: str) -> str:
    block, count = re.subn(
        r'vector<Map\*> vpMaps = mpAtlas->GetAllMaps\(\);\n'
        r'    Map\* pBiggerMap(?: = nullptr)?;\n'
        r'    int numMaxKFs = 0;\n',
        'vector<Map*> vpMaps = mpAtlas->GetAllMaps();\n'
        '    Map* pBiggerMap = nullptr;\n'
        '    int numMaxKFs = 0;\n',
        block,
        count=1,
    )
    if count == 0:
        raise ValueError(
            "Failed to normalize SaveKeyFrameTrajectoryEuRoC map initialization"
        )

    block, count = re.subn(
        r'(    for\(Map\* pMap :vpMaps\)\n'
        r'    \{\n'
        r'.*?'
        r'    \}\n)'
        r'(?:\n    if\(!pBiggerMap\)\n'
        r'    \{\n'
        r'        std::cout << "There is not a map!!" << std::endl;\n'
        r'        return;\n'
        r'    \}\n'
        r'|\n    if\(!pBiggerMap \|\| numMaxKFs == 0\)\n'
        r'    \{\n'
        r'        std::cout << "No keyframes were recorded; skipping keyframe trajectory save\." << std::endl;\n'
        r'        return;\n'
        r'    \}\n)*'
        r'\n    vector<KeyFrame\*> vpKFs = pBiggerMap->GetAllKeyFrames\(\);',
        r'\1\n    if(!pBiggerMap || numMaxKFs == 0)\n'
        r'    {\n'
        r'        std::cout << "No keyframes were recorded; skipping keyframe trajectory save." << std::endl;\n'
        r'        return;\n'
        r'    }\n'
        r'\n'
        r'    vector<KeyFrame*> vpKFs = pBiggerMap->GetAllKeyFrames();',
        block,
        count=1,
        flags=re.DOTALL,
    )
    if count == 0:
        raise ValueError("Failed to normalize SaveKeyFrameTrajectoryEuRoC guard block")

    return block


def patch_system_cc(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = rewrite_function_block(
        original,
        signature="void System::SaveTrajectoryEuRoC(const string &filename)\n{",
        next_signature="\nvoid System::SaveTrajectoryEuRoC(const string &filename, Map* pMap)\n{",
        rewriter=normalize_save_trajectory_euroc,
    )
    updated = rewrite_function_block(
        updated,
        signature="void System::SaveKeyFrameTrajectoryEuRoC(const string &filename)\n{",
        next_signature="\nvoid System::SaveKeyFrameTrajectoryEuRoC(const string &filename, Map* pMap)\n{",
        rewriter=normalize_save_keyframe_trajectory_euroc,
    )

    if updated == original:
        return False

    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout-dir", required=True)
    args = parser.parse_args()

    checkout_dir = Path(args.checkout_dir).resolve()
    system_cc = checkout_dir / "src/System.cc"
    if not system_cc.exists():
        raise SystemExit(f"Missing ORB-SLAM3 source file: {system_cc}")

    changed = patch_system_cc(system_cc)
    if changed:
        print(f"Patched ORB-SLAM3 trajectory guards in {system_cc}")
    else:
        print(f"ORB-SLAM3 trajectory guards already present in {system_cc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
