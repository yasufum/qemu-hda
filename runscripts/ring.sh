#!/bin/bash

QEMU=$HOME/dpdk-home/qemu-2.3.0/x86_64-softmmu/qemu-system-x86_64
HDA=ubuntu-16.04-server-amd64-ring.qcow2
MEMSIZE=2048
CORES=4

NOF_IF=1  # Number of NICs (Don't change withou you've any reason)
QEMU_IVSHMEM=/tmp/ivshmem_qemu_cmdline_pp_ivshmem
VM_ID=$1

# Check if VM_ID is invalid
if [ ! ${VM_ID} ]; then
  VM_ID=1
elif [ ${VM_ID} -gt 9 ]; then
  VM_ID=9
fi

VM_HOSTNAME=spp-ring${VM_ID}

# $WORKDIR is set to the directory of this script.
WORKDIR=$(cd $(dirname $0); pwd)

# Prepare image for the VM
mkdir -p ${WORKDIR}/img
HDA_INST=${WORKDIR}/img/ring${VM_ID}-${HDA}
if [ ! -e ${HDA_INST} ]; then 
  echo "[ring.sh] Preparing image:"
  echo "          "${HDA_INST}"..."
  cp ${WORKDIR}/${HDA} ${HDA_INST}
fi

# Maximum number of NIC
# there're no reason for 5 but it's consideralbe
if [ $NOF_IF -gt 5 ] ; then
  NOF_IF=5
fi

# Setup network interfaces
NIC_OPT=""
for ((i=0; i<${NOF_IF}; i++)); do
  TMP_MAC=00:AD:BE:EF:0${VM_ID}:0${i}
  TMP_NETDEV=net_r${VM_ID}_${i}
  NIC_OPT=${NIC_OPT}"-device e1000,netdev=${TMP_NETDEV},mac=${TMP_MAC} "
  NIC_OPT=${NIC_OPT}"-netdev tap,id=${TMP_NETDEV},ifname=${TMP_NETDEV},script=../ifscripts/qemu-ifup.sh "
done

# Prepare QEMU option for DPDK.
device_opt=$( cat ${QEMU_IVSHMEM} )

# For QEMU monitor
TELNET_PORT=4440${VM_ID}

#
echo "[ring.sh] Boot "${VM_HOSTNAME}" with image:"
echo "          "${HDA_INST}
echo "[ring.sh] QEMU option for DPDK:"
echo "          "${device_opt}
echo "[ring.sh] telnet port: "${TELNET_PORT}

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
  ${device_opt} \
  -nographic \
  -monitor telnet::${TELNET_PORT},server,nowait
