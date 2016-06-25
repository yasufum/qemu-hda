#!/bin/bash

QEMU=$HOME/dpdk-home/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64
HDA=ubuntu-16.04-server-amd64.qcow2
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
  -device e1000,netdev=net0,mac=DE:AD:BE:EF:00:00 \
  -netdev tap,id=net0,ifname=net0,script=../ifscripts/qemu-ifup.sh \
  -device e1000,netdev=net1,mac=DE:AD:BE:EF:00:01 \
  -netdev tap,id=net1,ifname=net1,script=../ifscripts/qemu-ifup.sh \
  -device e1000,netdev=net2,mac=DE:AD:BE:EF:00:02 \
  -netdev tap,id=net2,ifname=net2,script=../ifscripts/qemu-ifup.sh \
  -device e1000,netdev=net3,mac=DE:AD:BE:EF:00:03 \
  -netdev tap,id=net3,ifname=net3,script=../ifscripts/qemu-ifup.sh \
  -device ivshmem,size=${MEMSIZE}M,shm=fd:/dev/hugepages/rtemap_0:0x0:0x40000000:/dev/zero:0x0:0x3fffc000:/var/run/.dpdk_ivshmem_metadata_pp_ivshmem:0x0:0x4000 \
  -monitor telnet::4444,server,nowait \
  -nographic
