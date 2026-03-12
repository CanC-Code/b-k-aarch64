cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX ASM)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(DECOMP_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

set(CPP_ROOT  "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")

# ─── Compile flags ────────────────────────────────────────────────────────────
# We keep -D_ULTRATYPES_H_ because even with harmonized code, the NDK's 
# 'asm-generic/int-ll64.h' will conflict with N64's 'ultratypes.h'.
# We -include stdint.h to give the compiler the types it expects for s32, u16, etc.
set(COMMON_C_FLAGS "-w -fcommon -O2 -D_ULTRATYPES_H_ -include stdint.h")

set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   ${COMMON_C_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w -fcommon -O2")

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

# ─── THE CRITICAL FIX FOR AUDIO.H ───────────────────────────────────────────
# Even if harmonized, the compiler needs to find the N64 SDK's audio definitions
# when they are referenced in 'structs.h' or 'audio.h'. 
# This forces the GBI and ABI (audio) headers to load correctly.
set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h -include ${DECOMP_ROOT}/include/2.0L/PR/abi.h")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${FORCED_INCLUDES}")

# ─── Source / Build ──────────────────────────────────────────────────────────
file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")

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

add_library(bkawrapper SHARED ${CORE1_SOURCES} ${ASM_SOURCES} ${WRAPPER_SOURCES})

target_link_libraries(bkawrapper log android z GLESv2 EGL atomic m)
