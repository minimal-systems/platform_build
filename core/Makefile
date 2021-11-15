# Put some miscellaneous rules here
# Build system colors

# BUILD_VERSION
BUILD_VERSION=1.0
BUILD_GIT_ID=-$(shell git rev-parse --short HEAD)

BUILD_VERSION_FULL=$(BUILD_VERSION)$(BUILD_GIT_ID)


ifneq ($(BUILD_WITH_COLORS),0)
  CL_RED="\033[31m"
  CL_GRN="\033[32m"
  CL_YLW="\033[33m"
  CL_BLU="\033[34m"
  CL_MAG="\033[35m"
  CL_CYN="\033[36m"
  CL_RST="\033[0m"
  BOLD="\e[1m"
  NEWLINE="\e[1A\e[K"
endif

# Generate Internal Build keys
INTERNAL_BUILD_KEYS=$(TARGET_PRODUCT_OUT)/obj/ETC/signing/build.key
$(INTERNAL_BUILD_KEYS):
	@echo -e $(BOLD) $(NEWLINE)"//build/tools internel_key_gen"${CL_RST}
	@mkdir -p $(TARGET_PRODUCT_OUT)/obj/ETC/signing
	@openssl req -nodes -x509 -sha256 -newkey rsa:4096 -keyout "$(TARGET_PRODUCT_OUT)/obj/ETC/signing/build.key" -out "$(TARGET_PRODUCT_OUT)/obj/ETC/signing/$(TARGET_DEVICE)_$(HOST_BUILD_TYPE)_cert.key" -days 768 -subj "/C=US/ST=California/L=Mountain View/O=ANDROID /OU=Android" > /dev/null 2>&1
.PHONY:$(INTERNAL_BUILD_KEYS)

dump_vars:
	@echo ============================================
	@echo BUILD_TOP=$(BUILD_TOP)
	@echo PLATFORM_VERSION_CODENAME=$(PLATFORM_VERSION_CODENAME)
	@echo PLATFORM_VERSION=$(PLATFORM_VERSION)
	@echo TARGET_PRODUCT=$(TARGET_PRODUCT)
	@echo TARGET_BUILD_VARIANT=$(TARGET_BUILD_VARIANT)
	@echo TARGET_BUILD_TYPE=$(TARGET_BUILD_TYPE)
	@echo TARGET_ARCH=$(TARGET_ARCH)
	@echo TARGET_ARCH_VARIANT=$(TARGET_ARCH_VARIANT)
	@echo TARGET_CPU_VARIANT=$(TARGET_CPU_VARIANT)
	@echo HOST_ARCH=$(HOST_ARCH)
	@echo HOST_2ND_ARCH=$(HOST_2ND_ARCH)
	@echo HOST_OS=$(HOST_OS)
	@echo HOST_OS_EXTRA=$(HOST_OS_EXTRA)
	@echo HOST_CROSS_2ND_ARCH=x86_64
	@echo HOST_BUILD_TYPE=$(HOST_BUILD_TYPE)
	@echo BUILD_ID=$(BUILD_ID)
	@echo OUT_DIR=out
	@echo ============================================


OWNER=--owner=0 --group=0
ifeq ($(TARGET_BOOT_FORMAT),LZMA)
TAR=tar --lzma -Jcfh
IMG_END=lz4
else
TAR=tar -cvf
IMG_END=img
endif

clean:
	$(info Sucessfully cleaned files in out directory)
	@ rm -rf out


INSTALLED_RAMDISK_HEADERS=$(TARGET_PRODUCT_OUT)/system/usr/include/header-$(TARGET_KERNEL_HEADERS_VERSION).tar
$(INSTALLED_RAMDISK_HEADERS):
	@mkdir -p $(TARGET_PRODUCT_OUT)/system/usr/include
	@mkdir -p $(TARGET_PRODUCT_OUT)/obj/ETC/include/generated
	@echo -e $(BOLD)"Generating kernel headers..."${CL_RST}
	@build/tools/bin/gen_headers
	@echo -e $(BOLD)"Compressing kernel headers..."${CL_RST}
	@cd $(TARGET_PRODUCT_OUT)/obj/ETC/ && tar -Jcf $(INSTALLED_RAMDISK_HEADERS) include
	@cd $(BUILD_TOP)
.PHONY: $(INSTALLED_RAMDISK_HEADERS)

build_target:
	@ rm -rf out
	@ mkdir -p out
	@ /bin/bash -c ./build/envsetup.sh
	@ make $(SOONG_UI)
	@cp -r $(BUILD_TOP)/build/tools out/soong/tools/
	@make $(INTERNAL_BUILD_KEYS)
	@python $(BUILD_TOP)/build/make/tools/generate_folders.py
	@ /bin/bash -c ./build/make/core/make_modules.sh

TARGET_INSTALL_PRODUCT_COPY_FILES=$(PRODUCT_COPY_FILES)
$(TARGET_INSTALL_PRODUCT_COPY_FILES):
	@cp -r $(TARGET_INSTALL_PRODUCT_COPY_FILES)
	@echo

# for custom bootloader targets
BOOTLOADER_PATCH_DIR=$(TARGET_PRODUCT_OUT)/obj/ETC/bootloader_patch_indeterminates



FILE_NAME_TAG := eng.$(USER)
name := $(TARGET_PRODUCT)
ifeq ($(TARGET_BUILD_TYPE),debug)
  name := $(name)_debug
endif
name := $(name)-ota-$(FILE_NAME_TAG)

OTA_OBJ=$(TARGET_PRODUCT_OUT)/obj/PACKAGING
META_DIR=$(OTA_OBJ)/META-INF/com/google/android
INTERNAL_OTA_PACKAGE_TARGET := $(TARGET_PRODUCT_OUT)/$(name).zip
$(INTERNAL_OTA_PACKAGE_TARGET):
	@exec $(BUILD_TOP)/build/tools/bin/fileslist  $(TARGET_ROOT_OUT) > $(TARGET_PRODUCT_OUT)/installed_files_system.json
ifeq ($(BUILD_VENDOR_IMAGE),true)
	@exec $(BUILD_TOP)/build/tools/bin/fileslist  $(TARGET_VENDOR_OUT) > $(TARGET_PRODUCT_OUT)/installed_files_vendor.json
endif
	@mkdir -p $(OTA_OBJ)/images
ifeq ($(TARGET_ARCH),x86_64)
# store additonal images to the images directory for generic targets
	@cp -r $(TARGET_PRODUCT_OUT)/efi.img $(OTA_OBJ)/images
	@cp -r $(TARGET_PRODUCT_OUT)/$(TARGET_DEVICE)_preloader.bin $(OTA_OBJ)/images
	@cp -r $(TARGET_PRODUCT_OUT)/$(TARGET_DEVICE)_bootloader.bin $(OTA_OBJ)/images
endif
	@mkdir -p $(META_DIR)
	@echo "generating updater script..."
	@cat $(SYSTEM_OTA_SCRIPT) $(EXTRA_SYSTEM_UPDATER_SCRIPT) $(CUSTOM_UPDATER_SCRIPT)> $(META_DIR)/updater_script
	@python $(BUILD_TOP)/build/make/tools/generate_ota.py
	@echo -e ${BOLD}"target ota package $@"${CL_RST}
.PHONY:$(INTERNAL_OTA_PACKAGE_TARGET)
bacon: \
dump_vars \
build_target \
build_modules \
$(INSTALLED_DEFAULT_PROP_TARGET) \
$(INSTALLED_DEFAULT_PROP)  \
$(INSTALLED_RAMDISK_HEADERS) \
$(INTERNAL_OTA_PACKAGE_TARGET) \
