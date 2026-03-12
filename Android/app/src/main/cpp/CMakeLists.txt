cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)
set(CPP_ROOT  "${CMAKE_CURRENT_SOURCE_DIR}")

# ─── Master Force-Include ───────────────────────────────────────────────────
# We force n64_types.h into every file to prevent "unknown type" errors
set(COMMON_FLAGS "-w -fcommon -O2 -D_FINALROM -include ${DECOMP_ROOT}/include/n64_types.h")
set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   ${COMMON_FLAGS} -D_ULTRATYPES_H_")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${COMMON_FLAGS}")

# ─── Include Priorities ────────────────────────────────────────────────────
include_directories(
    ${CPP_ROOT}
    ${CPP_ROOT}/ultra
    ${CPP_ROOT}/tools
)

# Use SYSTEM to ensure NDK headers take precedence over project headers
include_directories(SYSTEM
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/src/core1
)

# --- Source Management ---
file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")
# ... (rest of your wrapper sources) ...

add_library(bkawrapper SHARED ${CORE1_SOURCES} ${WRAPPER_SOURCES})
target_link_libraries(bkawrapper log android z GLESv2 EGL m atomic)
