#!/bin/bash

HDA=ubuntu-16.04-server-amd64.qcow2
ISO=ubuntu-16.04-server-amd64.iso
FORMAT=qcow2
HDASIZE=10G

qemu-img create -f ${FORMAT} ${HDA} ${HDASIZE}

qemu-system-x86_64 \
  -cdrom ${ISO} \
  -hda ${HDA} \
  -m 2048 \
  -boot d
