


INSTALLED_RAMDISK_HEADERS=$(TARGET_PRODUCT_OUT)/usr/include/header-$(TARGET_KERNEL_HEADERS_VERSION).tar
$(INSTALLED_RAMDISK_HEADERS):
	@mkdir -p $(TARGET_PRODUCT_OUT)/system/usr/include
	@mkdir -p $(TARGET_PRODUCT_OUT)/obj/ETC/include/generated
	@echo -e $(BOLD)"Generating kernel headers..."${CL_RST}
	@build/tools/bin/gen_headers
	@echo -e $(BOLD)"Compressing kernel headers..."${CL_RST}
	@cd $(TARGET_PRODUCT_OUT)/obj/ETC/ && tar -Jcf $(INSTALLED_RAMDISK_HEADERS) include
	@cd $(BUILD_TOP)
.PHONY: $(INSTALLED_RAMDISK_HEADERS)


# for custom bootloader targets
BOOTLOADER_PATCH_DIR=$(TARGET_PRODUCT_OUT)/obj/ETC/bootloader_patch_indeterminates
