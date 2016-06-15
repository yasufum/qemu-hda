### What is this?

Setup tools for creating and running VMs for SPP.


### How to use

#### (1) Get iso file.

This tools support Ubuntu (I've tested only 16.04, but 14.04 possibly run).
Download iso file form Ubuntu's web page.
[Here](iso/iso-list.txt) is a list of url.


#### (2) Create VM

Put iso file you downloaded into iso/ to be refered from script.

Then, move to iso/ and edit, run create_install.sh script.
There are four params in the script.
  - HDA: name of image file of VM.
  - ISO: name of iso you downloaded.
  - FORMAT: format type of image file. qcow2 is better if you use KVM.
  - HDASIZE: size of image file, 10G is adequate for ubuntu server.

Run the script as following.

```
$ bash create_install.sh
```

After run the script, QEMU opens another window for installation.
So, you install Ubuntu by following the instructions.

Finally, shutdown OEMU's window after finished installation by clicking close button of the window.
If you choose restart inside the window without close, QEMU attempts installation again.


#### (3) Run VM

[NOTE] Before run VM using this tool,
you have to setup specialized qemu
for running SPP and DPDK
which is contained in
previous version of SPP (https://github.com/garogers01/soft-patch-panel).

Copy image file into runscript/ which you created by running create_install.sh in previous section.

There are two scripts for running VM, ring.sh and vhost.sh for your purpose (You might see other scripts, but there are no need).
SPP supports two types of resources for running VMs.
Please refer [setup guide](http://dpdk.org/browse/apps/spp/tree/examples/multi_process/patch_panel/docs/setup_guide.md) of SPP for details.

Then edit and run the script.
There are several params in the script.
  - QEMU: location of specialized QEMU's exec file.
  - HDA: image file you created.

Run the script as following.

```
$ bash ring.sh

or 

$ bash vhost.sh
```
