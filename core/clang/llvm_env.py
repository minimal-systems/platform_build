import os
import platform

# Set base paths and versions
llvm_prebuilts_base = "prebuilts/clang/host"
llvm_prebuilts_version = "clang-stable"
llvm_release_version = "19"

# Determine the OS automatically
build_os = "darwin" if platform.system() == "Darwin" else "linux"

# Determine the architecture automatically
arch = platform.machine()
if arch == "x86_64":
    target_triple = "x86_64-unknown-linux-gnu"
else:
    target_triple = f"{arch}-unknown-linux-gnu"

clang_2nd_arch_prefix = os.environ.get('TARGET_2ND_ARCH')

# Construct the llvm-readobj path
llvm_readobj = (
    f"{llvm_prebuilts_base}/{build_os}-{arch}/{llvm_prebuilts_version}/bin/llvm-readobj"
)

# Construct the runtime library path
llvm_rtlib_path = (
    f"{llvm_prebuilts_base}/{build_os}-{arch}/{llvm_prebuilts_version}/lib/clang/"
    f"{llvm_release_version}/lib/{target_triple}/"
)

# Construct the full prebuilt path
llvm_prebuilts_path = (
    f"{llvm_prebuilts_base}/{build_os}-{arch}/{llvm_prebuilts_version}/"
)