# package_scanner
Simple script which scans images for packages and its version

## How it works

First script clones provided repository. Then it goes through the Dockerfiles in this repository and for each this file it runs all their base images and it looks up for the
asked package. Finally it builds container from the Dockerfile and it also looks up for the asked package there.

Script shows package version for each base image and for the Dockerfile. If the package is not present you see error from container's shell.

It is possible to look up for packages in two sources:

- `pip`
- `rpm`

Source is specified in the arguments of the script.

## How to use

First you need to install pip requirements:

```
pip install -r requirements.txt
```

Then you can run the script:

```
python script.py [repository name] [package source] [package]
```

For example:

```
python script.py https://github.com/RedHatInsights/floorist-operator.git pip requests
```