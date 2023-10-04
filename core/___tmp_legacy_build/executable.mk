OBJ=$(TARGET_PRODUCT_OUT)/obj/EXECUTABLES/$(LOCAL_MODULE)_indeterminates
RECOVERY_OBJ=$(TARGET_PRODUCT_OUT)/obj/EXECUTABLES/$(LOCAL_MODULE)_recovery_indeterminates
LOCAL_C_INCLUDES += .
INCLUDES=$(shell for inc in $(LOCAL_C_INCLUDES); do echo "-I$$inc"; done) $(shell echo $(cat out/.module_paths/EXPORT_INCLUDES ))
ifeq ($(BUILD_WITH_CCACHE),true)
CCACHE=$(shell which ccache)
endif

CPP_FLAGS=-fdiagnostics-color=always -pipe -D_FILE_OFFSET_BITS=64

ifeq ($(TARGET_BUILD_VARIANT),eng)
CPP_FLAGS+= -DENG_BUILD -DDEBUG -DVERBOSE_LOG
endif
ifeq ($(TARGET_BUILD_VARIANT),eng_v2)
CPP_FLAGS+= -DDEBUG_BUILD -DDEBUG -DVERBOSE_LOG
endif


export CFLAGS LOCAL_C_INCLUDES LOCAL_CFLAGS LINK COMPILER_NAME
INSTALL_RECOVERY_EXEC_PATH=$(TARGET_RECOVERY_OUT)/sbin
RECOVERY_CFLAGS= -DRECOVERY_LINKER -DRECOVERY_MODULE -DRECOVERY_LIBRARY -DRECOVERY_INIT -DRECOVERY_EXECUTABLE
CFLAGS += $(LOCAL_CFLAGS) $(LOCAL_C_FLAGS)

STRIP_FLAGS += \
-S \
--strip-unneeded \
--remove-section=.note.gnu.gold-version  \
--remove-section=.comment  \
--remove-section=.note \
--remove-section=.note.gnu.build.id \
--remove-section=.not.ABI-tag

ifeq ($(LOCAL_CLANG),true)
COMPILER=$(CCACHE) /usr/bin/clang
else
COMPILER=$(CCACHE) gcc
endif


ifeq ($(LOCAL_CPP_CLANG),true)
CC=$(CCACHE) $(COMPILER)++
COMPILER_NAME=clang++
else
CC=$(CCACHE) $(COMPILER)
COMPILER_NAME=clang
endif


RECOVERY_EXECUTABLE_PATH=$(TARGET_RECOVERY_OUT)/sbin

ifeq ($(PROPRIETARY_MODULE),true)
ifeq ($(OVERRIDE_INSTALL_PATH),true)
INSTALL_EXEC_PATH=$(INSTALL_PATH)
else
INSTALL_EXEC_PATH= $(TARGET_VENDOR_OUT)/bin
endif
else
ifeq ($(OVERRIDE_INSTALL_PATH),true)
INSTALL_EXEC_PATH=$(INSTALL_PATH)
else
INSTALL_EXEC_PATH= $(TARGET_SYSTEM_OUT)/bin
endif
endif

LOCAL_OBJS=$(shell for i in $(LOCAL_SRC_FILES) ; do echo $(OBJ)/$$i.o ;done)
RECOVERY_LOCAL_OBJS=$(shell for i in $(LOCAL_SRC_FILES) ; do echo $(RECOVERY_OBJ)/$$i.o ;done)
# clean up c files
OBJ_C_FOLDERS=$(shell for i in $(LOCAL_SRC_FILES) ; do echo $(OBJ)/$$i ;done)
RECOVERY_OBJ_C_FOLDERS=$(shell for i in $(LOCAL_SRC_FILES) ; do echo $(OBJ)/$$i ;done)

INSTALLED_EXECUTABLE_TARGET=$(INSTALL_EXEC_PATH)/$(LOCAL_MODULE)
$(INSTALLED_EXECUTABLE_TARGET):
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
	@$(CC) -o $(INSTALLED_EXECUTABLE_TARGET)  $(LOCAL_OBJS) -Wl,--as-needed $(LD_FLAGS) -Wl,--no-undefined
	@echo -e $(BOLD)"\e[1A\e[KInstall:$@"${CL_RST}
	@strip $(STRIP_FLAGS) $(OBJ)/LINKED/$(LOCAL_MODULE)
	@strip $(STRIP_FLAGS) $(INSTALLED_EXECUTABLE_TARGET)
ifeq ($(INCLUDE_RECOVERY_EXECUTABLE),true)
	@make $(INSTALLED_RECOVERY_EXECUTABLE_TARGET)
endif
	@echo $(LOCAL_MODULE) >> $(TARGET_SYSTEM_OUT)/etc/package.conf
.PHONY:$(INSTALLED_EXECUTABLE_TARGET)


# recovery packages are not updatable
ifeq ($(INCLUDE_RECOVERY_EXECUTABLE),true)
INSTALLED_RECOVERY_EXECUTABLE_TARGET=$(TARGET_RECOVERY_OUT)/sbin/$(LOCAL_MODULE)
$(INSTALLED_RECOVERY_EXECUTABLE_TARGET):
	@mkdir -p $(RECOVERY_OBJ)
	@mkdir -p $(RECOVERY_OBJ)/LINKED
	@for src_mkdir in $(LOCAL_SRC_FILES); do \
	mkdir -p $(RECOVERY_OBJ)/$$src_mkdir ; \
	done
	@rm -rf $(RECOVERY_OBJ_C_FOLDERS)
	@for src in $(LOCAL_SRC_FILES); do \
	$(CC) $(CPP_FLAGS) $(INCLUDES) $(RECOVERY_CFLAGS) $(CFLAGS) -g -MD -MQ '$(RECOVERY_OBJ)/'$$src.o  -MF '$(RECOVERY_OBJ)/'$$src.o.d -o '$(RECOVERY_OBJ)/'$$src.o -c $(BUILD_TOP)/$(LOCAL_PATH)/$$src && echo -e $(BOLD)"\e[1A\e[K//$(LOCAL_PATH):$(LOCAL_MODULE) $$COMPILER_NAME $$src [recovery]"${CL_RST} ; \
	done
	@$(CC) -o $(RECOVERY_OBJ)/LINKED/$(LOCAL_MODULE) $(RECOVERY_LOCAL_OBJS)  -Wl,--as-needed $(LD_FLAGS) -Wl,--no-undefined
	@$(CC) -o $(INSTALLED_RECOVERY_EXECUTABLE_TARGET) $(RECOVERY_LOCAL_OBJS)  -Wl,--as-needed $(LD_FLAGS) -Wl,--no-undefined
	@echo -e $(BOLD)"\e[1A\e[KInstall:$@"${CL_RST}
	@strip $(STRIP_FLAGS) $(RECOVERY_OBJ)/LINKED/$(LOCAL_MODULE)
	@strip $(STRIP_FLAGS) $(INSTALLED_RECOVERY_EXECUTABLE_TARGET)
.PHONY:$(INSTALLED_RECOVERY_EXECUTABLE_TARGET)
endif
