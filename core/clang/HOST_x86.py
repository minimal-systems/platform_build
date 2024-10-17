from llvm_env import llvm_rtlib_path, clang_2nd_arch_prefix
# Define the variables similar to the Makefile
HOST_LIBPROFILE_RT = llvm_rtlib_path + "/libclang_rt.profile.a"
HOST_LIBCRT_BUILTINS = llvm_rtlib_path + "/libclang_rt.builtins.a"

# Add the prefix if necessary
HOST_LIBPROFILE_RT = clang_2nd_arch_prefix + HOST_LIBPROFILE_RT
HOST_LIBCRT_BUILTINS = clang_2nd_arch_prefix + HOST_LIBCRT_BUILTINS

print("HOST_LIBPROFILE_RT:", HOST_LIBPROFILE_RT)
print("HOST_LIBCRT_BUILTINS:", HOST_LIBCRT_BUILTINS)
