echo $(pwd) > /tmp/build_top
export BUILD_TOP=$(cat /tmp/build_top)
export TOP=$BUILD_TOP
#. $BUILD_TOP/build/tools/envsetup.sh
source $TOP/device/build/ninja/env.sh
export ANDROID_BUILD_TOP=$(gettop)
export PLATFORM_VERSION_CODENAME=REL
export PLATFORM_VERSION=11
export TARGET_DEVICE=generic
export TARGET_PRODUCT=aosp_generic
export TARGET_BUILD_VARIANT=userdebug
export TARGET_BUILD_TYPE=prod
export TARGET_ARCH=x86_64
export TARGET_ARCH_VARIANT=
export TARGET_CPU_VARIANT=
export HOST_ARCH=x86_64
export HOST_2ND_ARCH=x86
export HOST_OS=linux
export HOST_CROSS_OS=windows
export HOST_CROSS_ARCH=x86
export TARGET_INTEL_PLATFORM= ${TARGET_BOARD_PLATFORM}
export HOST_CROSS_2ND_ARCH=x86_64
export HOST_BUILD_TYPE=release
export BUILD_ID=QP3A.190801.070
export OUT_DIR=$BUILD_TOP/out
export TARGET_PRODUCT_OUT=$OUT_DIR/target/product/$TARGET_DEVICE
export TARGET_ROOT_OUT=$TARGET_PRODUCT_OUT/root
export TARGET_RECOVERY_OUT=$TARGET_PRODUCT_OUT/recovery/root
export TARGET_SYSTEM_OUT=$TARGET_PRODUCT_OUT/system
export TARGET_VENDOR_OUT=$TARGET_PRODUCT_OUT/vendor
export TARGET_ODM_OUT=$TARGET_ROOT_OUT/vendor/odm
export TARGET_OBJ=$TARGET_PRODUCT_OUT/obj
export TARGET_BOOT_FLAGS=${CPPFLAGS}
export BUILD_EXECUTABLE=$BUILD_TOP/build/make/core/executable.mk
export BUILD_SHARED_LIBRARY=$BUILD_TOP/build/make/core/library.mk
export BUILD_SYSTEM_SHARED_LIBRARY=$BUILD_TOP/build/make/core/library_sys.mk
export BOOTABLE_TARGET=$BUILD_TOP/build/make/core/bootable_target.mk
#alias echo='echo -e'
