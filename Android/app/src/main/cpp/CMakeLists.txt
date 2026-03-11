cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# --- Standard Configuration ---
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_language(ASM)

# --- Path Definitions ---
set(DECOMP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files)

# --- Global Compiler Flags & Definitions ---
# F3DEX_GBI_2 is mandatory for Banjo-Kazooie's microcode.
# _LANGUAGE_C is required for the SDK headers to expose the correct structs.
add_definitions(-DF3DEX_GBI_2 -D_LANGUAGE_C)

# Common flags for Android NDK compatibility.
# -fcommon allows the "multiple definition" style of the original BK source.
set(COMMON_C_FLAGS "-w -fcommon -include stdint.h")

# THE FIX FOR model.h (Vtx, s16, u8 errors):
# We force-include the types and the graphics interface at the start of every file.
# We also define guards for the headers that cause redefinition loops (gbi/abi/ultra64).
set(HEADER_GUARDS "-D_GBI_H_ -D_ABI_H_ -D_ULTRA64_H_")

# We must include ultratypes.h FIRST so that s16/u8 exist before model.h is parsed.
set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/ultratypes.h -include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h -include ${DECOMP_ROOT}/include/2.0L/PR/abi.h")

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${COMMON_C_FLAGS} ${HEADER_GUARDS} ${FORCED_INCLUDES}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w -fcommon")

# --- Include Directories ---
# Order is critical for BK: 2.0L/PR must come before the root include folder.
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

# --- Source File Collection ---

# Banjo-Kazooie Core C Files
file(GLOB CORE1_SOURCES 
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core1/gu/*.c"
    "${DECOMP_ROOT}/src/core1/io/*.c"
    "${DECOMP_ROOT}/src/core1/os/*.c"
    "${DECOMP_ROOT}/src/core1/audio/*.c"
)

# ASM / Ultra Files
file(GLOB_RECURSE ASM_SOURCES
    "${DECOMP_ROOT}/asm/ultra/*.s"
    "${DECOMP_ROOT}/asm/core1/ultra/*.s"
)
set_source_files_properties(${ASM_SOURCES} PROPERTIES LANGUAGE ASM)

# Android Wrapper / HLE / Bridge Files
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
# Combine everything into the .so for the APK
add_library(bkawrapper SHARED 
    ${CORE1_SOURCES} 
    ${ASM_SOURCES} 
    ${WRAPPER_SOURCES}
)

# --- Linker Configuration ---
find_library(log-lib log)
target_link_libraries(bkawrapper 
    ${log-lib} 
    GLESv2 
    android 
    EGL
)

set_target_properties(bkawrapper PROPERTIES
    C_VISIBILITY_PRESET "hidden"
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
)

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(bkawrapper PRIVATE -O0 -g)
endif()
