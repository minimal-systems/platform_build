#!/bin/bash


PATH=$BUILD_TOP/build/tools/bin:$PATH
find */* -name "*.min_build" -exec cat {} + > out/build_"${TARGET_DEVICE}".ninja

. out/build_"${TARGET_DEVICE}".ninja
