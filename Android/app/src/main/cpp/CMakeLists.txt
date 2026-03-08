cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Define absolute path to the decompilation root
# This ensures the compiler finds the files regardless of the working directory
get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../decomp-files" ABSOLUTE)

# 2. Collect core engine files
# We use a non-recursive GLOB to prevent picking up conflicting regional variants
file(GLOB GAME_SOURCES 
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core2/*.c"
    "${DECOMP_ROOT}/src/done/*.c"
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
# We must include the specific 'PR' folder for N64 hardware headers
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

# 4. Compiler Flags for Retro Decompilation
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# -fcommon: Merges multiple tentative definitions of global variables
# -w: Suppresses heavy warning output from the decompiled C code
target_compile_options(bkawrapper PRIVATE -w -fcommon)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
