cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# Gather all Game Source Files
file(GLOB_RECURSE GAME_SOURCES 
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
)

add_library(bkawrapper SHARED
    ${GAME_SOURCES}
    ultra/NativeBridge.cpp
    ultra/otr_builder.cpp
    ultra/audio_helper.cpp
    ultra/exceptasm.cpp
    emulator/resource_mgr.cpp
    emulator/pi_hle.cpp
    emulator/stubs.cpp
    tools/rare_decompression.cpp
)

# Apply lenient flags for legacy code
target_compile_options(bkawrapper PRIVATE -w -fcommon)

# --- Optimized Include Paths ---
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    # This path allows #include "PR/ultratypes.h" to resolve correctly
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# --- Robust PCH Generation ---
set(GLOBAL_PCH "${CMAKE_CURRENT_BINARY_DIR}/global_pch.h")
file(WRITE ${GLOBAL_PCH} "
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

/* Attempt to include via the standard PR path */
#if __has_include(\"PR/ultratypes.h\")
    #include \"PR/ultratypes.h\"
#elif __has_include(\"ultratypes.h\")
    #include \"ultratypes.h\"
#endif
")

target_compile_options(bkawrapper PRIVATE "-include" "${GLOBAL_PCH}")

# Linker setup
find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
