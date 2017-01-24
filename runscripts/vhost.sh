#!/bin/bash

CORES=4
MEMSIZE=2048
HDA=ubuntu-16.04-server-amd64.qcow2
QEMU=$HOME/dpdk-home/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64

# Don't change withou you've any reason
VHOST_HDA=ov-${HDA}
NOF_IF=1  # Number of NICs (Don't change withou you've any reason)
VM_ID=$1

VM_HOSTNAME=sppv${VM_ID}

# $WORKDIR is set to the directory of this script.
WORKDIR=$(cd $(dirname $0); pwd)

# Prepare image for the VM
mkdir -p ${WORKDIR}/img
HDA_INST=img/v${VM_ID}-${VHOST_HDA}
# If you don't have vhost's image in current dir, create it to install vhost.
if [ ! -e ${VHOST_HDA} ]; then
  echo "[vhost.sh] You don't have any image for runninng vhost."
  echo "[vhost.sh] Please install SPP and setup for vhost."
  echo "[vhost.sh] First, you need to install python inside VM for ansible."
  cp ${WORKDIR}/${HDA} ${WORKDIR}/${VHOST_HDA}
  HDA_INST=${VHOST_HDA}
# If you have image in current dir, check img/ and create new image if
# instance doesn't exist.
elif [ ! -e ${HDA_INST} ]; then 
  echo "[vhost.sh] Preparing image:"
  echo "           "${HDA_INST}
  cp ${WORKDIR}/${VHOST_HDA} ${WORKDIR}/${HDA_INST}
  echo "[vhost.sh] Change hostname to "${VM_HOSTNAME}" for convenience."
  echo "           Run hostnamectl command inside VM as following"
  echo "           $ sudo hostnamectl set-hostname "${VM_HOSTNAME}
fi

# Maximum number of NIC
# there're no reason for 5 but it's consideralbe
if [ $NOF_IF -gt 5 ] ; then
  NOF_IF=5
fi

# Setup network interfaces
NIC_OPT=""
for ((i=0; i<${NOF_IF}; i++)); do
  TMP_MAC=00:AD:BE:EF:${VM_ID}:0${i}
  TMP_NETDEV=net_v${VM_ID}_${i}
  NIC_OPT=${NIC_OPT}"-device e1000,netdev=${TMP_NETDEV},mac=${TMP_MAC} "
  NIC_OPT=${NIC_OPT}"-netdev tap,id=${TMP_NETDEV},ifname=${TMP_NETDEV},script=../ifscripts/qemu-ifup.sh "
done

# NIC for vhost-user
NIC_VU=net_vu${VM_ID}

# Assign socket id which is used as SPP secondary id
SOCK_ID=${VM_ID}

# For QEMU monitor
TELNET_PORT=444${VM_ID}


#
echo "[vhost.sh] Boot "${VM_HOSTNAME}" with image:"
echo "           "${HDA_INST}
echo "[vhost.sh] telnet port: "${TELNET_PORT}

sudo ${QEMU} \
  -cpu host \
  -enable-kvm \
  -object memory-backend-file,id=mem,size=${MEMSIZE}M,mem-path=/dev/hugepages,share=on \
  -numa node,memdev=mem \
  -mem-prealloc \
  -hda ${HDA_INST} \
  -m ${MEMSIZE} \
  -smp cores=${CORES},threads=1,sockets=1 \
  ${NIC_OPT} \
  -chardev socket,id=chr0,path=/tmp/sock${SOCK_ID} \
  -netdev vhost-user,id=${NIC_VU},chardev=chr0,vhostforce \
  -device virtio-net-pci,netdev=${NIC_VU} \
  -monitor telnet::${TELNET_PORT},server,nowait
#  -nographic \
#  -netdev tap,id=net0,ifname=net0,script=../ifscripts/qemu-ifup.sh \
