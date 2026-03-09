cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Define absolute path to the decompilation root
get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

# 2. Collect engine source files
file(GLOB GAME_SOURCES
    # Core1
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core1/audio/*.c"
    "${DECOMP_ROOT}/src/core1/gu/*.c"
    "${DECOMP_ROOT}/src/core1/io/*.c"
    "${DECOMP_ROOT}/src/core1/os/*.c"

    # Core2
    "${DECOMP_ROOT}/src/core2/*.c"
    "${DECOMP_ROOT}/src/core2/anim/*.c"
    "${DECOMP_ROOT}/src/core2/ba/*.c"
    "${DECOMP_ROOT}/src/core2/bs/*.c"
    "${DECOMP_ROOT}/src/core2/ch/*.c"
    "${DECOMP_ROOT}/src/core2/fx/*.c"
    "${DECOMP_ROOT}/src/core2/gc/*.c"
    "${DECOMP_ROOT}/src/core2/nc/*.c"
    "${DECOMP_ROOT}/src/core2/nc/ba/*.c"

    # Levels and cutscenes
    "${DECOMP_ROOT}/src/done/*.c"
    "${DECOMP_ROOT}/src/emptyLvl/*.c"
    "${DECOMP_ROOT}/src/cutscenes/*.c"
    "${DECOMP_ROOT}/src/BGS/*.c"
    "${DECOMP_ROOT}/src/BGS/ch/*.c"
    "${DECOMP_ROOT}/src/CC/*.c"
    "${DECOMP_ROOT}/src/CC/ch/*.c"
    "${DECOMP_ROOT}/src/CCW/*.c"
    "${DECOMP_ROOT}/src/CCW/ch/*.c"
    "${DECOMP_ROOT}/src/FP/*.c"
    "${DECOMP_ROOT}/src/FP/ch/*.c"
    "${DECOMP_ROOT}/src/FP/ma/*.c"
    "${DECOMP_ROOT}/src/GV/*.c"
    "${DECOMP_ROOT}/src/GV/ch/*.c"
    "${DECOMP_ROOT}/src/MM/*.c"
    "${DECOMP_ROOT}/src/MM/ch/*.c"
    "${DECOMP_ROOT}/src/MMM/*.c"
    "${DECOMP_ROOT}/src/MMM/ch/*.c"
    "${DECOMP_ROOT}/src/RBB/*.c"
    "${DECOMP_ROOT}/src/RBB/ch/*.c"
    "${DECOMP_ROOT}/src/SM/*.c"
    "${DECOMP_ROOT}/src/SM/ch/*.c"
    "${DECOMP_ROOT}/src/TTC/*.c"
    "${DECOMP_ROOT}/src/TTC/ch/*.c"
    "${DECOMP_ROOT}/src/TTC/ma/*.c"
    "${DECOMP_ROOT}/src/lair/*.c"
    "${DECOMP_ROOT}/src/lair/ch/*.c"
    "${DECOMP_ROOT}/src/fight/*.c"
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
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
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