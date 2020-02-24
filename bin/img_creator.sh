#!/bin/bash

###
# Create and setup HDA file
#

CMD_NAME="img_creator.sh"

# Default params
CORES=4
MEMSIZE=4096
HDASIZE=12
FORMAT=qcow2  # HDA format
DIST_VER="18.04.4"
DIST_TARGET="server"

DL_ONLY=0
USE_VIRSH=1
ENABLE_KVM="-enable-kvm"
ENABLE_DEBUG=0

function make_help() {
    CMD_OPTS="NAME\n"
    CMD_OPTS=${CMD_OPTS}"\t"${CMD_NAME}" - setup vm image\n"
    CMD_OPTS=${CMD_OPTS}"\n"

    CMD_OPTS=${CMD_OPTS}"SYNOPSIS\n"
    CMD_OPTS=${CMD_OPTS}"\t${CMD_NAME} [-d] [-i ISO] [-v DIST_VER] [-t TARGET] [-s HDASIZE]\n"
    CMD_OPTS=${CMD_OPTS}"\t[-f FORMAT] [-c CORES] [-m MEMSIZE] [-h]\n"
    CMD_OPTS=${CMD_OPTS}"\t[--hda FORMAT] [--no-kvm] [--graphic] [--help]\n\n"

    CMD_OPTS=${CMD_OPTS}"DESCRIPTION\n"
    CMD_OPTS=${CMD_OPTS}"\t-d : only download ISO\n"
    CMD_OPTS=${CMD_OPTS}"\t-i : path of ISO for booting VM\n"
    CMD_OPTS=${CMD_OPTS}"\t-v : version of Ubuntu\n"
    CMD_OPTS=${CMD_OPTS}"\t-t : target (ubuntu)\n"
    CMD_OPTS=${CMD_OPTS}"\t-s : size of HDA file\n"
    CMD_OPTS=${CMD_OPTS}"\t-f or --hda: format of HDA (default is qcow2)\n"
    CMD_OPTS=${CMD_OPTS}"\t-c : number of cores of VM\n"
    CMD_OPTS=${CMD_OPTS}"\t-m : mem size of VM\n"
    CMD_OPTS=${CMD_OPTS}"\t-h : show help message\n"
    CMD_OPTS=${CMD_OPTS}"\t--no-kvm : disable kvm\n"
    CMD_OPTS=${CMD_OPTS}"\t--graphic : install via GUI\n"
    CMD_OPTS=${CMD_OPTS}"\t--help : show help message"
}

function show_help() {
    make_help
    echo -e "${CMD_OPTS}"
    exit 0
}

function show_invalid() {
    echo "Usage: ${CMDNAME} ${CMD_OPTS}" 1>&2
    exit 1
}

while getopts di:v:t:s:f:c:m:h-: OPT
do
  case ${OPT} in
    "-")
        case ${OPTARG} in
            help)
                show_help;;
            hda)
                FORMAT=${OPTARG};;
            no-kvm)
                ENABLE_KVM=;;
            graphic)
                USE_VIRSH=0;;
            debug)
                ENABLE_DEBUG=1;;
        esac;;
    "d" ) DL_ONLY=1;;
    "i" ) ISO=${OPTARG};;
    "v" ) DIST_VER=${OPTARG};;
    "t" ) DIST_TARGET=${OPTARG};;
    "s" ) HDASIZE=${OPTARG};;
    "f" ) FORMAT=${OPTARG};;
    "c" ) CORES=${OPTARG};;
    "m" ) MEMSIZE=${OPTARG};;
    "h" ) show_help;;
      * ) show_invalid;;
  esac
done

if [ ${ENABLE_DEBUG} -eq 1 ]; then
    set -x
fi

# Parse major and minor versions, e.g. "18.04.01" => "18 04"
vers=($(echo "${DIST_VER}" | tr '-' ' '))
vers=${vers[0]}
vers=($(echo "${vers}" | tr '.' ' '))

VMNAME=spp-ubuntu-${DIST_VER}-${DIST_TARGET}

# Default ISO file
ISO_FILE=ubuntu-${DIST_VER}-${DIST_TARGET}-amd64.iso

# TODO(yasufum) Revise checking for versions.
if [ ${vers[0]} = 18 ]; then
    URL=http://cdimage.ubuntu.com/releases/${DIST_VER}/release/${ISO_FILE}
elif [ ${vers[0]} = 16 ]; then
    URL=http://releases.ubuntu.com/${vers[0]}.${vers[1]}/${ISO_FILE}
else
    echo "This tool supports only Ubuntu 16.04 or 18.04 LTS."
    exit 0
fi

PROJ_DIR=`dirname ${0}`/..

# Assign default val if not given
if [ -e ${ISO} ]; then
  ISO=${PROJ_DIR}/iso/${ISO_FILE}
fi

# Download ISO if not exist
echo "Downloading ISO file..."
wget -c -P ${PROJ_DIR}/iso ${URL}

if [ ${DL_ONLY} -eq 1 ]; then
  echo "Finish downloading!"
  exit 0
fi

# Name of HDA is defined as same as ISO
HDA=${PROJ_DIR}/hda/${ISO_FILE%.*}.${FORMAT}

# Create HDA image
qemu-img create -f ${FORMAT} ${HDA} ${HDASIZE}G

if [ ${USE_VIRSH} -eq 1 ]; then
    #sudo virsh undefine ${VMNAME}
    sudo virt-install \
        --connect=qemu:///system \
        --name ${VMNAME} \
        --ram ${MEMSIZE} \
        --disk path=${HDA},size=${HDASIZE},format=${FORMAT} \
        --vcpus=${CORES} \
        --os-type linux \
        --os-variant=ubuntu${vers[0]}.${vers[1]} \
        --network network=default \
        --nographics \
        --extra-args='console=tty0 console=ttyS0,115200n8' \
        --location ${ISO}
    sudo chown ${USER} ${HDA}
else
     # Install OS in graphical mode
     sudo qemu-system-x86_64 ${ENABLE_KVM} \
         -cdrom ${ISO} \
         -hda ${HDA} \
         -m ${MEMSIZE} \
         -smp cores=${CORES},threads=1,sockets=1 \
         -boot d
fi
