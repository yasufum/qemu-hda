#!/bin/bash

QEMU=../soft-patch-panel/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64
HDA=images/debian_wheezy_amd64_standard.qcow2
#HDA=debian_wheezy_amd64_standard.qcow2

sudo ${QEMU} \
  -cpu host \
  -enable-kvm \
  -object memory-backend-file,id=mem,size=2048M,mem-path=/dev/hugepages,share=on \
  -numa node,memdev=mem \
  -mem-prealloc \
  -hda ${HDA} \
  -m 2048 \
  -smp cores=4,threads=1,sockets=1 \
  -device e1000,netdev=net3,mac=DE:AD:BE:EF:00:03 \
  -netdev tap,id=net3,ifname=net3,script=./ifscripts/qemu-ifup.sh \
  -chardev socket,id=chr0,path=/tmp/sock0 \
  -netdev vhost-user,id=net4,chardev=chr0,vhostforce \
  -device virtio-net-pci,netdev=net4 \
  -nographic \
  -vnc :2
