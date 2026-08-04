cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(REPO_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../../../..)

# ============================================================
# 1. C++ Bridge Sources
# ============================================================
set(CPP_BRIDGE_SOURCES
    ultra/NativeBridge.cpp ultra/otr_builder.cpp ultra/parameters.cpp
    ultra/libm_vals.cpp ultra/exceptasm.cpp ultra/LinkerSymbols.cpp
    ultra/setintmask.cpp ultra/math_bridge.cpp ultra/audio_bridge.cpp
    ultra/lowlevel_bridge.cpp emulator/stubs.cpp emulator/pi_hle.cpp
    emulator/resource_mgr.cpp emulator/gfx_interpreter.cpp
    tools/rare_decompression.cpp ultra/HardwareRegs.cpp
)

# ============================================================
# 2. C Sources
# ============================================================
set(C_BRIDGE_SOURCES
    ultra/zlib/adler32.c ultra/zlib/compress.c ultra/zlib/crc32.c
    ultra/zlib/deflate.c ultra/zlib/infback.c ultra/zlib/inffast.c
    ultra/zlib/inflate.c ultra/zlib/inftrees.c ultra/zlib/trees.c
    ultra/zlib/uncompr.c ultra/zlib/zutil.c ultra/missing_stubs.c
)

option(EXCLUDE_GAME_SRC "Skip" OFF)
set(GAME_SOURCES "")
if(NOT EXCLUDE_GAME_SRC)
    file(GLOB_RECURSE ALL_GAME_FILES "${REPO_ROOT}/src/*.c")
    set(EXCLUDE_LIST createthread.c startthread.c stopthread.c destroythread.c
        yieldthread.c settreadpri.c getthreadpri.c createmesgqueue.c
        seteventmesg.c recvmesg.c sendmesg.c jammesg.c visetmode.c
        visetevent.c inflate.c)
overlaymanager.c
    foreach(F ${ALL_GAME_FILES})
        get_filename_component(N ${F} NAME)
        if(NOT N IN_LIST EXCLUDE_LIST)
            list(APPEND GAME_SOURCES ${F})
        endif()
    endforeach()
endif()

add_library(bkawrapper SHARED ${CPP_BRIDGE_SOURCES} ${C_BRIDGE_SOURCES} ${GAME_SOURCES})
target_link_options(bkawrapper PRIVATE "-Wl,--allow-multiple-definition" "-Wl,--export-dynamic" "-Wl,--wrap=__osInitialize_common")

# ============================================================
# Include Directories
# ============================================================
# Common (safe for both C and C++) - includes boot/core1 for rarezip.h
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${REPO_ROOT}/src
    ${REPO_ROOT}/lib/ultralib/include
)

# N64 SDK headers ONLY for C files
target_include_directories(bkawrapper PRIVATE
    $<$<COMPILE_LANGUAGE:C>:${REPO_ROOT}/include>
    $<$<COMPILE_LANGUAGE:C>:${REPO_ROOT}/include/n_audio/PR>
    $<$<COMPILE_LANGUAGE:C>:${REPO_ROOT}/lib/ultralib/include>
    $<$<COMPILE_LANGUAGE:C>:${REPO_ROOT}/lib/ultralib/include/PR>
    $<$<COMPILE_LANGUAGE:C>:${REPO_ROOT}/lib/ultralib/src/audio>
)

# ============================================================
# Compile Options
# ============================================================
set_source_files_properties(${CPP_BRIDGE_SOURCES} PROPERTIES
    COMPILE_FLAGS "-std=c++17 -w -fpermissive -O0 -g3"
)
set_source_files_properties(${C_BRIDGE_SOURCES} ${GAME_SOURCES} PROPERTIES
    COMPILE_FLAGS "-std=gnu11 -w -O0 -g3 -include ${CMAKE_CURRENT_SOURCE_DIR}/ultra/n64_types.h"
)

target_compile_definitions(bkawrapper PRIVATE F3DEX_GBI N64_RECOMP VERSION=0 __ANDROID__)

find_library(log-lib log)
find_library(android-lib android)
find_library(egl-lib EGL)
find_library(gles3-lib GLESv3)
find_library(gles2-lib GLESv2)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${egl-lib} ${gles3-lib} ${gles2-lib} atomic m)
