#!/bin/bash

#sudo ./x86_64-softmmu/qemu-system-x86_64 \
sudo qemu-system-x86_64 \
  -cpu host \
  -enable-kvm \
  -object memory-backend-file,id=mem,size=2048M,mem-path=/dev/hugepages,share=on \
  -numa node,memdev=mem \
  -mem-prealloc \
  -hda /home/dpdk/debian_wheezy_amd64_standard.qcow2 \
  -m 2048 \
  -smp cores=4,threads=1,sockets=1 \
  -device e1000,netdev=net0,mac=DE:AD:BE:EF:00:01 \
  -netdev tap,id=net0 \
  -nographic \
  -vnc :2
