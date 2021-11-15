BOOTABLE_OBJ=$(TARGET_PRODUCT_OUT)/obj/BOOTABLE_IMAGES
OBJ_INCLUDE=$(TARGET_PRODUCT_OUT)/obj/BOOTABLE_IMAGES/$(LOCAL_MODULE)/include
LOCAL_C_INCLUDES=$(OBJ_INCLUDE)
INCLUDES=$(shell for inc in $(LOCAL_C_INCLUDES); do echo "-I$$inc"; done) $(shell echo $(cat out/.module_paths/EXPORT_INCLUDES ))
CPP_FLAGS=-fdiagnostics-color=always -pipe -D_FILE_OFFSET_BITS=64 -Winvalid-pch -Wnon-virtual-dtor
OBJ=$(BOOTABLE_OBJ)/$(LOCAL_MODULE)
OBJ_C_FOLDERS=$(shell for i in $(LOCAL_SRC_FILES) ; do echo $(OBJ)/$$i ;done)


# use clang for bootloaders
ifeq ($(LOCAL_CPP_CLANG),true)
CC=$(CCACHE) /usr/bin/clang++
COMPILER_NAME=clang++
else
CC=$(CCACHE) /usr/bin/clang
COMPILER_NAME=clang
endif

LOCAL_OBJS=$(shell for i in $(LOCAL_SRC_FILES) ; do echo $(BOOTABLE_OBJ)/$(LOCAL_MODULE)/$$i.o ;done)

include $(BUILD_TOP)/$(LOCAL_PATH)/target/$(TARGET_DEVICE)/defconfig
INSTALLED_BOOTABLE_TARGET=$(TARGET_PRODUCT_OUT)/$(TARGET_DEVICE)_$(LOCAL_MODULE).bin
$(INSTALLED_BOOTABLE_TARGET) :
	@mkdir -p $(BOOTABLE_OBJ)/$(LOCAL_MODULE)
	@sh $(BUILD_TOP)/$(LOCAL_PATH)/scripts/gen_conf
	@cp -r $(BUILD_TOP)/$(LOCAL_PATH)/include $(BOOTABLE_OBJ)/$(LOCAL_MODULE)
	@mkdir -p $(OBJ)
	@mkdir -p $(OBJ)/LINKED
	@for src_mkdir in $(LOCAL_SRC_FILES); do \
	mkdir -p $(OBJ)/$$src_mkdir ; \
	done
	@rm -rf $(OBJ_C_FOLDERS)
	@for src in $(LOCAL_SRC_FILES); do \
	$(CC) $(CPP_FLAGS)  $(INCLUDES) $(CFLAGS) -g -MD -MQ '$(OBJ)/'$$src.o  -MF '$(OBJ)/'$$src.o.d -o '$(OBJ)/'$$src.o -c $(BUILD_TOP)/$(LOCAL_PATH)/$$src && echo -e $(BOLD)"\e[1A\e[K //$(LOCAL_PATH):$(LOCAL_MODULE) $$COMPILER_NAME $$src"${CL_RST} ; \
	done
	@$(CC) -o $(OBJ)/LINKED/$(LOCAL_MODULE) $(LOCAL_OBJS)  -Wl,--as-needed $(LD_FLAGS) -Wl,--no-undefined
	@$(CC) -o $(INSTALLED_BOOTABLE_TARGET)  $(LOCAL_OBJS) -Wl,--as-needed $(LD_FLAGS) -Wl,--no-undefined
	@echo -e "\e[1A\e[Ksigning $(LOCAL_MODULE)..."
	@mkdir -p $(TARGET_PRODUCT_OUT)/obj/BOOT_SIGN
	@openssl dgst -sha256 -sign "$(TARGET_PRODUCT_OUT)/obj/ETC/signing/build.key" -out $(TARGET_PRODUCT_OUT)/obj/BOOT_SIGN/$(LOCAL_MODULE)_signature.bin $(INSTALLED_BOOTABLE_TARGET)
	@printf "board=$(TARGET_DEVICE)$(DATE)" > $(TARGET_PRODUCT_OUT)/obj/BOOT_SIGN/board_info.txt
	@echo -e ${BOLD}"\e[1A\e[Ktarget $(LOCAL_MODULE) image:$@" ${CL_RST}
.PHONY : $(INSTALLED_BOOTABLE_TARGET)
