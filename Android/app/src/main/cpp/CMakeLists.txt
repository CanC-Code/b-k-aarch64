cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Define the path to the root of the decompilation project
set(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../decomp-files")

# 2. Specifically collect the engine source files
# We focus on core1 and core2 where the main game logic resides
file(GLOB_RECURSE GAME_SOURCES 
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

# 3. Fix the Include Paths
# The C files need to find ultra64.h and other headers in decomp-files/include
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src
)

target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)
target_compile_options(bkawrapper PRIVATE -w -fcommon)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
