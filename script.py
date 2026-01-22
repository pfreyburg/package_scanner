""" Simple script which scans container images for packages and its version """

from os import environ
import re
import shutil
import sys
from pathlib import Path

import docker
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

def run_image(client, image, source, package_name):
    """
    Function runs image on client and gets the installed version for the package
    if it is installed
    """
    command = ["-c", PYTHON_INTERPRETER + " -m pip freeze | grep " + package_name]

    if source == "rpm":
        command = ["-c", "rpm -qa | grep " + package_name]
    r = ""
    try:
        container = client.containers.run(image, command, remove=True, entrypoint="sh")
        r = container.decode('utf-8')
    except docker.errors.ContainerError as e:
        print(e)
    return r

def build_and_run_dockerfile(client, workdir, dockerfile, source, package_name):
    """
    Function builds Dockerfile and then runs it
    """
    df_path = Path(workdir).resolve()
    relative_dockerfile = dockerfile.replace(REPO_WORKDIR+"/", "")
    r = ""
    try:
        image_obj, _ = client.images.build(
                path=str(df_path),
                dockerfile=relative_dockerfile,
                rm=True,
                tag="ps_temp_script_image:latest"
            )
        r = run_image(client, image_obj.id, source, package_name)
        client.images.remove(image=image_obj.id, force=True)
    except docker.errors.BuildError as e:
        print(e)
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
    client = docker.from_env()

    try:
        Repo.clone_from(git_url, REPO_WORKDIR)
    except exc.GitCommandError as e:
        print(e)
        sys.exit(1)

    try:
        base_path = Path(REPO_WORKDIR)

        dockerfiles = list(base_path.rglob('Dockerfile'))

        for path in dockerfiles:
            print("- " + str(path))
            print("Base image: ")
            images = scan_dockerfile(path)
            for image in images:
                print(image+": ", end="")
                print(run_image(client, image, source, package_name))
            print("Dockerfile:")
            print(build_and_run_dockerfile(client, REPO_WORKDIR, str(path), source, package_name))
    finally:
        shutil.rmtree(REPO_WORKDIR)

if __name__ == '__main__':
    main()
