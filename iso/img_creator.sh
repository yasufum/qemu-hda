#!/bin/bash

###
# Init HDA file and boot VM for install ISO img
# 

URL=http://releases.ubuntu.com/16.04/
ISO_FILE=ubuntu-16.04.2-server-amd64.iso
SRC_DIR=`dirname ${0}`

while getopts di:s:f:c:m:h OPT
do
  case ${OPT} in
    "d" ) wget -c -P ${SRC_DIR} ${URL}${ISO_FILE}
          exit 0;;
    "i" ) ISO=${OPTARG};;
    "s" ) HDASIZE=${OPTARG};;
    "f" ) FORMAT=${OPTARG};;
    "c" ) CORES=${OPTARG};;
    "m" ) MEMSIZE=${OPTARG};;
    "h" ) echo "Usage: ${CMDNAME} [-d] [-i ISO] [-s HDASIZE] [-c CORES] [-m MEMSIZE]"
          exit 0;;
      * ) echo "Usage: ${CMDNAME} [-d] [-i ISO] [-s HDASIZE] [-c CORES] [-m MEMSIZE]" 1>&2
          exit 1;;
  esac
done

if [ -e ${ISO} ]; then
  ISO=${SRC_DIR}/${ISO_FILE}
fi

if [ -e ${HDASIZE} ]; then
  HDASIZE=8G
fi

if [ -e ${FORMAT} ]; then
  FORMAT=qcow2
fi

if [ -e ${CORES} ]; then
  CORES=4
fi

if [ -e ${MEMSIZE} ]; then
  MEMSIZE=4096
fi

HDA=${SRC_DIR}/${ISO_FILE%.*}.${FORMAT}

# Create image
qemu-img create -f ${FORMAT} ${HDA} ${HDASIZE}

# Install in graphical mode
qemu-system-x86_64 \
  -cdrom ${ISO} \
  -hda ${HDA} \
  -m ${MEMSIZE} \
  -smp cores=${CORES},threads=1,sockets=1 \
  -boot d
