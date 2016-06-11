#!/bin/sh

br=virbr0

echo "Bringing up $1 for bridged mode..."
ifconfig $1 0.0.0.0 promisc up
echo "Adding $1 to ${br}..."
brctl addif ${br} $1
