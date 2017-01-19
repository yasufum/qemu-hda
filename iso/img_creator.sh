#!/bin/bash

# Specify name of image file
HDA=ubuntu-16.04-server-amd64.qcow2

# params for install
CORES=4
MEMSIZE=4096

# params for create image
ISO=ubuntu-16.04-server-amd64.iso
HDASIZE=8G
FORMAT=qcow2

# Create image
qemu-img create -f ${FORMAT} ${HDA} ${HDASIZE}

# Install in graphical mode
qemu-system-x86_64 \
  -cdrom ${ISO} \
  -hda ${HDA} \
  -m ${MEMSIZE} \
  -smp cores=${CORES},threads=1,sockets=1 \
  -boot d
