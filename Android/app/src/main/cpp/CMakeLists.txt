cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)
set(CPP_ROOT  "${CMAKE_CURRENT_SOURCE_DIR}")

# ─── Global Configuration ──────────────────────────────────────────────────
# We keep the types and hardware definitions forced
set(FORCED_INCLUDES 
    "-include ${DECOMP_ROOT}/include/n64_types.h"
    "-include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h"
    "-include ${DECOMP_ROOT}/include/2.0L/PR/abi.h"
)
string(REPLACE ";" " " FORCED_INCLUDES_STR "${FORCED_INCLUDES}")

set(COMMON_FLAGS "-w -fcommon -O2 -D_FINALROM -D_ALHEAP_H_ ${FORCED_INCLUDES_STR}")
set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   ${COMMON_FLAGS} -D_ULTRATYPES_H_ -D_LANGUAGE_C")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${COMMON_FLAGS}")

include_directories(SYSTEM
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src/core1
)

# --- Source Management ---
file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")

# EXCLUDE memory.c and MIPS audio
# Since we are using System memcpy/memmove, we don't need the legacy implementations
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*memory.c")
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*n_reverb.*")

add_library(bkawrapper SHARED ${CORE1_SOURCES} ${WRAPPER_SOURCES})
target_link_libraries(bkawrapper log android z GLESv2 EGL m atomic)
