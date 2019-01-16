#!/bin/bash

###
# Create and setup HDA file
#

#set -x

# Default params
CORES=4
MEMSIZE=4096
HDASIZE=10G
FORMAT=qcow2  # HDA format

U_VER="18.04.1.0-live"
U_TARGET="server"

DL_ONLY=0

# Parsing args
# option:
#   -v : version of Ubuntu
#   -d : only download iso
#   -i : path of iso for booting VM
#   -s : size of HDA file
#   -f : format of HDA (default is qcow2)
#   -c : number of cores of VM
#   -m : mem size of VM
#   -h : show help message
#   --help : show help message
#   --kvm : enable kvm
#   --nographic : install via CUI

CMD_OPTS="[-d] [-i ISO] [-v DIST_VER] [-t TARGET] [-s HDASIZE]"
CMD_OPTS=${CMD_OPTS}" [-f FORMAT] [-c CORES] [-m MEMSIZE] [-h]"
CMD_OPTS=${CMD_OPTS}" [--help] [--kvm] [--nographic]"

function show_help() {
    echo "Usage: ${CMDNAME} ${CMD_OPTS}"
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
            kvm)
                KVM="-enable-kvm";;
            nographic)
                NO_GRAPHIC="-nographic -device sga";;
        esac;;
    "d" ) DL_ONLY=1;;
    "i" ) ISO=${OPTARG};;
    "v" ) U_VER=${OPTARG};;
    "t" ) U_TARGET=${OPTARG};;
    "s" ) HDASIZE=${OPTARG};;
    "f" ) FORMAT=${OPTARG};;
    "c" ) CORES=${OPTARG};;
    "m" ) MEMSIZE=${OPTARG};;
    "h" ) show_help;;
      * ) show_invalid;;
  esac
done

# Parse major and minor versions, e.g. "18.04.01" => "18 04"
vers=($(echo "${U_VER}" | tr '-' ' '))
vers=${vers[0]}
vers=($(echo "${vers}" | tr '.' ' '))

# Default iso file
ISO_FILE=ubuntu-${U_VER}-${U_TARGET}-amd64.iso
URL=http://releases.ubuntu.com/${vers[0]}.${vers[1]}/${ISO_FILE}

PROJ_DIR=`dirname ${0}`/..

echo $URL
# Assign default val if not given
if [ -e ${ISO} ]; then
  ISO=${PROJ_DIR}/iso/${ISO_FILE}
fi

# Download iso if not exist
echo "Downloading iso file..."
wget -c -P ${PROJ_DIR}/iso ${URL}

if [ ${DL_ONLY} -eq 1 ]; then
  echo "Finish downloading!"
  exit 0
fi

# Name of HDA is defined as same as ISO
HDA=${PROJ_DIR}/hda/${ISO_FILE%.*}.${FORMAT}

# Create HDA image
qemu-img create -f ${FORMAT} ${HDA} ${HDASIZE}

echo ${NO_GRAPHIC}

# Install OS in graphical mode
qemu-system-x86_64 ${KVM} ${NO_GRAPHIC} \
  -cdrom ${ISO} \
  -hda ${HDA} \
  -m ${MEMSIZE} \
  -smp cores=${CORES},threads=1,sockets=1 \
  -boot d
