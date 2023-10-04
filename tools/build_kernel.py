#!/usr/bin/env python

import os
import sys

build_top = os.environ.get("BUILD_TOP")
sys.path.append(f"{build_top}/build/make/core")
from envsetup import *


def generate_kernel_config(arch):
    print(f"generating kernel config for {arch}")
    os.system(f"make O={obj}/KERNEL_OBJ ARCH={arch} {target_defconfig}")
    os.system(f"make O={obj}/KERNEL_OBJ ARCH={arch} menuconfig")
    os.system(f"cp {obj}/KERNEL_OBJ/.config {kernel_out}/{arch}_config")
    print(f"kernel config generated for {arch}")


def build_kernel(arch):
    print(f"building kernel for {arch}")
    os.system(f"make O={obj}/KERNEL_OBJ ARCH={arch} -j$(nproc)")
    print(f"kernel build completed for {arch}")


archs = ["x86_64"]

for arch in archs:
    generate_kernel_config(arch)
    build_kernel(arch)

