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
    def test_rewrites_edge_se3_project_xyz_to_force_eigen_eval(self) -> None:
        source = """void EdgeSE3ProjectXYZ::linearizeOplus() {
    g2o::VertexSE3Expmap * vj = static_cast<g2o::VertexSE3Expmap *>(_vertices[1]);
    g2o::SE3Quat T(vj->estimate());
    g2o::VertexSBAPointXYZ* vi = static_cast<g2o::VertexSBAPointXYZ*>(_vertices[0]);
    Eigen::Vector3d xyz = vi->estimate();
    Eigen::Vector3d xyz_trans = T.map(xyz);

    double x = xyz_trans[0];
    double y = xyz_trans[1];
    double z = xyz_trans[2];

    auto projectJac = -pCamera->projectJac(xyz_trans);

    _jacobianOplusXi =  projectJac * T.rotation().toRotationMatrix();

    Eigen::Matrix<double,3,6> SE3deriv;
    SE3deriv << 0.f, z,   -y, 1.f, 0.f, 0.f,
            -z , 0.f, x, 0.f, 1.f, 0.f,
            y ,  -x , 0.f, 0.f, 0.f, 1.f;

    _jacobianOplusXj = projectJac * SE3deriv;
}
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "OptimizableTypes.cpp"
            source_path.write_text(source, encoding="utf-8")
            changed = PATCH_HELPER.patch_optimizable_types(source_path)
            rewritten = source_path.read_text(encoding="utf-8")

        self.assertTrue(changed)
        self.assertIn("const Eigen::Matrix<double, 2, 3> project_jac =", rewritten)
        self.assertIn("(-pCamera->projectJac(xyz_trans)).eval()", rewritten)
        self.assertIn("_jacobianOplusXi = project_jac * T.rotation().toRotationMatrix();", rewritten)
        self.assertIn("_jacobianOplusXj = project_jac * SE3deriv;", rewritten)
        self.assertNotIn("auto projectJac = -pCamera->projectJac(xyz_trans);", rewritten)

    def test_edge_se3_project_xyz_rewrite_is_idempotent(self) -> None:
        source = """void EdgeSE3ProjectXYZ::linearizeOplus() {
    g2o::VertexSE3Expmap * vj = static_cast<g2o::VertexSE3Expmap *>(_vertices[1]);
    g2o::SE3Quat T(vj->estimate());
    g2o::VertexSBAPointXYZ* vi = static_cast<g2o::VertexSBAPointXYZ*>(_vertices[0]);
    Eigen::Vector3d xyz = vi->estimate();
    Eigen::Vector3d xyz_trans = T.map(xyz);

    double x = xyz_trans[0];
    double y = xyz_trans[1];
    double z = xyz_trans[2];

    const Eigen::Matrix<double, 2, 3> project_jac =
        (-pCamera->projectJac(xyz_trans)).eval();

    _jacobianOplusXi = project_jac * T.rotation().toRotationMatrix();

    Eigen::Matrix<double,3,6> SE3deriv;
    SE3deriv << 0.f, z,   -y, 1.f, 0.f, 0.f,
            -z , 0.f, x, 0.f, 1.f, 0.f,
            y ,  -x , 0.f, 0.f, 0.f, 1.f;

    _jacobianOplusXj = project_jac * SE3deriv;
}
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "OptimizableTypes.cpp"
            source_path.write_text(source, encoding="utf-8")
            changed = PATCH_HELPER.patch_optimizable_types(source_path)
            rewritten = source_path.read_text(encoding="utf-8")

        self.assertFalse(changed)
        self.assertEqual(rewritten, source)

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
    int seq = 0;
    int num_seq = 1;
    vector<float> vTimesTrack;
    vector<int> nImages;
    nImages.push_back(1);
    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::MONOCULAR,false, 0, "");
    float imageScale = SLAM.GetImageScale();
    double t_resize = 0.f;
    double t_track = 0.f;

    int proccIm = 0;
    for (seq = 0; seq<num_seq; seq++)
    {
        for(int ni=0; ni<nImages[seq]; ni++, proccIm++)
        {
            double tframe = 0;

            // Pass the image to the SLAM system
            SLAM.TrackMonocular(im,tframe); // TODO change to monocular_inertial

            double ttrack= 0;
            vTimesTrack[ni]=ttrack;

            // Wait to load the next frame
        }
        if(seq < num_seq - 1)
        {
            cout << "Changing the dataset" << endl;

            SLAM.ChangeDataset();
        }
    }

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

    sort(vTimesTrack.begin(),vTimesTrack.end());
    float totaltime = 0;
    for(int ni=0; ni<nImages[0]; ni++)
    {
        totaltime+=vTimesTrack[ni];
    }
    cout << "-------" << endl << endl;
    cout << "median tracking time: " << vTimesTrack[nImages[0]/2] << endl;
    cout << "mean tracking time: " << totaltime/proccIm << endl;

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
        self.assertIn('std::getenv("ORB_SLAM3_HEL68_MAX_FRAMES")', rewritten)
        self.assertIn("HEL-68 diagnostic: mono_tum_vi max frames=", rewritten)
        self.assertIn("HEL-68 diagnostic: frame ", rewritten)
        self.assertIn("TrackMonocular completed", rewritten)
        self.assertIn('std::getenv("ORB_SLAM3_SKIP_FRAME_TRAJECTORY_SAVE")', rewritten)
        self.assertIn("HEL-75 diagnostic: trajectory save cwd=", rewritten)
        self.assertIn("HEL-63 diagnostic: entering SLAM shutdown", rewritten)
        self.assertIn("HEL-63 diagnostic: SaveTrajectoryEuRoC completed", rewritten)
        self.assertIn("HEL-78 diagnostic: frame trajectory post_return open=", rewritten)
        self.assertIn(
            "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed",
            rewritten,
        )
        self.assertIn(
            "HEL-78 diagnostic: keyframe trajectory post_return open=",
            rewritten,
        )

    def test_mono_tum_vi_rewrite_is_idempotent(self) -> None:
        source = """#include <unistd.h>
#include <cstdlib>

int main(int argc, char **argv)
{
    int seq = 0;
    int num_seq = 1;
    vector<float> vTimesTrack;
    vector<int> nImages;
    nImages.push_back(1);
    ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::MONOCULAR,false, 0, "");
    float imageScale = SLAM.GetImageScale();
    double t_resize = 0.f;
    double t_track = 0.f;

    const char* hel68_max_frames_env = std::getenv("ORB_SLAM3_HEL68_MAX_FRAMES");
    int hel68_max_frames = -1;
    if(hel68_max_frames_env)
    {
        hel68_max_frames = std::atoi(hel68_max_frames_env);
        cout << "HEL-68 diagnostic: mono_tum_vi max frames=" << hel68_max_frames << endl;
    }

    int proccIm = 0;
    int hel68_processed_frames = 0;
    bool hel68_stop_requested = false;
    for (seq = 0; seq<num_seq; seq++)
    {
        for(int ni=0; ni<nImages[seq]; ni++, proccIm++)
        {
            double tframe = 0;

            // Pass the image to the SLAM system
            cout << "HEL-68 diagnostic: frame " << hel68_processed_frames
                 << " TrackMonocular start timestamp=" << tframe << endl;
            SLAM.TrackMonocular(im,tframe); // TODO change to monocular_inertial
            cout << "HEL-68 diagnostic: frame " << hel68_processed_frames
                 << " TrackMonocular completed" << endl;

            double ttrack= 0;
            vTimesTrack[hel68_processed_frames]=ttrack;
            hel68_processed_frames++;

            if(hel68_max_frames > 0 && hel68_processed_frames >= hel68_max_frames)
            {
                cout << "HEL-68 diagnostic: stopping after " << hel68_processed_frames
                     << " frames due to ORB_SLAM3_HEL68_MAX_FRAMES" << endl;
                hel68_stop_requested = true;
                break;
            }

            // Wait to load the next frame
        }
        if(hel68_stop_requested)
        {
            break;
        }

        if(seq < num_seq - 1)
        {
            cout << "Changing the dataset" << endl;

            SLAM.ChangeDataset();
        }
    }

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
    char hel75_save_cwd[4096];
    if(getcwd(hel75_save_cwd, sizeof(hel75_save_cwd)) != nullptr)
        cout << "HEL-75 diagnostic: trajectory save cwd=" << hel75_save_cwd << endl;
    else
        cout << "HEL-75 diagnostic: trajectory save cwd=<unavailable>" << endl;

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
            ifstream hel78_frame_saved_file(f_file.c_str(), ios::binary | ios::ate);
            cout << "HEL-78 diagnostic: frame trajectory post_return open=" << hel78_frame_saved_file.is_open()
                 << ", bytes="
                 << (hel78_frame_saved_file.is_open() ? static_cast<long long>(hel78_frame_saved_file.tellg()) : -1)
                 << ", filename=" << f_file << endl;
        }
        if(skip_keyframe_trajectory_save)
            cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryEuRoC for " << kf_file << endl;
        else
        {
            cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC for " << kf_file << endl;
            SLAM.SaveKeyFrameTrajectoryEuRoC(kf_file);
            cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed" << endl;
            ifstream hel78_keyframe_saved_file(kf_file.c_str(), ios::binary | ios::ate);
            cout << "HEL-78 diagnostic: keyframe trajectory post_return open=" << hel78_keyframe_saved_file.is_open()
                 << ", bytes="
                 << (hel78_keyframe_saved_file.is_open() ? static_cast<long long>(hel78_keyframe_saved_file.tellg()) : -1)
                 << ", filename=" << kf_file << endl;
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
            ifstream hel78_frame_saved_file("CameraTrajectory.txt", ios::binary | ios::ate);
            cout << "HEL-78 diagnostic: frame trajectory post_return open=" << hel78_frame_saved_file.is_open()
                 << ", bytes="
                 << (hel78_frame_saved_file.is_open() ? static_cast<long long>(hel78_frame_saved_file.tellg()) : -1)
                 << ", filename=CameraTrajectory.txt" << endl;
        }
        if(skip_keyframe_trajectory_save)
            cout << "HEL-63 diagnostic: skipping SaveKeyFrameTrajectoryEuRoC for KeyFrameTrajectory.txt" << endl;
        else
        {
            cout << "HEL-63 diagnostic: calling SaveKeyFrameTrajectoryEuRoC for KeyFrameTrajectory.txt" << endl;
            SLAM.SaveKeyFrameTrajectoryEuRoC("KeyFrameTrajectory.txt");
            cout << "HEL-63 diagnostic: SaveKeyFrameTrajectoryEuRoC completed" << endl;
            ifstream hel78_keyframe_saved_file("KeyFrameTrajectory.txt", ios::binary | ios::ate);
            cout << "HEL-78 diagnostic: keyframe trajectory post_return open=" << hel78_keyframe_saved_file.is_open()
                 << ", bytes="
                 << (hel78_keyframe_saved_file.is_open() ? static_cast<long long>(hel78_keyframe_saved_file.tellg()) : -1)
                 << ", filename=KeyFrameTrajectory.txt" << endl;
        }
    }

    const int hel68_stats_count = hel68_processed_frames > 0 ? hel68_processed_frames : nImages[0];
    sort(vTimesTrack.begin(), vTimesTrack.begin() + hel68_stats_count);
    float totaltime = 0;
    for(int ni=0; ni<hel68_stats_count; ni++)
    {
        totaltime+=vTimesTrack[ni];
    }
    cout << "-------" << endl << endl;
    cout << "median tracking time: " << vTimesTrack[hel68_stats_count/2] << endl;
    cout << "mean tracking time: " << totaltime/hel68_stats_count << endl;

    return 0;
}

void LoadImages() {}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = Path(tmpdir) / "mono_tum_vi.cc"
            source_path.write_text(source, encoding="utf-8")
            self.assertFalse(PATCH_HELPER.patch_mono_tum_vi(source_path))
            self.assertEqual(source_path.read_text(encoding="utf-8"), source)

    def test_normalize_save_trajectory_euroc_adds_post_close_diagnostics(self) -> None:
        block = """void System::SaveTrajectoryEuRoC(const string &filename)
{
    vector<Map*> vpMaps = mpAtlas->GetAllMaps();
    int numMaxKFs = 0;
    Map* pBiggerMap;
    std::cout << "There are " << std::to_string(vpMaps.size()) << " maps in the atlas" << std::endl;
    for(Map* pMap :vpMaps)
    {
        std::cout << " Map " << std::to_string(pMap->GetId()) << " has " << std::to_string(pMap->GetAllKeyFrames().size()) << " KFs" << std::endl;
        if(pMap->GetAllKeyFrames().size() > numMaxKFs)
        {
            numMaxKFs = pMap->GetAllKeyFrames().size();
            pBiggerMap = pMap;
        }
    }

    vector<KeyFrame*> vpKFs = pBiggerMap->GetAllKeyFrames();
    ofstream f;
    f.open(filename.c_str());
    // cout << "file open" << endl;
    f << fixed;
    list<ORB_SLAM3::KeyFrame*>::iterator lRit = mpTracker->mlpReferences.begin();
    list<double>::iterator lT = mpTracker->mlFrameTimes.begin();
    list<bool>::iterator lbL = mpTracker->mlbLost.begin();
    for(list<Sophus::SE3f>::iterator lit=mpTracker->mlRelativeFramePoses.begin(),
    lend=mpTracker->mlRelativeFramePoses.end();lit!=lend;lit++, lRit++, lT++, lbL++)
    {
        if(*lbL)
            continue;
        KeyFrame* pKF = *lRit;
        Sophus::SE3f Trw;
        while(pKF->isBad())
        {
            Trw = Trw * pKF->mTcp;
            pKF = pKF->GetParent();
        }
        Trw = Trw * pKF->GetPose() * Two;
        Sophus::SE3f Tcw = (*lit) * Trw;
        Sophus::SE3f Twc = Tcw.inverse();
        Eigen::Vector3f twc = Twc.translation();
        Eigen::Quaternionf q = Twc.unit_quaternion();
        f << setprecision(6) << *lT << " " << setprecision(9) << twc(0) << " " << twc(1) << " " << twc(2) << " " << q.x() << " " << q.y() << " " << q.z() << " " << q.w() << endl;
    }
    f.close();
}
"""
        rewritten = PATCH_HELPER.normalize_save_trajectory_euroc(block)

        self.assertIn("No keyframes were recorded; skipping trajectory save.", rewritten)
        self.assertIn(
            'HEL-75 diagnostic: SaveTrajectoryEuRoC stream open=',
            rewritten,
        )
        self.assertIn(
            'HEL-78 diagnostic: SaveTrajectoryEuRoC atlas_state ',
            rewritten,
        )
        self.assertIn(
            'HEL-75 diagnostic: SaveTrajectoryEuRoC post_close open=',
            rewritten,
        )

    def test_normalize_save_keyframe_trajectory_euroc_adds_post_close_diagnostics(
        self,
    ) -> None:
        block = """void System::SaveKeyFrameTrajectoryEuRoC(const string &filename)
{
    vector<Map*> vpMaps = mpAtlas->GetAllMaps();
    Map* pBiggerMap;
    int numMaxKFs = 0;
    for(Map* pMap :vpMaps)
    {
        if(pMap->GetAllKeyFrames().size() > numMaxKFs)
        {
            numMaxKFs = pMap->GetAllKeyFrames().size();
            pBiggerMap = pMap;
        }
    }

    vector<KeyFrame*> vpKFs = pBiggerMap->GetAllKeyFrames();
    ofstream f;
    f.open(filename.c_str());
    f << fixed;
    for(size_t i=0; i<vpKFs.size(); i++)
    {
        KeyFrame* pKF = vpKFs[i];
        if(pKF->isBad())
            continue;
        Sophus::SE3f Twc = pKF->GetPoseInverse();
        Eigen::Quaternionf q = Twc.unit_quaternion();
        Eigen::Vector3f t = Twc.translation();
        f << setprecision(6) << pKF->mTimeStamp << setprecision(7) << " " << t(0) << " " << t(1) << " " << t(2)
          << " " << q.x() << " " << q.y() << " " << q.z() << " " << q.w() << endl;
    }
    f.close();
}
"""
        rewritten = PATCH_HELPER.normalize_save_keyframe_trajectory_euroc(block)

        self.assertIn(
            "No keyframes were recorded; skipping keyframe trajectory save.",
            rewritten,
        )
        self.assertIn(
            'HEL-75 diagnostic: SaveKeyFrameTrajectoryEuRoC stream open=',
            rewritten,
        )
        self.assertIn(
            'HEL-78 diagnostic: SaveKeyFrameTrajectoryEuRoC atlas_state ',
            rewritten,
        )
        self.assertIn(
            'HEL-75 diagnostic: SaveKeyFrameTrajectoryEuRoC post_close open=',
            rewritten,
        )

    def test_normalize_reset_active_map_adds_pre_and_post_clear_diagnostics(self) -> None:
        block = """void Tracking::ResetActiveMap(bool bLocMap)
{
    Verbose::PrintMess("Active map Reseting", Verbose::VERBOSITY_NORMAL);
    if(mpViewer)
    {
        mpViewer->RequestStop();
        while(!mpViewer->isStopped())
            usleep(3000);
    }

    Map* pMap = mpAtlas->GetCurrentMap();

    if (!bLocMap)
    {
        Verbose::PrintMess("Reseting Local Mapper...", Verbose::VERBOSITY_VERY_VERBOSE);
        mpLocalMapper->RequestResetActiveMap(pMap);
        Verbose::PrintMess("done", Verbose::VERBOSITY_VERY_VERBOSE);
    }

    Verbose::PrintMess("Reseting Loop Closing...", Verbose::VERBOSITY_NORMAL);
    mpLoopClosing->RequestResetActiveMap(pMap);
    Verbose::PrintMess("done", Verbose::VERBOSITY_NORMAL);

    Verbose::PrintMess("Reseting Database", Verbose::VERBOSITY_NORMAL);
    mpKeyFrameDB->clearMap(pMap);
    Verbose::PrintMess("done", Verbose::VERBOSITY_NORMAL);

    // Clear Map (this erase MapPoints and KeyFrames)
    mpAtlas->clearMap();
}
"""

        rewritten = PATCH_HELPER.normalize_reset_active_map(block)

        self.assertIn(
            'HEL-78 diagnostic: ResetActiveMap pre_clear ',
            rewritten,
        )
        self.assertIn(
            'HEL-78 diagnostic: ResetActiveMap post_clear ',
            rewritten,
        )

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
