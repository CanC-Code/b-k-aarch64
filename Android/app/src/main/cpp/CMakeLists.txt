cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

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

target_compile_options(bkawrapper PRIVATE
    -w 
    -fcommon 
)

target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# --- Updated PCH Generation with Relative Path ---
set(GLOBAL_PCH "${CMAKE_CURRENT_BINARY_DIR}/global_pch.h")
file(WRITE ${GLOBAL_PCH} "
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
/* Use relative path from include directories defined above */
#include \"PR/ultratypes.h\"
")
target_compile_options(bkawrapper PRIVATE "-include" "${GLOBAL_PCH}")

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
