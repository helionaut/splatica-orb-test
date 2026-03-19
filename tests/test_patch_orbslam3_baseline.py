from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts/patch_orbslam3_baseline.py"
SPEC = importlib.util.spec_from_file_location("patch_orbslam3_baseline", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
PATCH_HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCH_HELPER)


class PatchOrbslam3BaselineTests(unittest.TestCase):
    def test_rewrites_shutdown_to_wait_for_worker_threads(self) -> None:
        source = """void System::Shutdown()
{
    {
        unique_lock<mutex> lock(mMutexReset);
        mbShutDown = true;
    }

    cout << "Shutdown" << endl;

    mpLocalMapper->RequestFinish();
    mpLoopCloser->RequestFinish();
    /*if(mpViewer)
    {
        mpViewer->RequestFinish();
        while(!mpViewer->isFinished())
            usleep(5000);
    }*/

    // Wait until all thread have effectively stopped
    /*while(!mpLocalMapper->isFinished() || !mpLoopCloser->isFinished() || mpLoopCloser->isRunningGBA())
    {
        if(!mpLocalMapper->isFinished())
            cout << "mpLocalMapper is not finished" << endl;*/
        /*if(!mpLoopCloser->isFinished())
            cout << "mpLoopCloser is not finished" << endl;
        if(mpLoopCloser->isRunningGBA()){
            cout << "mpLoopCloser is running GBA" << endl;
            cout << "break anyway..." << endl;
            break;
        }*/
        /*usleep(5000);
    }*/
}
bool System::isShutDown() { return false; }
"""

        rewritten = PATCH_HELPER.rewrite_function_block(
            source,
            signature="void System::Shutdown()\n{",
            next_signature="\nbool System::isShutDown()",
            rewriter=PATCH_HELPER.normalize_shutdown,
        )

        self.assertIn(
            "Waiting for ORB-SLAM3 worker shutdown before trajectory save...",
            rewritten,
        )
        self.assertIn(
            "Shutdown wait reached 30000 ms; continuing with current worker state.",
            rewritten,
        )
        self.assertIn("shutdown_wait_iterations >= 6000", rewritten)
        self.assertIn("Shutdown worker state before save: local_mapping_finished=", rewritten)
        self.assertNotIn("// Wait until all thread have effectively stopped", rewritten)

    def test_shutdown_rewrite_is_idempotent(self) -> None:
        shutdown_block = """void System::Shutdown()
{
    {
        unique_lock<mutex> lock(mMutexReset);
        mbShutDown = true;
    }

    cout << "Shutdown" << endl;

    mpLocalMapper->RequestFinish();
    mpLoopCloser->RequestFinish();
    /*if(mpViewer)
    {
        mpViewer->RequestFinish();
        while(!mpViewer->isFinished())
            usleep(5000);
    }*/

    int shutdown_wait_iterations = 0;
    while(!mpLocalMapper->isFinished() || !mpLoopCloser->isFinished() || mpLoopCloser->isRunningGBA())
    {
        if(shutdown_wait_iterations == 0)
            cout << "Waiting for ORB-SLAM3 worker shutdown before trajectory save..." << endl;
        if(shutdown_wait_iterations >= 6000)
        {
            cout << "Shutdown wait reached 30000 ms; continuing with current worker state." << endl;
            break;
        }
        usleep(5000);
        shutdown_wait_iterations++;
    }

    cout << "Shutdown worker state before save: local_mapping_finished="
         << mpLocalMapper->isFinished()
         << ", loop_closing_finished=" << mpLoopCloser->isFinished()
         << ", loop_closing_running_gba=" << mpLoopCloser->isRunningGBA()
         << ", wait_iterations=" << shutdown_wait_iterations << endl;
}
"""

        self.assertEqual(
            PATCH_HELPER.normalize_shutdown(shutdown_block),
            shutdown_block,
        )

    def test_rewrites_mono_tum_vi_main_with_save_phase_diagnostics(self) -> None:
        source = """#include <unistd.h>

int main(int argc, char **argv)
{
    bool bFileName = true;

    // Stop all threads
    SLAM.Shutdown();


    // Tracking time statistics

    // Save camera trajectory

    if (bFileName)
    {
        const string kf_file =  "kf_" + string(argv[argc-1]) + ".txt";
        const string f_file =  "f_" + string(argv[argc-1]) + ".txt";
        SLAM.SaveTrajectoryEuRoC(f_file);
        SLAM.SaveKeyFrameTrajectoryEuRoC(kf_file);
    }
    else
    {
        SLAM.SaveTrajectoryEuRoC("CameraTrajectory.txt");
        SLAM.SaveKeyFrameTrajectoryEuRoC("KeyFrameTrajectory.txt");
    }

    return 0;
}

void LoadImages() {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "mono_tum_vi.cc"
            source_path.write_text(source, encoding="utf-8")
            changed = PATCH_HELPER.patch_mono_tum_vi(source_path)
            rewritten = source_path.read_text(encoding="utf-8")

        self.assertTrue(changed)
        self.assertIn("#include <cstdlib>", rewritten)
        self.assertIn('std::getenv("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE")', rewritten)
        self.assertIn("HEL-63 diagnostic: entering SLAM shutdown", rewritten)
        self.assertIn("HEL-63 diagnostic: SaveTrajectoryEuRoC completed", rewritten)
        self.assertIn(
            "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed",
            rewritten,
        )

    def test_mono_tum_vi_rewrite_is_idempotent(self) -> None:
        source = """#include <unistd.h>
#include <cstdlib>

int main(int argc, char **argv)
{
    bool bFileName = true;

    // Stop all threads
    cout << "HEL-63 diagnostic: entering SLAM shutdown" << endl;
    SLAM.Shutdown();
    cout << "HEL-63 diagnostic: SLAM shutdown completed" << endl;

    const bool skip_frame_trajectory_save = std::getenv("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE") != nullptr;
    const bool skip_keyframe_trajectory_save = std::getenv("ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE") != nullptr;
    if(skip_frame_trajectory_save || skip_keyframe_trajectory_save)
    {
        cout << "HEL-63 diagnostic: save toggles frame=" << skip_frame_trajectory_save
             << ", keyframe=" << skip_keyframe_trajectory_save << endl;
    }

    // Tracking time statistics

    // Save camera trajectory

    if (bFileName)
    {
        const string kf_file =  "kf_" + string(argv[argc-1]) + ".txt";
        const string f_file =  "f_" + string(argv[argc-1]) + ".txt";
        if(skip_frame_trajectory_save)
            cout << "HEL-63 diagnostic: skipping SaveTrajectoryEuRoC for " << f_file << endl;
        else
        {
            cout << "HEL-63 diagnostic: calling SaveTrajectoryEuRoC for " << f_file << endl;
            SLAM.SaveTrajectoryEuRoC(f_file);
            cout << "HEL-63 diagnostic: SaveTrajectoryEuRoC completed" << endl;
        }
        if(skip_keyframe_trajectory_save)
            cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryEuRoC for " << kf_file << endl;
        else
        {
            cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC for " << kf_file << endl;
            SLAM.SaveKeyFrameTrajectoryEuRoC(kf_file);
            cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed" << endl;
        }
    }
    else
    {
        if(skip_frame_trajectory_save)
            cout << "HEL-63 diagnostic: skipping SaveTrajectoryEuRoC for CameraTrajectory.txt" << endl;
        else
        {
            cout << "HEL-63 diagnostic: calling SaveTrajectoryEuRoC for CameraTrajectory.txt" << endl;
            SLAM.SaveTrajectoryEuRoC("CameraTrajectory.txt");
            cout << "HEL-63 diagnostic: SaveTrajectoryEuRoC completed" << endl;
        }
        if(skip_keyframe_trajectory_save)
            cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryEuRoC for KeyFrameTrajectory.txt" << endl;
        else
        {
            cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC for KeyFrameTrajectory.txt" << endl;
            SLAM.SaveKeyFrameTrajectoryEuRoC("KeyFrameTrajectory.txt");
            cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed" << endl;
        }
    }

    return 0;
}

void LoadImages() {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "mono_tum_vi.cc"
            source_path.write_text(source, encoding="utf-8")
            self.assertFalse(PATCH_HELPER.patch_mono_tum_vi(source_path))
            self.assertEqual(source_path.read_text(encoding="utf-8"), source)

    def test_rewrites_rgbd_tum_main_with_tracking_diagnostics(self) -> None:
        source = """#include<iostream>
#include<algorithm>
#include<fstream>
#include<chrono>

void LoadImages();

int main(int argc, char **argv)
{
    int nImages = 2;
    vector<float> vTimesTrack;
    vTimesTrack.resize(nImages);

    // Create SLAM system. It initializes all system threads and gets ready to process frames.
    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::RGBD,true);
    float imageScale = SLAM.GetImageScale();

    // Main loop
    cv::Mat imRGB, imD;
    for(int ni=0; ni<nImages; ni++)
    {
        // Read image and depthmap from file
        imRGB = cv::imread(string(argv[3])+"/"+vstrImageFilenamesRGB[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        imD = cv::imread(string(argv[3])+"/"+vstrImageFilenamesD[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        double tframe = vTimestamps[ni];

        if(imRGB.empty())
        {
            cerr << endl << "Failed to load image at: "
                 << string(argv[3]) << "/" << vstrImageFilenamesRGB[ni] << endl;
            return 1;
        }

        if(imageScale != 1.f)
        {
            int width = imRGB.cols * imageScale;
            int height = imRGB.rows * imageScale;
            cv::resize(imRGB, imRGB, cv::Size(width, height));
            cv::resize(imD, imD, cv::Size(width, height));
        }

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t1 = std::chrono::monotonic_clock::now();
#endif

        // Pass the image to the SLAM system
        SLAM.TrackRGBD(imRGB,imD,tframe);

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t2 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t2 = std::chrono::monotonic_clock::now();
#endif

        double ttrack= std::chrono::duration_cast<std::chrono::duration<double> >(t2 - t1).count();

        vTimesTrack[ni]=ttrack;

        // Wait to load the next frame
        double T=0;
        if(ni<nImages-1)
            T = vTimestamps[ni+1]-tframe;
        else if(ni>0)
            T = tframe-vTimestamps[ni-1];

        if(ttrack<T)
            usleep((T-ttrack)*1e6);
    }

    // Stop all threads
    SLAM.Shutdown();

    // Tracking time statistics
    sort(vTimesTrack.begin(),vTimesTrack.end());
    float totaltime = 0;
    for(int ni=0; ni<nImages; ni++)
    {
        totaltime+=vTimesTrack[ni];
    }
    cout << "-------" << endl << endl;
    cout << "median tracking time: " << vTimesTrack[nImages/2] << endl;
    cout << "mean tracking time: " << totaltime/nImages << endl;

    // Save camera trajectory
    SLAM.SaveTrajectoryTUM("CameraTrajectory.txt");
    SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");   

    return 0;
}

void LoadImages() {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "rgbd_tum.cc"
            source_path.write_text(source, encoding="utf-8")
            changed = PATCH_HELPER.patch_rgbd_tum(source_path)
            rewritten = source_path.read_text(encoding="utf-8")

        self.assertTrue(changed)
        self.assertIn("#include<cstdlib>", rewritten)
        self.assertIn('std::getenv("ORB_SLAM3_DISABLE_VIEWER")', rewritten)
        self.assertIn("HEL-63 diagnostic: rgbd_tum disable_viewer=", rewritten)
        self.assertIn("HEL-63 diagnostic: frame ", rewritten)
        self.assertIn("ORB_SLAM3_HEL63_MAX_FRAMES", rewritten)
        self.assertIn("HEL-63 diagnostic: entering SLAM shutdown", rewritten)
        self.assertIn("HEL-63 diagnostic: SaveTrajectoryTUM completed", rewritten)
        self.assertIn(
            "HEL-63 diagnostic: SaveKeyFrameTrajectoryTUM completed",
            rewritten,
        )

    def test_rgbd_tum_rewrite_is_idempotent(self) -> None:
        source = """#include<iostream>
#include<algorithm>
#include<fstream>
#include<chrono>
#include<cstdlib>

void LoadImages();

int main(int argc, char **argv)
{
    int nImages = 2;
    vector<float> vTimesTrack;
    vTimesTrack.resize(nImages);
    const bool disable_viewer = std::getenv("ORB_SLAM3_DISABLE_VIEWER") != nullptr;
    cout << "HEL-63 diagnostic: rgbd_tum disable_viewer=" << disable_viewer << endl;

    // Create SLAM system. It initializes all system threads and gets ready to process frames.
    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::RGBD,!disable_viewer);
    float imageScale = SLAM.GetImageScale();

    const char* hel63_max_frames_env = std::getenv("ORB_SLAM3_HEL63_MAX_FRAMES");
    const bool skip_frame_trajectory_save = std::getenv("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE") != nullptr;
    const bool skip_keyframe_trajectory_save = std::getenv("ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE") != nullptr;
    int hel63_max_frames = -1;
    if(hel63_max_frames_env)
    {
        hel63_max_frames = std::atoi(hel63_max_frames_env);
        cout << "HEL-63 diagnostic: rgbd_tum max frames=" << hel63_max_frames << endl;
    }
    if(skip_frame_trajectory_save || skip_keyframe_trajectory_save)
    {
        cout << "HEL-63 diagnostic: save toggles frame=" << skip_frame_trajectory_save
             << ", keyframe=" << skip_keyframe_trajectory_save << endl;
    }

    int processed_images = 0;

    // Main loop
    cv::Mat imRGB, imD;
    for(int ni=0; ni<nImages; ni++)
    {
        // Read image and depthmap from file
        imRGB = cv::imread(string(argv[3])+"/"+vstrImageFilenamesRGB[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        imD = cv::imread(string(argv[3])+"/"+vstrImageFilenamesD[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        double tframe = vTimestamps[ni];

        if(imRGB.empty())
        {
            cerr << endl << "Failed to load image at: "
                 << string(argv[3]) << "/" << vstrImageFilenamesRGB[ni] << endl;
            return 1;
        }

        if(imageScale != 1.f)
        {
            int width = imRGB.cols * imageScale;
            int height = imRGB.rows * imageScale;
            cv::resize(imRGB, imRGB, cv::Size(width, height));
            cv::resize(imD, imD, cv::Size(width, height));
        }

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t1 = std::chrono::monotonic_clock::now();
#endif

        // Pass the image to the SLAM system
        cout << "HEL-63 diagnostic: frame " << ni << " TrackRGBD start timestamp=" << tframe << endl;
        SLAM.TrackRGBD(imRGB,imD,tframe);
        cout << "HEL-63 diagnostic: frame " << ni << " TrackRGBD completed" << endl;

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t2 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t2 = std::chrono::monotonic_clock::now();
#endif

        double ttrack= std::chrono::duration_cast<std::chrono::duration<double> >(t2 - t1).count();

        vTimesTrack[ni]=ttrack;
        processed_images = ni + 1;

        if(hel63_max_frames > 0 && processed_images >= hel63_max_frames)
        {
            cout << "HEL-63 diagnostic: stopping after " << processed_images
                 << " frames due to ORB_SLAM3_HEL63_MAX_FRAMES" << endl;
            break;
        }

        // Wait to load the next frame
        double T=0;
        if(ni<nImages-1)
            T = vTimestamps[ni+1]-tframe;
        else if(ni>0)
            T = tframe-vTimestamps[ni-1];

        if(ttrack<T)
            usleep((T-ttrack)*1e6);
    }

    if(processed_images == 0)
        processed_images = nImages;

    // Stop all threads
    cout << "HEL-63 diagnostic: entering SLAM shutdown" << endl;
    SLAM.Shutdown();
    cout << "HEL-63 diagnostic: SLAM shutdown completed" << endl;

    // Tracking time statistics
    sort(vTimesTrack.begin(), vTimesTrack.begin() + processed_images);
    float totaltime = 0;
    for(int ni=0; ni<processed_images; ni++)
    {
        totaltime+=vTimesTrack[ni];
    }
    cout << "-------" << endl << endl;
    cout << "median tracking time: " << vTimesTrack[processed_images/2] << endl;
    cout << "mean tracking time: " << totaltime/processed_images << endl;

    // Save camera trajectory
    if(skip_frame_trajectory_save)
        cout << "HEL-63 diagnostic: skipping SaveTrajectoryTUM for CameraTrajectory.txt" << endl;
    else
    {
        cout << "HEL-63 diagnostic: calling SaveTrajectoryTUM for CameraTrajectory.txt" << endl;
        SLAM.SaveTrajectoryTUM("CameraTrajectory.txt");
        cout << "HEL-63 diagnostic: SaveTrajectoryTUM completed" << endl;
    }
    if(skip_keyframe_trajectory_save)
        cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryTUM for KeyFrameTrajectory.txt" << endl;
    else
    {
        cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryTUM for KeyFrameTrajectory.txt" << endl;
        SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");
        cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryTUM completed" << endl;
    }

    return 0;
}

void LoadImages() {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "rgbd_tum.cc"
            source_path.write_text(source, encoding="utf-8")
            self.assertFalse(PATCH_HELPER.patch_rgbd_tum(source_path))
            self.assertEqual(source_path.read_text(encoding="utf-8"), source)

    def test_rewrites_rgbd_tum_main_with_viewer_and_save_diagnostics(self) -> None:
        source = """#include<iostream>
#include<algorithm>
#include<fstream>
#include<chrono>

int main(int argc, char **argv)
{
    // Create SLAM system. It initializes all system threads and gets ready to process frames.
    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::RGBD,true);
    float imageScale = SLAM.GetImageScale();

    // Main loop
    cv::Mat imRGB, imD;
    for(int ni=0; ni<nImages; ni++)
    {
        // Read image and depthmap from file
        imRGB = cv::imread(string(argv[3])+"/"+vstrImageFilenamesRGB[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        imD = cv::imread(string(argv[3])+"/"+vstrImageFilenamesD[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        double tframe = vTimestamps[ni];

        if(imRGB.empty())
        {
            cerr << endl << "Failed to load image at: "
                 << string(argv[3]) << "/" << vstrImageFilenamesRGB[ni] << endl;
            return 1;
        }

        if(imageScale != 1.f)
        {
            int width = imRGB.cols * imageScale;
            int height = imRGB.rows * imageScale;
            cv::resize(imRGB, imRGB, cv::Size(width, height));
            cv::resize(imD, imD, cv::Size(width, height));
        }

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t1 = std::chrono::monotonic_clock::now();
#endif

        // Pass the image to the SLAM system
        SLAM.TrackRGBD(imRGB,imD,tframe);

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t2 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t2 = std::chrono::monotonic_clock::now();
#endif

        double ttrack= std::chrono::duration_cast<std::chrono::duration<double> >(t2 - t1).count();

        vTimesTrack[ni]=ttrack;

        // Wait to load the next frame
        double T=0;
        if(ni<nImages-1)
            T = vTimestamps[ni+1]-tframe;
        else if(ni>0)
            T = tframe-vTimestamps[ni-1];

        if(ttrack<T)
            usleep((T-ttrack)*1e6);
    }

    // Stop all threads
    SLAM.Shutdown();

    // Tracking time statistics
    sort(vTimesTrack.begin(),vTimesTrack.end());
    float totaltime = 0;
    for(int ni=0; ni<nImages; ni++)
    {
        totaltime+=vTimesTrack[ni];
    }
    cout << "-------" << endl << endl;
    cout << "median tracking time: " << vTimesTrack[nImages/2] << endl;
    cout << "mean tracking time: " << totaltime/nImages << endl;

    // Save camera trajectory
    SLAM.SaveTrajectoryTUM("CameraTrajectory.txt");
    SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");   
}

void LoadImages() {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "rgbd_tum.cc"
            source_path.write_text(source, encoding="utf-8")
            changed = PATCH_HELPER.patch_rgbd_tum(source_path)
            rewritten = source_path.read_text(encoding="utf-8")

        self.assertTrue(changed)
        self.assertIn("#include<cstdlib>", rewritten)
        self.assertIn('std::getenv("ORB_SLAM3_DISABLE_VIEWER")', rewritten)
        self.assertIn('HEL-63 diagnostic: rgbd_tum disable_viewer=', rewritten)
        self.assertIn('HEL-63 diagnostic: calling SaveTrajectoryTUM', rewritten)
        self.assertIn('HEL-63 diagnostic: SaveKeyFrameTrajectoryTUM completed', rewritten)

    def test_rgbd_tum_rewrite_is_idempotent(self) -> None:
        source = """#include<iostream>
#include<algorithm>
#include<fstream>
#include<chrono>
#include<cstdlib>

int main(int argc, char **argv)
{
    const bool disable_viewer = std::getenv("ORB_SLAM3_DISABLE_VIEWER") != nullptr;
    cout << "HEL-63 diagnostic: rgbd_tum disable_viewer=" << disable_viewer << endl;

    // Create SLAM system. It initializes all system threads and gets ready to process frames.
    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::RGBD,!disable_viewer);
    float imageScale = SLAM.GetImageScale();

    const char* hel63_max_frames_env = std::getenv("ORB_SLAM3_HEL63_MAX_FRAMES");
    const bool skip_frame_trajectory_save = std::getenv("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE") != nullptr;
    const bool skip_keyframe_trajectory_save = std::getenv("ORB_SLAM3_SKIP_KEYFRAME_TRAJECTORY_SAVE") != nullptr;
    int hel63_max_frames = -1;
    if(hel63_max_frames_env)
    {
        hel63_max_frames = std::atoi(hel63_max_frames_env);
        cout << "HEL-63 diagnostic: rgbd_tum max frames=" << hel63_max_frames << endl;
    }
    if(skip_frame_trajectory_save || skip_keyframe_trajectory_save)
    {
        cout << "HEL-63 diagnostic: save toggles frame=" << skip_frame_trajectory_save
             << ", keyframe=" << skip_keyframe_trajectory_save << endl;
    }

    int processed_images = 0;

    // Main loop
    cv::Mat imRGB, imD;
    for(int ni=0; ni<nImages; ni++)
    {
        // Read image and depthmap from file
        imRGB = cv::imread(string(argv[3])+"/"+vstrImageFilenamesRGB[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        imD = cv::imread(string(argv[3])+"/"+vstrImageFilenamesD[ni],cv::IMREAD_UNCHANGED); //,cv::IMREAD_UNCHANGED);
        double tframe = vTimestamps[ni];

        if(imRGB.empty())
        {
            cerr << endl << "Failed to load image at: "
                 << string(argv[3]) << "/" << vstrImageFilenamesRGB[ni] << endl;
            return 1;
        }

        if(imageScale != 1.f)
        {
            int width = imRGB.cols * imageScale;
            int height = imRGB.rows * imageScale;
            cv::resize(imRGB, imRGB, cv::Size(width, height));
            cv::resize(imD, imD, cv::Size(width, height));
        }

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t1 = std::chrono::monotonic_clock::now();
#endif

        // Pass the image to the SLAM system
        cout << "HEL-63 diagnostic: frame " << ni << " TrackRGBD start timestamp=" << tframe << endl;
        SLAM.TrackRGBD(imRGB,imD,tframe);
        cout << "HEL-63 diagnostic: frame " << ni << " TrackRGBD completed" << endl;

#ifdef COMPILEDWITHC11
        std::chrono::steady_clock::time_point t2 = std::chrono::steady_clock::now();
#else
        std::chrono::monotonic_clock::time_point t2 = std::chrono::monotonic_clock::now();
#endif

        double ttrack= std::chrono::duration_cast<std::chrono::duration<double> >(t2 - t1).count();

        vTimesTrack[ni]=ttrack;
        processed_images = ni + 1;

        if(hel63_max_frames > 0 && processed_images >= hel63_max_frames)
        {
            cout << "HEL-63 diagnostic: stopping after " << processed_images
                 << " frames due to ORB_SLAM3_HEL63_MAX_FRAMES" << endl;
            break;
        }

        // Wait to load the next frame
        double T=0;
        if(ni<nImages-1)
            T = vTimestamps[ni+1]-tframe;
        else if(ni>0)
            T = tframe-vTimestamps[ni-1];

        if(ttrack<T)
            usleep((T-ttrack)*1e6);
    }

    if(processed_images == 0)
        processed_images = nImages;

    // Stop all threads
    cout << "HEL-63 diagnostic: entering SLAM shutdown" << endl;
    SLAM.Shutdown();
    cout << "HEL-63 diagnostic: SLAM shutdown completed" << endl;

    // Tracking time statistics
    sort(vTimesTrack.begin(), vTimesTrack.begin() + processed_images);
    float totaltime = 0;
    for(int ni=0; ni<processed_images; ni++)
    {
        totaltime+=vTimesTrack[ni];
    }
    cout << "-------" << endl << endl;
    cout << "median tracking time: " << vTimesTrack[processed_images/2] << endl;
    cout << "mean tracking time: " << totaltime/processed_images << endl;

    // Save camera trajectory
    if(skip_frame_trajectory_save)
        cout << "HEL-63 diagnostic: skipping SaveTrajectoryTUM for CameraTrajectory.txt" << endl;
    else
    {
        cout << "HEL-63 diagnostic: calling SaveTrajectoryTUM for CameraTrajectory.txt" << endl;
        SLAM.SaveTrajectoryTUM("CameraTrajectory.txt");
        cout << "HEL-63 diagnostic: SaveTrajectoryTUM completed" << endl;
    }
    if(skip_keyframe_trajectory_save)
        cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryTUM for KeyFrameTrajectory.txt" << endl;
    else
    {
        cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryTUM for KeyFrameTrajectory.txt" << endl;
        SLAM.SaveKeyFrameTrajectoryTUM("KeyFrameTrajectory.txt");
        cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryTUM completed" << endl;
    }
}

void LoadImages() {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "rgbd_tum.cc"
            source_path.write_text(source, encoding="utf-8")
            self.assertFalse(PATCH_HELPER.patch_rgbd_tum(source_path))
            self.assertEqual(source_path.read_text(encoding="utf-8"), source)
