cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Define absolute path to the decompilation root
# Based on ls -R: cpp -> main -> src -> app -> Android -> root (5 levels)
get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

# 2. Collect engine source files
# Non-recursive GLOB avoids picking up conflicting regional variants (US/JP/PAL)
file(GLOB GAME_SOURCES 
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core2/*.c"
    "${DECOMP_ROOT}/src/done/*.c"
    
    # Explicitly include hardware/utility modules to resolve Undefined References
    "${DECOMP_ROOT}/src/core1/os/*.c"
    "${DECOMP_ROOT}/src/core1/gu/*.c"
    "${DECOMP_ROOT}/src/core1/io/*.c"
    "${DECOMP_ROOT}/src/core1/audio/*.c"
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

# 3. Comprehensive Include Paths
# Includes the specific 2.0L/PR path for N64 hardware headers
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src
)

# 4. Compiler Flags for AArch64/Android NDK
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# -fcommon: Essential for merging global variables declared across different .c files
# -w: Suppresses heavy warnings from original decompiled code
target_compile_options(bkawrapper PRIVATE -w -fcommon)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

# Link atomic for 64-bit synchronization and m for math functions
target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)