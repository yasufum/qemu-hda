# HDA files directory

## Directory structure

hda directory is for containing templates, instances and original of
them.

  - original: DPDK is not installed.
  - template: Copied from original and DPDK+SPP is installed.
  - instance: Copied from template for each of SPP secondaries.

For example, `ubuntu-16.04.2-server-amd64.qcow2` and its children are
placed like as following.

```
hda
├── README.md
├── instances
│   └── n1-ubuntu-16.04.2-server-amd64.qcow2
├── templates
│   └── n0-ubuntu-16.04.2-server-amd64.qcow2
└── ubuntu-16.04.2-server-amd64.qcow2
```

You generate original with `img_creator.sh`. Then templates and
instances with `run-vm.py`.
