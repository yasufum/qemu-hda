#!/bin/bash

QEMU=../soft-patch-panel/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64
HDA=debian_wheezy_amd64_standard.qcow2

sudo ${QEMU} \
  -cpu host \
  -enable-kvm \
  -object memory-backend-file,id=mem,size=2048M,mem-path=/dev/hugepages,share=on \
  -numa node,memdev=mem \
  -mem-prealloc \
  -hda ${HDA} \
  -m 2048 \
  -smp cores=4,threads=1,sockets=1 \
  -device e1000,netdev=net0,mac=DE:AD:BE:EF:00:01 \
  -netdev tap,id=net0,ifname=net0,script=./ifscripts/qemu-ifup.sh \
  -device ivshmem,size=2048M,shm=fd:/dev/hugepages/rtemap_0:0x0:0x40000000:/dev/zero:0x0:0x3fffc000:/var/run/.dpdk_ivshmem_metadata_pp_ivshmem:0x0:0x4000 \
  -nographic
