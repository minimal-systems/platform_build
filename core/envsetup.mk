BUILD_EXECUTABLE=$(BUILD_TOP)/build/make/core/executable.mk
BUILD_SHARED_LIBRARY=$(BUILD_TOP)/build/make/core/library.mk
CLEAR_VARS=$(BUILD_TOP)/build/make/core/clear_vars.mk

TARGET_DEVICE=generic
TARGET_PRODUCT=aosp_generic
TARGET_BUILD_VARIANT=userdebug
TARGET_BUILD_TYPE=REL
TARGET_ARCH=x86_64
TARGET_ARCH_VARIANT=
TARGET_CPU_VARIANT=
FRAMEWORK_CLASSPATH=$(shell find * -name frameworks-*-stripped.jar)
OUT_DIR=$(BUILD_TOP)/out
TARGET_PRODUCT_OUT=$(BUILD_TOP)/out/target/product/$(TARGET_DEVICE)
TARGET_SYSTEM_OUT=$(TARGET_PRODUCT_OUT)/system
TARGET_ROOT_OUT=$(TARGET_PRODUCT_OUT)/root
TARGET_VENDOR_OUT=$(TARGET_PRODUCT_OUT)/vendor
TARGET_RECOVERY_OUT=$(TARGET_PRODUCT_OUT)/recovery/root
TARGET_ODM_OUT=$(TARGET_PRODUCT_OUT)/vendor/odm
BOOT_CMDLINE=$(BOOT_IMAGE_FLAGS)
date=$(shell date -u +%Y%m%d)
BUILD_DATE=$(date)
ANDROID_HOME=~/Android/Sdk
ANDROID_NDK_HOME=$(BUILD_TOP)/prebuilts/ndk



ifdef ($(MAKE_VERBOSE),true)
# verbose
MAKEFLAGS += -rRnvd
else
# non-verbose
MAKEFLAGS += -rR --no-print-directory
endif




include $(BUILD_TOP)/build/make/core/build_id.mk
include $(BUILD_TOP)/build/make/core/version_defaults.mk
include $(BUILD_TOP)/build/make/core/definitions.mk
include $(BUILD_TOP)/build/make/core/selinux.mk
include $(BUILD_TOP)/build/make/core/compiler.mk
include $(BUILD_TOP)/build/make/core/include.mk
include $(BUILD_TOP)/device/$(TARGET_DEVICE)/aosp_$(TARGET_DEVICE).mk
include $(BUILD_TOP)/device/$(TARGET_DEVICE)/Android.mk
-include $(BUILD_TOP)/vendor/$(TARGET_DEVICE)/*.mk
