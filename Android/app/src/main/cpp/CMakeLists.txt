cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX ASM)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(DECOMP_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

set(CPP_ROOT  "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")

# ─── Compile flags ────────────────────────────────────────────────────────────
# -fcommon: Essential for original BK source global variables.
# -D_ULTRATYPES_H_: We use this to tell the N64 headers to skip their own 
#    typedefs for s32, u16, etc., and instead use Android's stdint.h.
# -include stdint.h: Forces the system types to be available everywhere.
# ─────────────────────────────────────────────────────────────────────────────
set(COMMON_C_FLAGS "-w -fcommon -O2 -D_ULTRATYPES_H_ -include stdint.h")

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
    ${DECOMP_ROOT}/src/core1
    ${DECOMP_ROOT}/src/core1/audio
)

# ─── THE AUDIO.H FIX ─────────────────────────────────────────────────────────
# If the harmonizer isn't catching all instances of "audio.h" vs <audio.h>,
# we force the compiler to see the Graphics and Audio base types globally.
set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h -include ${DECOMP_ROOT}/include/2.0L/PR/abi.h")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${FORCED_INCLUDES}")

# ─── Source files ─────────────────────────────────────────────────────────────
file(GLOB_RECURSE CORE1_SOURCES
    "${DECOMP_ROOT}/src/core1/*.c"
)

file(GLOB ASM_SOURCES
    "${DECOMP_ROOT}/asm/ultra/*.s"
    "${DECOMP_ROOT}/asm/core1/ultra/*.s"
)
set_source_files_properties(${ASM_SOURCES} PROPERTIES LANGUAGE ASM)

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

set_target_properties(bkawrapper PROPERTIES
    C_VISIBILITY_PRESET   "hidden"
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
)
