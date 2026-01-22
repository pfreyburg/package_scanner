import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from script import build_and_run_dockerfile, run_image, scan_dockerfile, REPO_WORKDIR

client = None

class TestPackageScanner(unittest.TestCase):
    def test_scan_dockerfile(self):
        desired_images = ['image_a', 'image_b', 'image_c:latest']
        images = scan_dockerfile("tests/data/Dockerfile")
        
        self.assertEqual(desired_images, images)

    def test_run_image(self):
        x = run_image("redhat/ubi8-minimal", "rpm", "grep")
        self.assertTrue(x.startswith("grep"))

    def test_build_and_run_dockerfile(self):
        dockerfile = "tests/" + REPO_WORKDIR + "/Dockerfile"

        x = build_and_run_dockerfile(dockerfile, "pip", "requests")
        self.assertEqual("requests==2.32.5", x.replace("\n", ""))
