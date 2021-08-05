#!/bin/bash
set -e
export FAIR_HOME=$HOME/.fair/registry
mkdir -p "$FAIR_HOME"

if [ $# -eq 0 ]; then
    TAG=`curl --silent "https://api.github.com/repos/FAIRDataPipeline/data-registry/releases/latest" | grep -Po '"tag_name": "\K.*?(?=")'`
    echo "Cloning tag $TAG"
    git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME" > /dev/null 2>&1
    cd "$FAIR_HOME"
    git checkout tags/$TAG > /dev/null 2>&1
else
    case $1 in
        -t|--tag)
            echo "Cloning tag $2"
            git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME" > /dev/null 2>&1
            cd "$FAIR_HOME"
            git checkout tags/$2 > /dev/null 2>&1
            ;;
        -b|--branch)
            echo "Cloning branch $2"
            git clone https://github.com/FAIRDataPipeline/data-registry.git -b $2 "$FAIR_HOME" > /dev/null 2>&1
            ;;
        -p|--prerelease)
            TAG=`curl --silent "https://api.github.com/repos/FAIRDataPipeline/data-registry/releases" | grep -Po '"tag_name": "\K.*?(?=")' | sort -r -V | head -n 1`
            echo "Cloning tag $TAG"
            git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME" > /dev/null 2>&1
            cd "$FAIR_HOME"
            git checkout tags/$TAG > /dev/null 2>&1
            ;;
        -m|--main)
            echo "Cloning branch 'main'"
            git clone https://github.com/FAIRDataPipeline/data-registry.git "$FAIR_HOME" > /dev/null 2>&1
            ;;
    esac
fi

python3 -m venv "$FAIR_HOME"/venv
source "$FAIR_HOME"/venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r "$FAIR_HOME"/local-requirements.txt
export DJANGO_SETTINGS_MODULE="drams.local-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
cd "$FAIR_HOME"/scripts || exit
./rebuild-local.sh
