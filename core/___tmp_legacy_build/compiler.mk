CCACHE		=$(shell which ccache)
AS		= $(CCACHE) as
LD		= $(CCACHE) ld
CC		= $(CCACHE) /usr/bin/clang
CPP		= $(CCACHE) /usr/bin/clang++
AR		= $(CCACHE) ar
NM		= $(CCACHE) nm
STRIP	= $(CCACHE) strip
OBJCOPY	= $(CCACHE) objcopy
OBJDUMP	= $(CCACHE) objdump
AWK		= awk
INSTALLKERNEL  = installkernel
DEPMOD		= /sbin/depmod
PERL		= perl
PYTHON		= python
CHECK		= sparse
CP		    = for COPYFILES in $(2) ; do echo $(BOLD)"Target Copy:$(COPYFILES)"${CL_RST} ; done && cp
TARGET_CPPFLAGS=$(TARGET_BOARD_CPPFLAGS) -D$(TARGET_PRODUCT) -Wall -Wextra
CPPFLAGS	=$(TARGET_CPPFLAGS)
CFLAGS		=$(CPPFLAGS)
GCCFLAGS	=$(CFLAGS)


export CC GCC LD CP COPYFILES
export TARGET_BOARD_CPPFLAGS CPPFLAGS CFLAGS GCCFLAGS AS LD CC TARGET_CPPFLAGS
export CPP AR NM STRIP OBJCOPY OBJDUMP
