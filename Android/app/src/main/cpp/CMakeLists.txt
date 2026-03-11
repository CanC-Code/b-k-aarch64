cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_language(ASM)

set(DECOMP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files)

# --- Compiler Definitions ---
add_definitions(-DF3DEX_GBI_2 -D_LANGUAGE_C)

# --- Compilation Flags ---
set(COMMON_C_FLAGS "-w -fcommon -include stdint.h")

# FIX FOR CURRENTLOG.TXT:
# We must ensure ultratypes is processed FIRST to define u8, s16, etc.
# Then gbi and abi to define Vtx and Acmd.
# We define the guards ONLY for the headers that conflict with modern Clang.
set(HEADER_GUARDS "-D_GBI_H_ -D_ABI_H_ -D_ULTRA64_H_")

set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/ultratypes.h -include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h -include ${DECOMP_ROOT}/include/2.0L/PR/abi.h")

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${COMMON_C_FLAGS} ${HEADER_GUARDS} ${FORCED_INCLUDES}")
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

# --- Source Collection ---
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

# --- Linking ---
find_library(log-lib log)
target_link_libraries(bkawrapper ${log-lib} GLESv2 android EGL)

set_target_properties(bkawrapper PROPERTIES
    C_VISIBILITY_PRESET "hidden"
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
)

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(bkawrapper PRIVATE -O0 -g)
endif()
