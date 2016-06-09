#!/bin/bash

# get spp for qemu
https://github.com/garogers01/soft-patch-panel.git

# get vm img
wget https://people.debian.org/~aurel32/qemu/amd64/debian_wheezy_amd64_standard.qcow2

# install packages for compiling qemu
for pkg in libtool zlib1g-dev libglib2.0-dev dh-autoreconf
do
  sudo apt-get install ${pkg}
done
