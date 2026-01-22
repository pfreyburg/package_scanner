""" Simple script which scans container images for packages and its version """

from os import environ
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

from git import Repo, exc

REPO_WORKDIR = environ.get("REPO_WORKDIR", ".workdir")
PYTHON_INTERPRETER = environ.get("PYTHON_INTERPRETER", "python3")

def scan_dockerfile(dockerfile):
    """
    Function opens provided Dockerfile and scans it for base images
    """
    with open(dockerfile, encoding="utf-8") as f:
        r = f.read()

    rows = r.split("\n")
    images = []

    for row in rows:
        if row.startswith("FROM"):
            pattern = r'^FROM\s+(?:--platform=\S+\s+)?([^\s]+)'
            image = re.search(pattern, row, re.IGNORECASE).group(1)
            images.append(image)

    return images

def run_image(image, source, package_name):
    """
    Function runs image on client and gets the installed version for the package
    if it is installed
    """
    command = PYTHON_INTERPRETER + " -m pip freeze | grep " + package_name

    if source == "rpm":
        command = "rpm -qa | grep " + package_name

    r = ""
    cmd = [
            "podman", "run", "--rm", 
            "--entrypoint", "sh", 
            image,
            "-c", command
        ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        r = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(e.stderr)
    return r

def build_and_run_dockerfile(dockerfile, source, package_name):
    """
    Function builds Dockerfile and then runs it
    """
    r = ""

    tag = "ps_temp_script_image"+str(random.randint(1000, 9999))+":latest"
    cmd = ["podman", "build", "-f", dockerfile, "-t", tag]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        return r

    r = run_image(tag, source, package_name)

    cmd = ["podman", "rmi", tag]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        return r

    return r

def main():
    """
    Main function
    """
    if len(sys.argv) < 4:
        print("missing required arguments")
        sys.exit(1)

    git_url = sys.argv[1]
    source = sys.argv[2]

    if source not in ["pip", "rpm"]:
        print("Package source "+source+" is not supported")
        sys.exit(1)

    package_name = sys.argv[3]

    try:
        Repo.clone_from(git_url, REPO_WORKDIR)
    except exc.GitCommandError as e:
        print(e)
        sys.exit(1)

    try:
        base_path = Path(REPO_WORKDIR)

        dockerfiles = list(base_path.rglob('Dockerfile'))

        if len(dockerfiles) < 1:
            print("there are no Dockerfiles in this repository")
            sys.exit(1)

        for path in dockerfiles:
            print("- " + str(path))
            print("Base image: ")
            images = scan_dockerfile(path)
            for image in images:
                print(image+": ", end="")
                print(run_image(image, source, package_name))
            print("Dockerfile:")
            print(build_and_run_dockerfile(str(path), source, package_name))
    finally:
        shutil.rmtree(REPO_WORKDIR)

if __name__ == '__main__':
    main()
