#!/bin/bash

QEMU=$HOME/dpdk-home/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64
HDA=ubuntu-16.04-server-amd64-vhost.qcow2
MEMSIZE=2048
CORES=4

sudo ${QEMU} \
  -cpu host \
  -enable-kvm \
  -object memory-backend-file,id=mem,size=${MEMSIZE}M,mem-path=/dev/hugepages,share=on \
  -numa node,memdev=mem \
  -mem-prealloc \
  -hda ${HDA} \
  -m ${MEMSIZE} \
  -smp cores=${CORES},threads=1,sockets=1 \
  -device e1000,netdev=net0,mac=DE:AD:BE:EF:00:01 \
  -netdev tap,id=net0,ifname=net0,script=../ifscripts/qemu-ifup.sh \
  -chardev socket,id=chr0,path=/tmp/sock5 \
  -netdev vhost-user,id=net1,chardev=chr0,vhostforce \
  -device virtio-net-pci,netdev=net1 \
  -monitor telnet::4444,server,nowait \
  -nographic
#  -netdev tap,id=net0,ifname=net0,script=../ifscripts/qemu-ifup.sh \
