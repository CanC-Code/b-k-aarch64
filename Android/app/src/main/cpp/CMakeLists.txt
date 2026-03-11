cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# --- Standard Configuration ---
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_language(ASM)

# --- Path Definitions ---
set(DECOMP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files)

# --- Global Compiler Flags & Definitions ---
# F3DEX_GBI_2: Enables G_TRI2 and F3DEX2 GBI opcodes.
# _LANGUAGE_C: Required for internal Ultra64 header logic.
add_definitions(-DF3DEX_GBI_2 -D_LANGUAGE_C)

# Common flags for NDK compatibility.
# -fcommon: Necessary for legacy projects that define the same globals in multiple files.
# -include stdint.h: Provides standard types to headers that lack them.
set(COMMON_C_FLAGS "-w -fcommon -include stdint.h")

# FIX FOR LOG 95: 
# We REMOVED manual TYPE_ALIASES (-Du32, etc.) because they clashed with ultratypes.h.
# Instead, we define the guards for the project's own type headers to prevent collisions.
set(HEADER_GUARDS "-D__GBI_H__ -D_GBI_H_ -D__ABI_H__ -D_ABI_H_ -D_ULTRA64_H_ -D_ULTRATYPES_H_")

# THE FIX: Forced Includes
# Forces the compiler to process these before reading any source file.
set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h -include ${DECOMP_ROOT}/include/2.0L/PR/abi.h")

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${COMMON_C_FLAGS} ${HEADER_GUARDS} ${FORCED_INCLUDES}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w -fcommon")

# --- Include Directories ---
# Search order is critical: PR headers must come before generic SDK headers.
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
    ${DECOMP_ROOT}/include/gc
)

# --- Source File Collection ---

file(GLOB CORE1_ROOT_SOURCES   "${DECOMP_ROOT}/src/core1/*.c")
file(GLOB CORE1_GU_SOURCES     "${DECOMP_ROOT}/src/core1/gu/*.c")
file(GLOB CORE1_IO_SOURCES     "${DECOMP_ROOT}/src/core1/io/*.c")
file(GLOB CORE1_OS_SOURCES     "${DECOMP_ROOT}/src/core1/os/*.c")
file(GLOB CORE1_AUDIO_SOURCES  "${DECOMP_ROOT}/src/core1/audio/*.c")

set(CORE1_SOURCES
    ${CORE1_ROOT_SOURCES}
    ${CORE1_GU_SOURCES}
    ${CORE1_IO_SOURCES}
    ${CORE1_OS_SOURCES}
    ${CORE1_AUDIO_SOURCES}
)

file(GLOB_RECURSE ASM_SOURCES
    "${DECOMP_ROOT}/asm/ultra/*.s"
    "${DECOMP_ROOT}/asm/core1/ultra/*.s"
)
set_source_files_properties(${ASM_SOURCES} PROPERTIES LANGUAGE ASM)

set(EMULATOR_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/pi_hle.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/resource_mgr.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/stubs.cpp
)

set(MENU_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/menu/menu.cpp
)

set(ULTRA_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/NativeBridge.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/audio_helper.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/exceptasm.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/libm_vals.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_builder.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/parameters.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/setintmask.cpp
)

set(ALL_SOURCES
    ${CORE1_SOURCES}
    ${ASM_SOURCES}
    ${EMULATOR_SOURCES}
    ${MENU_SOURCES}
    ${ULTRA_SOURCES}
)

# --- Build Target ---
# This generates the libbkawrapper.so file used by the Android APK.
add_library(bkawrapper SHARED ${ALL_SOURCES})

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
