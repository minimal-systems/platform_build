from llvm_env import *
# Define the variables similar to the Makefile
HOST_LIBPROFILE_RT = llvm_rtlib_path + "/libclang_rt.profile.a"
HOST_LIBCRT_BUILTINS = llvm_rtlib_path + "/libclang_rt.builtins.a"

# Add the prefix if necessary
HOST_LIBPROFILE_RT = clang_2nd_arch_prefix + HOST_LIBPROFILE_RT
HOST_LIBCRT_BUILTINS = clang_2nd_arch_prefix + HOST_LIBCRT_BUILTINS
