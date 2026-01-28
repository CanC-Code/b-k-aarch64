cmake_minimum_required(VERSION 3.18)
project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 99)

# 1. Global Definitions & Injections
# This fixes the 'Vtx', 'Gfx', and 'bool' errors without editing files
add_definitions(-DVERSION_US=1 -D_LANGUAGE_C -DN_AUDIO -D__BOOL_H__)

# 2. Source Collection
# Dynamically find all the N64 game C files moved by your Python script
file(GLOB_RECURSE GAME_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/game_src/*.c")

set(WRAPPER_SOURCES
    ultra/NativeBridge.cpp
    ultra/otr_builder.cpp
    ultra/audio_helper.cpp
    ultra/exceptasm.cpp
    ultra/libm_vals.cpp
    emulator/stubs.cpp
    tools/rare_decompression.cpp
)

# 3. Build the shared library (Linking BOTH wrapper and game source)
add_library(bkawrapper SHARED ${WRAPPER_SOURCES} ${GAME_SOURCES})

# 4. Header Management
# Use SYSTEM for N64 headers to prevent them from breaking standard C libraries
target_include_directories(bkawrapper SYSTEM PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR
)

target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/game_src
)

# 5. Compiler Flags for Legacy N64 Code
target_compile_options(bkawrapper PRIVATE
    -fno-builtin
    -w                # Suppress legacy warnings
    -fsigned-char
    -include "PR/ultratypes.h"
    -include "PR/gbi.h"
)

# 6. Linking
find_library(log-lib log)
find_library(android-lib android)
find_library(jnigraphics-lib jnigraphics)
find_library(z-lib z)

target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${jnigraphics-lib}
    ${z-lib}
    atomic
    m
)
