OBJ=$(TARGET_PRODUCT_OUT)/obj/APEX/apex_indeterminates/$(LOCAL_APEX_MODULE)_indeterminates
OBJ2=$(TARGET_PRODUCT_OUT)/apex/$(LOCAL_APEX_MODULE)
SRC_FILES= $(LOCAL_SRC_FILES)
INCLUDES=-I$(LOCAL_C_INCLUDES)
export CFLAGS LOCAL_C_INCLUDES LOCAL_CFLAGS
ifeq ($(LOCAL_CPP_CLANG),true)
CC=echo $(BOLD)"target clang++: $(LOCAL_MODULE) <= $(LOCAL_SRC_FILES)"${CL_RST} && clang++
else
CC=echo $(BOLD)"target clang: $(LOCAL_MODULE) <= $(LOCAL_SRC_FILES)"${CL_RST} && clang
endif
export CC OBJ OBJ2

ifeq ($(PROPRIETARY_MODULE),true)
INSTALL_EXEC_PATH= $(TARGET_VENDOR_OUT)/apex/$(LOCAL_APEX_MODULE)/bin
else
INSTALL_EXEC_PATH= $(TARGET_SYSTEM_OUT)/apex/$(LOCAL_APEX_MODULE)/bin
endif

INSTALLED_APEX_TARGET=$(TARGET_SYSTEM_OUT)/apex/$(LOCAL_APEX_MODULE)
$(INSTALLED_APEX_TARGET):
	@mkdir -p $(OBJ)
	@mkdir -p $(OBJ2) $(OBJ2)/bin/
	@mkdir -p $(OBJ2)/lib $(OBJ2)/lib64 
	@for var in $(SHARED_LIBRARIES); do ln -sf  ../../../$(LIBRARY_LOCATION)/$$var.so $(OBJ2)/lib/$$var.so; done
	@for var in $(SHARED_LIBRARIES); do ln -sf  ../../../$(LIBRARY_LOCATION)64/$$var.so $(OBJ2)/lib64/$$var.so; done
	@$(CC) -g -o $(OBJ)/$(LOCAL_MODULE).o $(LOCAL_SRC_FILES)
	@cp $(OBJ)/$(LOCAL_MODULE).o $(OBJ2)/bin/$(LOCAL_MODULE)
	@echo "{ \"name\"": \"$(LOCAL_APEX_MODULE)\"", \"version\"": \"$(VERSION)\"} >$(OBJ2)/apex_manifest.json
	@cd $(OBJ2) && cd .. && zip --symlinks -q -r $(TARGET_SYSTEM_OUT)/apex/$(LOCAL_APEX_MODULE) $(LOCAL_APEX_MODULE)
	@cd $(BUILD_TOP)
ifeq ($(LOCAL_DEX),true)
	@echo $(BOLD)"Target Dex:$(INSTALL_EXEC_PATH)/$(LOCAL_MODULE)"  
	@for var in $(SHARED_LIBRARIES); do echo $(BOLD)"\e[1A\e[KTarget Dex:$(OBJ2)/lib/$$var.so" && sleep 0.01; done
	@for var in $(SHARED_LIBRARIES); do echo $(BOLD)"\e[1A\e[KTarget Dex:$(OBJ2)/lib64/$$var.so" && sleep 0.01; done
endif
ifeq ($(LOCAL_JAVA),true)
	@echo $(BOLD)"Target Dex:$(INSTALL_EXEC_PATH)/$(LOCAL_MODULE)"  
	@for var in $(SHARED_LIBRARIES); do echo $(BOLD)"\e[1A\e[KTarget Javac:$(OBJ2)/lib/$$var.so" && sleep 0.01; done
	@for var in $(SHARED_LIBRARIES); do echo $(BOLD)"\e[1A\e[KTarget Javac:$(OBJ2)/lib64/$$var" && sleep 0.01; done
endif
	@echo $(BOLD)"Packing:$@"${CL_RST}
	@echo $(BOLD)"Install:$@"${CL_RST}
.PHONY:$(INSTALLED_APEX_TARGET)

