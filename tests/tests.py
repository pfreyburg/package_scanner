import docker
import os
import pathlib
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from script import build_and_run_dockerfile, REPO_WORKDIR

class TestPackageScanner(unittest.TestCase):
    def test_build_and_run_dockerfile(self):
        client = docker.from_env() 
        dockerfile = REPO_WORKDIR+"/Dockerfile"

        x = build_and_run_dockerfile(client, "tests/"+REPO_WORKDIR, dockerfile, "pip", "requests")
        self.assertEqual("requests==2.32.5", x.replace("\n", ""))
    
if __name__ == '__main__':
    unittest.main()