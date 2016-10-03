### What is this?

Setup tools for creating and running VMs for SPP.


### How to use

#### (1) Get ISO file.

This tools support Ubuntu (I've tested only 16.04, but 14.04 possibly run).
Download ISO file form Ubuntu's web page.
[Here](iso/iso-list.txt) is a list of url.


#### (2) Create VM

Put ISO file you downloaded into iso/ to be refered from script.

Then, move to iso/ and edit, run create_install.sh script.
There are four params in the script.
  - HDA: name of image file of VM.
  - ISO: name of ISO you downloaded.
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


#### (3) Setup QEMU

Before run VM using this tool, you have to setup specialized qemu
for running DPDK with IVSHMEM.
Currently it's included in repository of
previous version of SPP (https://github.com/garogers01/soft-patch-panel).

##### 3-1 Get source

Create a directory for download and get source from the repository.

```
$ mkdir [WORK_DIR]
$ cd  [WORK_DIR]
$ git clone https://github.com/garogers01/soft-patch-panel.git
```

##### 3-2 Compile

Move to `[WORK_DIR]` and run make command for compilation.

```
$ cd [WORK_DIR]/qemu-2.3.0
$ make
```

It would take a while to compile QEMU.
Compiled executable `qemu-system-x86_64` is placed in `[WORK_DIR]/qemu-2.3.0/x86_64-softmmu/`.


#### (4) Run VM

Now you can run VM of the image you created by using QEMU command with options.
But, you had better to use run scripts as following than input command and options by hand.

Copy image file into runscript/ which you created by running create_install.sh in previous section.

There are two scripts for running VM, ring.sh and vhost.sh, for your purpose (You might see other scripts, but there are no need).
SPP supports two types of resources to communicate with VMs.
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
