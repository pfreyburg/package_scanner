import docker
from git import Repo, exc
from os import environ
import re
import shutil
import sys
from pathlib import Path

REPO_WORKDIR = environ.get("REPO_WORKDIR", ".workdir")
PYTHON_INTERPRETER = environ.get("PYTHON_INTERPRETER", "python3")

def scan_dockerfile(dockerfile):
    f = open(dockerfile)
    r = f.read()

    rows = r.split("\n")
    images = []

    for row in rows:
        if row.startswith("FROM"):
            image = re.search(r'^FROM\s+(?:--platform=\S+\s+)?([^\s]+)', row, re.IGNORECASE).group(1)
            images.append(image)

    return images

def run_image(client, image, source, package_name):
    command = ["-c", PYTHON_INTERPRETER + " -m pip freeze | grep " + package_name]

    if source == "rpm":
        command = ["-c", "rpm -qa | grep " + package_name]
   
    try:
        container = client.containers.run(image, command, remove=True, entrypoint="sh")

        print(container.decode('utf-8'))
    except docker.errors.ContainerError as e:
        print(e)

def build_and_run_dockerfile(client, dockerfile, source, package_name):
    df_path = Path(REPO_WORKDIR).resolve()
    relative_dockerfile = str(dockerfile).replace(REPO_WORKDIR+"/", "")
    image_obj, _ = client.images.build(
            path=str(df_path),
            dockerfile=relative_dockerfile,
            rm=True, 
            tag="ps_temp_script_image:latest" 
        )
    run_image(client, image_obj.id, source, package_name)
    client.images.remove(image=image_obj.id, force=True)
   

if len(sys.argv) < 4:
    print("missing required arguments")
    sys.exit(1)

git_url = sys.argv[1]
source = sys.argv[2]

if source != "pip" and source != "rpm":
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
            run_image(client, image, source, package_name)
        print("Dockerfile:")
        build_and_run_dockerfile(client, path, source, package_name)
finally:
    shutil.rmtree(REPO_WORKDIR)