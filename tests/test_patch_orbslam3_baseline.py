from __future__ import annotations

import importlib.util
from pathlib import Path
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
