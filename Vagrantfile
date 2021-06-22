# -*- mode: ruby -*-
# vi: set ft=ruby :

#
# A VM can be created using the command "vagrant up"
#
# This will make a local version of the registry running in a VM.
# You can connect to the registry via http://192.168.20.10:8000
#

Vagrant.configure("2") do |config|

    config.vm.box = "bento/ubuntu-18.04"

    # sync folder containing data registry code
    config.vm.synced_folder ".", "/code/data-registry"

    config.vm.network "private_network", ip: "192.168.20.10"
    config.vm.network "forwarded_port", guest: 8000, host: 8000
    config.vm.provision :shell, inline: <<SHELL
set -x

mkdir -p /root/.ssh
cp ~vagrant/.ssh/authorized_keys /root/.ssh

apt-get update -y
apt-get install -y python3-venv graphviz

export SCRC_HOME=/code/data-registry
rm -rf "$SCRC_HOME"/venv
python3 -m venv "$SCRC_HOME"/venv
source "$SCRC_HOME"/venv/bin/activate

python -m pip install --upgrade pip wheel
python -m pip install -r "$SCRC_HOME"/local-requirements.txt

export DJANGO_SETTINGS_MODULE="drams.vagrant-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin

cd "$SCRC_HOME"/scripts || exit

./rebuild-local.sh
./run_scrc_server_vagrant

SHELL

end
