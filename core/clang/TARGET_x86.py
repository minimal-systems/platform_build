import os
import platform

from llvm_env import *

TARGET_LIBPROFILE_RT = os.path.join(llvm_rtlib_path, "libclang_rt.profile.a")
TARGET_LIBCRT_BUILTINS = os.path.join(llvm_rtlib_path, "libclang_rt.builtins.a")

# For AddressSanitizer on Linux, use the -fsanitize=address flag
ASAN_CFLAGS = "-fsanitize=address"
ASAN_LDFLAGS = "-fsanitize=address"


def setup_build():
    print("Target LibProfile Runtime:", TARGET_LIBPROFILE_RT)
    print("Target LibCRT Builtins:", TARGET_LIBCRT_BUILTINS)
    print("AddressSanitizer Compilation Flags:", ASAN_CFLAGS)
    print("AddressSanitizer Linker Flags:", ASAN_LDFLAGS)


if __name__ == "__main__":
    setup_build()
