#!/bin/bash

###
# Init HDA file and boot VM for install ISO img
# 

while getopts i:s:f:c:m:h OPT
do
  case ${OPT} in
    "i" ) ISO=${OPTARG};;
    "s" ) HDASIZE=${OPTARG};;
    "f" ) FORMAT=${OPTARG};;
    "c" ) CORES=${OPTARG};;
    "m" ) MEMSIZE=${OPTARG};;
    "h" ) echo "Usage: ${CMDNAME} [-i ISO] [-s HDASIZE] [-c CORES] [-m MEMSIZE]"
          exit 0;;
      * ) echo "Usage: ${CMDNAME} [-i ISO] [-s HDASIZE] [-c CORES] [-m MEMSIZE]" 1>&2
          exit 1;;
  esac
done

if [ -e ${ISO}]; then
  ISO=ubuntu-16.04.2-server-amd64.iso
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

HDA=${ISO%.*}.${FORMAT}


# Create image
qemu-img create -f ${FORMAT} ${HDA} ${HDASIZE}

# Install in graphical mode
qemu-system-x86_64 \
  -cdrom ${ISO} \
  -hda ${HDA} \
  -m ${MEMSIZE} \
  -smp cores=${CORES},threads=1,sockets=1 \
  -boot d
