cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX ASM)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)
set(CPP_ROOT  "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")
set(TOOLS_DIR "${CPP_ROOT}/tools")

# ─── Compile flags ────────────────────────────────────────────────────────────
# REMOVED -fno-builtin to allow the system to handle string/mem functions
set(COMMON_FLAGS "-w -fcommon -O2 -D_FINALROM")
set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   ${COMMON_FLAGS} -D_ULTRATYPES_H_ -include stdint.h")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${COMMON_FLAGS}")

add_compile_definitions($<$<COMPILE_LANGUAGE:C>:_LANGUAGE_C>)
add_definitions(-DF3DEX_GBI_2)

# ─── Include directories ─────────────────────────────────────────────────────
include_directories(
    ${CPP_ROOT}
    ${ULTRA_DIR}
    ${TOOLS_DIR}
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
    ${DECOMP_ROOT}/src/core1
)

set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h -include ${DECOMP_ROOT}/include/2.0L/PR/abi.h")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${FORCED_INCLUDES}")

# ─── Source Management ──────────────────────────────────────────────────────
file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")

set(WRAPPER_SOURCES
    ${ULTRA_DIR}/NativeBridge.cpp 
    ${ULTRA_DIR}/otr_builder.cpp
    ${ULTRA_DIR}/audio_helper.cpp 
    ${ULTRA_DIR}/exceptasm.cpp
    ${ULTRA_DIR}/setintmask.cpp 
    ${ULTRA_DIR}/libm_vals.cpp
    ${ULTRA_DIR}/parameters.cpp 
    ${TOOLS_DIR}/rare_decompression.cpp
    ${CPP_ROOT}/emulator/pi_hle.cpp
    ${CPP_ROOT}/emulator/resource_mgr.cpp 
    ${CPP_ROOT}/emulator/stubs.cpp
    ${CPP_ROOT}/menu/menu.cpp
)

add_library(bkawrapper SHARED ${CORE1_SOURCES} ${WRAPPER_SOURCES})
target_link_libraries(bkawrapper log android z GLESv2 EGL atomic m)
