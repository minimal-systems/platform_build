MAKEFILES=$(find * -name "Makefile" | sed 's/Makefile//g')
MAKE_CMD=make -C
MAKE=$(MAKE_CMD)
build_modules:
#	@$(MAKE) $(MAKEFILES)
	@$(MAKE) bionic
	@make recovery -C bootable/recovery/
	@$(MAKE) bootable/recovery/crypto_updater
	@$(MAKE) bootable/recovery/update_engine
	@$(MAKE) system/core/init
	@$(MAKE) system/core/rootdir/
	@$(MAKE) system/core/varible/
# disable until build is fixed 
	@$(MAKE) external/toybox
	@$(MAKE) external/kmod
	@external/toybox/install.sh vendor_toybox
	@external/toybox/install.sh system_toybox
	@external/toybox/install.sh recovery_toybox
	@$(MAKE) external/bash
	@$(MAKE) external/dialog
	@$(MAKE) external/7z
	@make $(VENDOR_TOYBOX)
	@make -f external/zip/Android.mk
	@make -f external/pigz/Android.mk
	@$(MAKE) external/unzip
	@$(MAKE) system/sepolicy
	@$(MAKE) vendor/magisk
	@$(MAKE) vendor/intel
	@$(MAKE) packages/apps/pacman4console
	@$(MAKE) vendor/intel/bootable/preloader
	@$(MAKE) vendor/intel/bootable/bootloader


VENDOR_TOYBOX=$(TARGET_VENDOR_OUT)/bin/toybox_vendor
$(VENDOR_TOYBOX):
	@cp -r $(TARGET_PRODUCT_OUT)/obj/EXECUTABLES/toybox_indeterminates/LINKED/toybox $(VENDOR_TOYBOX)
.PHONY: $(VENDOR_TOYBOX)
