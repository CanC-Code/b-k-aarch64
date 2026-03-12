cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_language(ASM)

get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

# --- Compiler Flags ---
# 1. F3DEX_GBI_2 & _LANGUAGE_C: Standard N64 decomp requirements.
# 2. _ULTRATYPES_H_: Bypasses N64's s8/u8/s32 to use Android's stdint.h types.
# 3. _GBI_H_: This is the "Magic Bullet." By defining this, we tell the compiler 
#    gbi.h is already loaded, preventing abi.h from trying to load it a second time.
add_definitions(-DF3DEX_GBI_2 -D_LANGUAGE_C -D_ULTRATYPES_H_ -D_GBI_H_)

# Common flags
set(COMMON_C_FLAGS "-w -fcommon -include stdint.h")

# FORCED INCLUDES: We only force gbi.h. 
# It contains Gfx, Vtx, and Mtx which are the types causing the most trouble.
set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h")

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${COMMON_C_FLAGS} ${FORCED_INCLUDES}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w -fcommon")

# --- Include Directories ---
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
    ${DECOMP_ROOT}/include/gc
)

# --- Source Files ---
file(GLOB CORE1_SOURCES 
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core1/gu/*.c"
    "${DECOMP_ROOT}/src/core1/io/*.c"
    "${DECOMP_ROOT}/src/core1/os/*.c"
    "${DECOMP_ROOT}/src/core1/audio/*.c"
)

file(GLOB_RECURSE ASM_SOURCES
    "${DECOMP_ROOT}/asm/ultra/*.s"
    "${DECOMP_ROOT}/asm/core1/ultra/*.s"
)
set_source_files_properties(${ASM_SOURCES} PROPERTIES LANGUAGE ASM)

set(WRAPPER_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/pi_hle.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/resource_mgr.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/stubs.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/menu/menu.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/NativeBridge.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/audio_helper.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/exceptasm.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/libm_vals.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_builder.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/parameters.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/setintmask.cpp
)

# --- Build Target ---
add_library(bkawrapper SHARED ${CORE1_SOURCES} ${ASM_SOURCES} ${WRAPPER_SOURCES})

find_library(log-lib log)
target_link_libraries(bkawrapper ${log-lib} GLESv2 android EGL)

set_target_properties(bkawrapper PROPERTIES
    C_VISIBILITY_PRESET "hidden"
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
)
