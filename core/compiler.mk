CCACHE		=$(shell which ccache)
AS		= $(CCACHE) as
LD		= $(CCACHE) ld
CC		= @echo $(BOLD)"\e[1A\e[K //$(LOCAL_PATH):$(LOCAL_MODULE) $$CC $(LOCAL_SRC_FILES)"${CL_RST} && $(CCACHE) /usr/bin/clang
CPP		= @echo $(BOLD)"\e[1A\e[K //$(LOCAL_PATH):$(LOCAL_MODULE) $$CPP $(LOCAL_SRC_FILES)"${CL_RST} && $(CCACHE) /usr/bin/clang++
AR		= $(CCACHE) ar
NM		= $(CCACHE) nm
STRIP		= $(CCACHE) strip
OBJCOPY	= $(CCACHE) objcopy
OBJDUMP	= $(CCACHE) objdump
AWK		= awk
INSTALLKERNEL  = installkernel
DEPMOD		= /sbin/depmod
PERL		= perl
PYTHON		= python
CHECK		= sparse
CP		=for COPYFILES in $(2) ; do echo $(BOLD)"Target Copy:$(COPYFILES)"${CL_RST} ; done && cp
TARGET_CPPFLAGS=$(TARGET_BOARD_CPPFLAGS) -D$(TARGET_PRODUCT) -Wall -Wextra
CPPFLAGS	=$(TARGET_CPPFLAGS)
CFLAGS		=$(CPPFLAGS)
GCCFLAGS	=$(CFLAGS)


export CC GCC LD CP COPYFILES
export TARGET_BOARD_CPPFLAGS CPPFLAGS CFLAGS GCCFLAGS AS LD CC TARGET_CPPFLAGS
export CPP AR NM STRIP OBJCOPY OBJDUMP
