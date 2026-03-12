cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX ASM)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(DECOMP_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

set(CPP_ROOT  "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")

# ─── Compile flags ────────────────────────────────────────────────────────────
# -w          : suppress all warnings from legacy decomp sources
# -fcommon    : allow multiple tentative definitions (common in N64 decomps)
# -O2         : reasonable optimisation; use -O0 if debugging miscompiles
# _LANGUAGE_C : makes N64 SDK headers behave as C (not C++)
# F3DEX_GBI_2 : enable F3DEX2 GBI opcode set in gbi.h
#
# REMOVED vs prior CMake:
#   -D_ULTRATYPES_H_  ← was suppressing ultratypes.h entirely, causing
#                        "unknown type name 's32'" in os_thread.h etc.
#   -D_GBI_H_         ← was suppressing gbi.h, now handled by harmonizer H-passes
#   -include gbi.h    ← forced include no longer needed; harmonizer patches headers
# ─────────────────────────────────────────────────────────────────────────────
set(COMMON_C_FLAGS "-w -fcommon -O2")

set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   ${COMMON_C_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w -fcommon -O2")

# ─── Compile definitions ──────────────────────────────────────────────────────
add_definitions(
    -D_LANGUAGE_C
    -DF3DEX_GBI_2
)

# ─── Include directories ─────────────────────────────────────────────────────
include_directories(
    ${CPP_ROOT}
    ${ULTRA_DIR}
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
    ${DECOMP_ROOT}/include/gc
)

# ─── Source files ─────────────────────────────────────────────────────────────
# core1 game sources (same glob pattern as the original working CMake,
# minus the inflate/rarezip/gu exclusions that were in v6.3)
file(GLOB_RECURSE CORE1_SOURCES
    "${DECOMP_ROOT}/src/core1/*.c"
)

# Assembly stubs (ultra SDK replacements)
file(GLOB ASM_SOURCES
    "${DECOMP_ROOT}/asm/ultra/*.s"
    "${DECOMP_ROOT}/asm/core1/ultra/*.s"
)
set_source_files_properties(${ASM_SOURCES} PROPERTIES LANGUAGE ASM)

# C++ wrapper / bridge layer
set(WRAPPER_SOURCES
    ${ULTRA_DIR}/NativeBridge.cpp
    ${ULTRA_DIR}/otr_builder.cpp
    ${ULTRA_DIR}/audio_helper.cpp
    ${ULTRA_DIR}/exceptasm.cpp
    ${ULTRA_DIR}/setintmask.cpp
    ${ULTRA_DIR}/libm_vals.cpp
    ${ULTRA_DIR}/parameters.cpp
    ${CPP_ROOT}/emulator/pi_hle.cpp
    ${CPP_ROOT}/emulator/resource_mgr.cpp
    ${CPP_ROOT}/emulator/stubs.cpp
    ${CPP_ROOT}/menu/menu.cpp
)

# ─── Shared library target ───────────────────────────────────────────────────
add_library(bkawrapper SHARED
    ${CORE1_SOURCES}
    ${ASM_SOURCES}
    ${WRAPPER_SOURCES}
)

# ─── Linked libraries ────────────────────────────────────────────────────────
find_library(log-lib     log)
find_library(android-lib android)
find_library(z-lib       z)

target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${z-lib}
    GLESv2
    EGL
    atomic
    m
)

# ─── Symbol visibility ───────────────────────────────────────────────────────
set_target_properties(bkawrapper PROPERTIES
    C_VISIBILITY_PRESET   "hidden"
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
)
