#!/bin/sh

br=virbr0

echo "Removing $1 to ${br}..."
brctl delif ${br} $1
echo "Shutting down $1..."
ifconfig $1 down
