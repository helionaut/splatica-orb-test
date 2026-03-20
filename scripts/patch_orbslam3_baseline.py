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


def normalize_mono_tum_vi_main(block: str) -> str:
    block, count = re.subn(
        r'    double t_resize = 0\.f;\n'
        r'    double t_track = 0\.f;\n'
        r'\n'
        r'    int proccIm = 0;\n',
        '    double t_resize = 0.f;\n'
        '    double t_track = 0.f;\n'
        '\n'
        '    const char* hel68_max_frames_env = std::getenv("ORB_SLAM3_HEL68_MAX_FRAMES");\n'
        '    int hel68_max_frames = -1;\n'
        '    if(hel68_max_frames_env)\n'
        '    {\n'
        '        hel68_max_frames = std::atoi(hel68_max_frames_env);\n'
        '        cout << "HEL-68 diagnostic: mono_tum_vi max frames=" << hel68_max_frames << endl;\n'
        '    }\n'
        '\n'
        '    int proccIm = 0;\n'
        '    int hel68_processed_frames = 0;\n'
        '    bool hel68_stop_requested = false;\n',
        block,
        count=1,
    )
    if count == 0 and 'HEL-68 diagnostic: mono_tum_vi max frames=' not in block:
        raise ValueError("Failed to normalize mono_tum_vi max-frame configuration")

    block, count = re.subn(
        r'            // Pass the image to the SLAM system\n'
        r'            SLAM.TrackMonocular\(im,tframe\); // TODO change to monocular_inertial\n',
        '            // Pass the image to the SLAM system\n'
        '            cout << "HEL-68 diagnostic: frame " << hel68_processed_frames\n'
        '                 << " TrackMonocular start timestamp=" << tframe << endl;\n'
        '            SLAM.TrackMonocular(im,tframe); // TODO change to monocular_inertial\n'
        '            cout << "HEL-68 diagnostic: frame " << hel68_processed_frames\n'
        '                 << " TrackMonocular completed" << endl;\n',
        block,
        count=1,
    )
    if count == 0 and 'HEL-68 diagnostic: frame " << hel68_processed_frames' not in block:
        raise ValueError("Failed to normalize mono_tum_vi TrackMonocular diagnostics")

    block, count = re.subn(
        r'            vTimesTrack\[ni\]=ttrack;\n'
        r'\n'
        r'            // Wait to load the next frame\n',
        '            vTimesTrack[hel68_processed_frames]=ttrack;\n'
        '            hel68_processed_frames++;\n'
        '\n'
        '            if(hel68_max_frames > 0 && hel68_processed_frames >= hel68_max_frames)\n'
        '            {\n'
        '                cout << "HEL-68 diagnostic: stopping after " << hel68_processed_frames\n'
        '                     << " frames due to ORB_SLAM3_HEL68_MAX_FRAMES" << endl;\n'
        '                hel68_stop_requested = true;\n'
        '                break;\n'
        '            }\n'
        '\n'
        '            // Wait to load the next frame\n',
        block,
        count=1,
    )
    if count == 0 and 'ORB_SLAM3_HEL68_MAX_FRAMES' not in block:
        raise ValueError("Failed to normalize mono_tum_vi max-frame stop boundary")

    if 'if(hel68_stop_requested)' not in block:
        block, count = re.subn(
            r'        if\(seq < num_seq - 1\)\n',
            '        if(hel68_stop_requested)\n'
            '        {\n'
            '            break;\n'
            '        }\n'
            '\n'
            '        if(seq < num_seq - 1)\n',
            block,
            count=1,
        )
        if count == 0:
            raise ValueError("Failed to normalize mono_tum_vi early-stop outer loop")

    original_sequence = (
        '    // Stop all threads\n'
        '    SLAM.Shutdown();\n'
        '\n'
        '\n'
        '    // Tracking time statistics\n'
        '\n'
        '    // Save camera trajectory\n'
        '\n'
        '    if (bFileName)\n'
        '    {\n'
        '        const string kf_file =  "kf_" + string(argv[argc-1]) + ".txt";\n'
        '        const string f_file =  "f_" + string(argv[argc-1]) + ".txt";\n'
        '        SLAM.SaveTrajectoryEuRoC(f_file);\n'
        '        SLAM.SaveKeyFrameTrajectoryEuRoC(kf_file);\n'
        '    }\n'
        '    else\n'
        '    {\n'
        '        SLAM.SaveTrajectoryEuRoC("CameraTrajectory.txt");\n'
        '        SLAM.SaveKeyFrameTrajectoryEuRoC("KeyFrameTrajectory.txt");\n'
        '    }\n'
    )
    replacement_sequence = (
        '    // Stop all threads\n'
        '    cout << "HEL-63 diagnostic: entering SLAM shutdown" << endl;\n'
        '    SLAM.Shutdown();\n'
        '    cout << "HEL-63 diagnostic: SLAM shutdown completed" << endl;\n'
        '\n'
        '    const bool skip_frame_trajectory_save = std::getenv("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE") != nullptr;\n'
        '    const bool skip_keyframe_trajectory_save = std::getenv("ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE") != nullptr;\n'
        '    if(skip_frame_trajectory_save || skip_keyframe_trajectory_save)\n'
        '    {\n'
        '        cout << "HEL-63 diagnostic: save toggles frame=" << skip_frame_trajectory_save\n'
        '             << ", keyframe=" << skip_keyframe_trajectory_save << endl;\n'
        '    }\n'
        '\n'
        '    // Tracking time statistics\n'
        '\n'
        '    // Save camera trajectory\n'
        '\n'
        '    if (bFileName)\n'
        '    {\n'
        '        const string kf_file =  "kf_" + string(argv[argc-1]) + ".txt";\n'
        '        const string f_file =  "f_" + string(argv[argc-1]) + ".txt";\n'
        '        if(skip_frame_trajectory_save)\n'
        '            cout << "HEL-63 diagnostic: skipping SaveTrajectoryEuRoC for " << f_file << endl;\n'
        '        else\n'
        '        {\n'
        '            cout << "HEL-63 diagnostic: calling SaveTrajectoryEuRoC for " << f_file << endl;\n'
        '            SLAM.SaveTrajectoryEuRoC(f_file);\n'
        '            cout << "HEL-63 diagnostic: SaveTrajectoryEuRoC completed" << endl;\n'
        '        }\n'
        '        if(skip_keyframe_trajectory_save)\n'
        '            cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryEuRoC for " << kf_file << endl;\n'
        '        else\n'
        '        {\n'
        '            cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC for " << kf_file << endl;\n'
        '            SLAM.SaveKeyFrameTrajectoryEuRoC(kf_file);\n'
        '            cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed" << endl;\n'
        '        }\n'
        '    }\n'
        '    else\n'
        '    {\n'
        '        if(skip_frame_trajectory_save)\n'
        '            cout << "HEL-63 diagnostic: skipping SaveTrajectoryEuRoC for CameraTrajectory.txt" << endl;\n'
        '        else\n'
        '        {\n'
        '            cout << "HEL-63 diagnostic: calling SaveTrajectoryEuRoC for CameraTrajectory.txt" << endl;\n'
        '            SLAM.SaveTrajectoryEuRoC("CameraTrajectory.txt");\n'
        '            cout << "HEL-63 diagnostic: SaveTrajectoryEuRoC completed" << endl;\n'
        '        }\n'
        '        if(skip_keyframe_trajectory_save)\n'
        '            cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryEuRoC for KeyFrameTrajectory.txt" << endl;\n'
        '        else\n'
        '        {\n'
        '            cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC for KeyFrameTrajectory.txt" << endl;\n'
        '            SLAM.SaveKeyFrameTrajectoryEuRoC("KeyFrameTrajectory.txt");\n'
        '            cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed" << endl;\n'
        '        }\n'
        '    }\n'
    )
    block, count = re.subn(
        re.escape(original_sequence),
        lambda _: replacement_sequence,
        block,
        count=1,
    )
    if count == 0:
        if "HEL-63 diagnostic: entering SLAM shutdown" in block:
            return block
        raise ValueError("Failed to normalize mono_tum_vi save flow")

    block, count = re.subn(
        r'    sort\(vTimesTrack.begin\(\),vTimesTrack.end\(\)\);\n'
        r'    float totaltime = 0;\n'
        r'    for\(int ni=0; ni<nImages\[0\]; ni\+\+\)\n'
        r'    \{\n'
        r'        totaltime\+=vTimesTrack\[ni\];\n'
        r'    \}\n'
        r'    cout << "-------" << endl << endl;\n'
        r'    cout << "median tracking time: " << vTimesTrack\[nImages\[0\]/2\] << endl;\n'
        r'    cout << "mean tracking time: " << totaltime/proccIm << endl;\n',
        '    const int hel68_stats_count = hel68_processed_frames > 0 ? hel68_processed_frames : nImages[0];\n'
        '    sort(vTimesTrack.begin(), vTimesTrack.begin() + hel68_stats_count);\n'
        '    float totaltime = 0;\n'
        '    for(int ni=0; ni<hel68_stats_count; ni++)\n'
        '    {\n'
        '        totaltime+=vTimesTrack[ni];\n'
        '    }\n'
        '    cout << "-------" << endl << endl;\n'
        '    cout << "median tracking time: " << vTimesTrack[hel68_stats_count/2] << endl;\n'
        '    cout << "mean tracking time: " << totaltime/hel68_stats_count << endl;\n',
        block,
        count=1,
    )
    if count == 0 and 'const int hel68_stats_count =' not in block:
        raise ValueError("Failed to normalize mono_tum_vi timing statistics")

    return block


def normalize_rgbd_tum_main(block: str) -> str:
    block, count = re.subn(
        r'    // Create SLAM system\. It initializes all system threads and gets ready to process frames\.\n'
        r'    ORB_SLAM3::System SLAM\(argv\[1\],argv\[2\],ORB_SLAM3::System::RGBD,true\);\n'
        r'    float imageScale = SLAM.GetImageScale\(\);\n',
        '    const bool disable_viewer = std::getenv("ORB_SLAM3_DISABLE_VIEWER") != nullptr;\n'
        '    cout << "HEL-63 diagnostic: rgbd_tum disable_viewer=" << disable_viewer << endl;\n'
        '\n'
        '    // Create SLAM system. It initializes all system threads and gets ready to process frames.\n'
        '    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::RGBD,!disable_viewer);\n'
        '    float imageScale = SLAM.GetImageScale();\n',
        block,
        count=1,
    )
    if count == 0 and 'HEL-63 diagnostic: rgbd_tum disable_viewer=' not in block:
        raise ValueError("Failed to normalize rgbd_tum viewer toggle")

    original_sequence = (
        '    // Main loop\n'
        '    cv::Mat imRGB, imD;\n'
        '    for(int ni=0; ni<nImages; ni++)\n'
        '    {\n'
        '        // Read image and depthmap from file\n'
        '        imRGB = cv::imread(string(argv[3])+"/"+vstrImageFilenamesRGB[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);\n'
        '        imD = cv::imread(string(argv[3])+"/"+vstrImageFilenamesD[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);\n'
        '        double tframe = vTimestamps[ni];\n'
        '\n'
        '        if(imRGB.empty())\n'
        '        {\n'
        '            cerr << endl << "Failed to load image at: "\n'
        '                 << string(argv[3]) << "/" << vstrImageFilenamesRGB[ni] << endl;\n'
        '            return 1;\n'
        '        }\n'
        '\n'
        '        if(imageScale != 1.f)\n'
        '        {\n'
        '            int width = imRGB.cols * imageScale;\n'
        '            int height = imRGB.rows * imageScale;\n'
        '            cv::resize(imRGB, imRGB, cv::Size(width, height));\n'
        '            cv::resize(imD, imD, cv::Size(width, height));\n'
        '        }\n'
        '\n'
        '#ifdef COMPILEDWITHC11\n'
        '        std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();\n'
        '#else\n'
        '        std::chrono::monotonic_clock::time_point t1 = std::chrono::monotonic_clock::now();\n'
        '#endif\n'
        '\n'
        '        // Pass the image to the SLAM system\n'
        '        SLAM.TrackRGBD(imRGB,imD,tframe);\n'
        '\n'
        '#ifdef COMPILEDWITHC11\n'
        '        std::chrono::steady_clock::time_point t2 = std::chrono::steady_clock::now();\n'
        '#else\n'
        '        std::chrono::monotonic_clock::time_point t2 = std::chrono::monotonic_clock::now();\n'
        '#endif\n'
        '\n'
        '        double ttrack= std::chrono::duration_cast<std::chrono::duration<double> >(t2 - t1).count();\n'
        '\n'
        '        vTimesTrack[ni]=ttrack;\n'
        '\n'
        '        // Wait to load the next frame\n'
        '        double T=0;\n'
        '        if(ni<nImages-1)\n'
        '            T = vTimestamps[ni+1]-tframe;\n'
        '        else if(ni>0)\n'
        '            T = tframe-vTimestamps[ni-1];\n'
        '\n'
        '        if(ttrack<T)\n'
        '            usleep((T-ttrack)*1e6);\n'
        '    }\n'
        '\n'
        '    // Stop all threads\n'
        '    SLAM.Shutdown();\n'
        '\n'
        '    // Tracking time statistics\n'
        '    sort(vTimesTrack.begin(),vTimesTrack.end());\n'
        '    float totaltime = 0;\n'
        '    for(int ni=0; ni<nImages; ni++)\n'
        '    {\n'
        '        totaltime+=vTimesTrack[ni];\n'
        '    }\n'
        '    cout << "-------" << endl << endl;\n'
        '    cout << "median tracking time: " << vTimesTrack[nImages/2] << endl;\n'
        '    cout << "mean tracking time: " << totaltime/nImages << endl;\n'
        '\n'
        '    // Save camera trajectory\n'
        '    SLAM.SaveTrajectoryTUM("CameraTrajectory.txt");\n'
        '    SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");   \n'
    )
    replacement_sequence = (
        '    const char* hel63_max_frames_env = std::getenv("ORB_SLAM3_HEL63_MAX_FRAMES");\n'
        '    const bool skip_frame_trajectory_save = std::getenv("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE") != nullptr;\n'
        '    const bool skip_keyframe_trajectory_save = std::getenv("ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE") != nullptr;\n'
        '    int hel63_max_frames = -1;\n'
        '    if(hel63_max_frames_env)\n'
        '    {\n'
        '        hel63_max_frames = std::atoi(hel63_max_frames_env);\n'
        '        cout << "HEL-63 diagnostic: rgbd_tum max frames=" << hel63_max_frames << endl;\n'
        '    }\n'
        '    if(skip_frame_trajectory_save || skip_keyframe_trajectory_save)\n'
        '    {\n'
        '        cout << "HEL-63 diagnostic: save toggles frame=" << skip_frame_trajectory_save\n'
        '             << ", keyframe=" << skip_keyframe_trajectory_save << endl;\n'
        '    }\n'
        '\n'
        '    int processed_images = 0;\n'
        '\n'
        '    // Main loop\n'
        '    cv::Mat imRGB, imD;\n'
        '    for(int ni=0; ni<nImages; ni++)\n'
        '    {\n'
        '        // Read image and depthmap from file\n'
        '        imRGB = cv::imread(string(argv[3])+"/"+vstrImageFilenamesRGB[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);\n'
        '        imD = cv::imread(string(argv[3])+"/"+vstrImageFilenamesD[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);\n'
        '        double tframe = vTimestamps[ni];\n'
        '\n'
        '        if(imRGB.empty())\n'
        '        {\n'
        '            cerr << endl << "Failed to load image at: "\n'
        '                 << string(argv[3]) << "/" << vstrImageFilenamesRGB[ni] << endl;\n'
        '            return 1;\n'
        '        }\n'
        '\n'
        '        if(imageScale != 1.f)\n'
        '        {\n'
        '            int width = imRGB.cols * imageScale;\n'
        '            int height = imRGB.rows * imageScale;\n'
        '            cv::resize(imRGB, imRGB, cv::Size(width, height));\n'
        '            cv::resize(imD, imD, cv::Size(width, height));\n'
        '        }\n'
        '\n'
        '#ifdef COMPILEDWITHC11\n'
        '        std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();\n'
        '#else\n'
        '        std::chrono::monotonic_clock::time_point t1 = std::chrono::monotonic_clock::now();\n'
        '#endif\n'
        '\n'
        '        // Pass the image to the SLAM system\n'
        '        cout << "HEL-63 diagnostic: frame " << ni << " TrackRGBD start timestamp=" << tframe << endl;\n'
        '        SLAM.TrackRGBD(imRGB,imD,tframe);\n'
        '        cout << "HEL-63 diagnostic: frame " << ni << " TrackRGBD completed" << endl;\n'
        '\n'
        '#ifdef COMPILEDWITHC11\n'
        '        std::chrono::steady_clock::time_point t2 = std::chrono::steady_clock::now();\n'
        '#else\n'
        '        std::chrono::monotonic_clock::time_point t2 = std::chrono::monotonic_clock::now();\n'
        '#endif\n'
        '\n'
        '        double ttrack= std::chrono::duration_cast<std::chrono::duration<double> >(t2 - t1).count();\n'
        '\n'
        '        vTimesTrack[ni]=ttrack;\n'
        '        processed_images = ni + 1;\n'
        '\n'
        '        if(hel63_max_frames > 0 && processed_images >= hel63_max_frames)\n'
        '        {\n'
        '            cout << "HEL-63 diagnostic: stopping after " << processed_images\n'
        '                 << " frames due to ORB_SLAM3_HEL63_MAX_FRAMES" << endl;\n'
        '            break;\n'
        '        }\n'
        '\n'
        '        // Wait to load the next frame\n'
        '        double T=0;\n'
        '        if(ni<nImages-1)\n'
        '            T = vTimestamps[ni+1]-tframe;\n'
        '        else if(ni>0)\n'
        '            T = tframe-vTimestamps[ni-1];\n'
        '\n'
        '        if(ttrack<T)\n'
        '            usleep((T-ttrack)*1e6);\n'
        '    }\n'
        '\n'
        '    if(processed_images == 0)\n'
        '        processed_images = nImages;\n'
        '\n'
        '    // Stop all threads\n'
        '    cout << "HEL-63 diagnostic: entering SLAM shutdown" << endl;\n'
        '    SLAM.Shutdown();\n'
        '    cout << "HEL-63 diagnostic: SLAM shutdown completed" << endl;\n'
        '\n'
        '    // Tracking time statistics\n'
        '    sort(vTimesTrack.begin(), vTimesTrack.begin() + processed_images);\n'
        '    float totaltime = 0;\n'
        '    for(int ni=0; ni<processed_images; ni++)\n'
        '    {\n'
        '        totaltime+=vTimesTrack[ni];\n'
        '    }\n'
        '    cout << "-------" << endl << endl;\n'
        '    cout << "median tracking time: " << vTimesTrack[processed_images/2] << endl;\n'
        '    cout << "mean tracking time: " << totaltime/processed_images << endl;\n'
        '\n'
        '    // Save camera trajectory\n'
        '    if(skip_frame_trajectory_save)\n'
        '        cout << "HEL-63 diagnostic: skipping SaveTrajectoryTUM for CameraTrajectory.txt" << endl;\n'
        '    else\n'
        '    {\n'
        '        cout << "HEL-63 diagnostic: calling SaveTrajectoryTUM for CameraTrajectory.txt" << endl;\n'
        '        SLAM.SaveTrajectoryTUM("CameraTrajectory.txt");\n'
        '        cout << "HEL-63 diagnostic: SaveTrajectoryTUM completed" << endl;\n'
        '    }\n'
        '    if(skip_keyframe_trajectory_save)\n'
        '        cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryTUM for KeyFrameTrajectory.txt" << endl;\n'
        '    else\n'
        '    {\n'
        '        cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryTUM for KeyFrameTrajectory.txt" << endl;\n'
        '        SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");\n'
        '        cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryTUM completed" << endl;\n'
        '    }\n'
    )
    block, count = re.subn(
        re.escape(original_sequence),
        lambda _: replacement_sequence,
        block,
        count=1,
    )
    if count == 0:
        if "HEL-63 diagnostic: frame " in block:
            return block
        raise ValueError("Failed to normalize rgbd_tum diagnostic flow")

    return block


def patch_optimizable_types(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    updated = original
    count = 0
    for indent in ("        ", "    "):
        original_sequence = (
            f"{indent}auto projectJac = -pCamera->projectJac(xyz_trans);\n\n"
            f"{indent}_jacobianOplusXi =  projectJac * T.rotation().toRotationMatrix();\n\n"
            f"{indent}Eigen::Matrix<double,3,6> SE3deriv;\n"
            f"{indent}SE3deriv << 0.f, z,   -y, 1.f, 0.f, 0.f,\n"
            f"{indent}        -z , 0.f, x, 0.f, 1.f, 0.f,\n"
            f"{indent}        y ,  -x , 0.f, 0.f, 0.f, 1.f;\n\n"
            f"{indent}_jacobianOplusXj = projectJac * SE3deriv;\n"
        )
        replacement_sequence = (
            f"{indent}const Eigen::Matrix<double, 2, 3> project_jac =\n"
            f"{indent}    (-pCamera->projectJac(xyz_trans)).eval();\n\n"
            f"{indent}_jacobianOplusXi = project_jac * T.rotation().toRotationMatrix();\n\n"
            f"{indent}Eigen::Matrix<double,3,6> SE3deriv;\n"
            f"{indent}SE3deriv << 0.f, z,   -y, 1.f, 0.f, 0.f,\n"
            f"{indent}        -z , 0.f, x, 0.f, 1.f, 0.f,\n"
            f"{indent}        y ,  -x , 0.f, 0.f, 0.f, 1.f;\n\n"
            f"{indent}_jacobianOplusXj = project_jac * SE3deriv;\n"
        )
        updated = original.replace(original_sequence, replacement_sequence, 1)
        count = int(updated != original)
        if count:
            break
    if count == 0:
        if "const Eigen::Matrix<double, 2, 3> project_jac =" in original:
            return False
        raise ValueError(
            "Failed to normalize EdgeSE3ProjectXYZ Jacobian evaluation lifetime"
        )

    path.write_text(updated, encoding="utf-8")
    return True


def patch_cmakelists(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    marker = (
        "# HEL-67: rely on the wrapper-controlled release flags instead of\n"
        "# forcing -march=native in the fetched upstream checkout.\n"
    )
    if marker in original:
        return False

    updated, count = re.subn(
        r'set\(CMAKE_C_FLAGS_RELEASE "\$\{CMAKE_C_FLAGS_RELEASE\} -march=native"\)\n'
        r'set\(CMAKE_CXX_FLAGS_RELEASE "\$\{CMAKE_CXX_FLAGS_RELEASE\} -march=native"\)\n',
        marker,
        original,
        count=1,
    )
    if count == 0:
        raise ValueError("Failed to normalize upstream -march=native release flags")

    path.write_text(updated, encoding="utf-8")
    return True


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


def patch_mono_tum_vi(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    if "#include <cstdlib>\n" in original:
        updated = original
    else:
        updated, count = re.subn(
            r'#include <unistd\.h>\n',
            '#include <unistd.h>\n#include <cstdlib>\n',
            original,
            count=1,
        )
        if count == 0:
            raise ValueError("Failed to normalize mono_tum_vi includes")

    updated = rewrite_function_block(
        updated,
        signature="int main(int argc, char **argv)\n{",
        next_signature="\nvoid LoadImages(",
        rewriter=normalize_mono_tum_vi_main,
    )

    if updated == original:
        return False

    path.write_text(updated, encoding="utf-8")
    return True


def patch_rgbd_tum(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    if "#include<cstdlib>\n" in original:
        updated = original
    else:
        updated, count = re.subn(
            r'#include<chrono>\n',
            '#include<chrono>\n#include<cstdlib>\n',
            original,
            count=1,
        )
        if count == 0:
            raise ValueError("Failed to normalize rgbd_tum includes")

    updated = rewrite_function_block(
        updated,
        signature="int main(int argc, char **argv)\n{",
        next_signature="\nvoid LoadImages(",
        rewriter=normalize_rgbd_tum_main,
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
    cmake_lists = checkout_dir / "CMakeLists.txt"
    system_cc = checkout_dir / "src/System.cc"
    optimizable_types_cc = checkout_dir / "src/OptimizableTypes.cpp"
    mono_tum_vi_cc = checkout_dir / "Examples/Monocular/mono_tum_vi.cc"
    rgbd_tum_cc = checkout_dir / "Examples/RGB-D/rgbd_tum.cc"
    if not cmake_lists.exists():
        raise SystemExit(f"Missing ORB-SLAM3 source file: {cmake_lists}")
    if not system_cc.exists():
        raise SystemExit(f"Missing ORB-SLAM3 source file: {system_cc}")
    if not optimizable_types_cc.exists():
        raise SystemExit(f"Missing ORB-SLAM3 source file: {optimizable_types_cc}")
    if not mono_tum_vi_cc.exists():
        raise SystemExit(f"Missing ORB-SLAM3 source file: {mono_tum_vi_cc}")
    if not rgbd_tum_cc.exists():
        raise SystemExit(f"Missing ORB-SLAM3 source file: {rgbd_tum_cc}")

    cmake_changed = patch_cmakelists(cmake_lists)
    changed = patch_system_cc(system_cc)
    optimizable_types_changed = patch_optimizable_types(optimizable_types_cc)
    mono_changed = patch_mono_tum_vi(mono_tum_vi_cc)
    rgbd_changed = patch_rgbd_tum(rgbd_tum_cc)
    if (
        cmake_changed
        or changed
        or optimizable_types_changed
        or mono_changed
        or rgbd_changed
    ):
        print(
            "Patched ORB-SLAM3 release-flag/trajectory guards plus the "
            "EdgeSE3ProjectXYZ Jacobian lifetime fix in "
            f"{cmake_lists}, {system_cc}, {optimizable_types_cc}, "
            f"{mono_tum_vi_cc}, and {rgbd_tum_cc}"
        )
    else:
        print(
            "ORB-SLAM3 release-flag/trajectory guards and the "
            "EdgeSE3ProjectXYZ Jacobian lifetime fix already present in "
            f"{cmake_lists}, {system_cc}, {optimizable_types_cc}, "
            f"{mono_tum_vi_cc}, and {rgbd_tum_cc}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
