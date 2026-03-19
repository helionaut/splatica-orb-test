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


def normalize_shutdown(block: str) -> str:
    block, count = re.subn(
        r'    mpLocalMapper->RequestFinish\(\);\n'
        r'    mpLoopCloser->RequestFinish\(\);\n'
        r'    /\*if\(mpViewer\)\n'
        r'    \{\n'
        r'        mpViewer->RequestFinish\(\);\n'
        r'        while\(!mpViewer->isFinished\(\)\)\n'
        r'            usleep\(5000\);\n'
        r'    \}\*/\n'
        r'\n'
        r'    // Wait until all thread have effectively stopped\n'
        r'    /\*while\(!mpLocalMapper->isFinished\(\) \|\| !mpLoopCloser->isFinished\(\) \|\| mpLoopCloser->isRunningGBA\(\)\)\n'
        r'    \{\n'
        r'        if\(!mpLocalMapper->isFinished\(\)\)\n'
        r'            cout << "mpLocalMapper is not finished" << endl;\*/\n'
        r'        /\*if\(!mpLoopCloser->isFinished\(\)\)\n'
        r'            cout << "mpLoopCloser is not finished" << endl;\n'
        r'        if\(mpLoopCloser->isRunningGBA\(\)\)\{\n'
        r'            cout << "mpLoopCloser is running GBA" << endl;\n'
        r'            cout << "break anyway\.\.\." << endl;\n'
        r'            break;\n'
        r'        \}\*/\n'
        r'        /\*usleep\(5000\);\n'
        r'    \}\*/\n',
        '    mpLocalMapper->RequestFinish();\n'
        '    mpLoopCloser->RequestFinish();\n'
        '    /*if(mpViewer)\n'
        '    {\n'
        '        mpViewer->RequestFinish();\n'
        '        while(!mpViewer->isFinished())\n'
        '            usleep(5000);\n'
        '    }*/\n'
        '\n'
        '    int shutdown_wait_iterations = 0;\n'
        '    while(!mpLocalMapper->isFinished() || !mpLoopCloser->isFinished() || mpLoopCloser->isRunningGBA())\n'
        '    {\n'
        '        if(shutdown_wait_iterations == 0)\n'
        '            cout << "Waiting for ORB-SLAM3 worker shutdown before trajectory save..." << endl;\n'
        '        if(shutdown_wait_iterations >= 6000)\n'
        '        {\n'
        '            cout << "Shutdown wait reached 30000 ms; continuing with current worker state." << endl;\n'
        '            break;\n'
        '        }\n'
        '        usleep(5000);\n'
        '        shutdown_wait_iterations++;\n'
        '    }\n'
        '\n'
        '    cout << "Shutdown worker state before save: local_mapping_finished="\n'
        '         << mpLocalMapper->isFinished()\n'
        '         << ", loop_closing_finished=" << mpLoopCloser->isFinished()\n'
        '         << ", loop_closing_running_gba=" << mpLoopCloser->isRunningGBA()\n'
        '         << ", wait_iterations=" << shutdown_wait_iterations << endl;\n',
        block,
        count=1,
    )
    if count == 0:
        if "Waiting for ORB-SLAM3 worker shutdown before trajectory save..." in block:
            return block
        raise ValueError("Failed to normalize Shutdown wait block")

    return block


def patch_system_cc(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = rewrite_function_block(
        original,
        signature="void System::Shutdown()\n{",
        next_signature="\nbool System::isShutDown()",
        rewriter=normalize_shutdown,
    )
    updated = rewrite_function_block(
        updated,
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
