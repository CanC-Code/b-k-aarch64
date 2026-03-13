cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# --- Path Configuration ---
get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)
set(DECOMP_ROOT "${REPO_ROOT}/decomp-files")
set(BRIDGE_HEADER "${DECOMP_ROOT}/include/n64_types.h")

# --- Compilation Flags ---
# -fno-strict-aliasing: Essential for N64 type punning (pointers to unions)
# -include: Forces our bridge header into every file on Line 1
set(COMMON_FLAGS 
    -w 
    -fcommon 
    -O2 
    -fno-strict-aliasing
    -D_FINALROM 
    -D_LANGUAGE_C 
    -D_ULTRATYPES_H_ 
    -DANDROID
    -include "${BRIDGE_HEADER}"
)

# --- Include Directories ---
# Using SYSTEM prevents the compiler from warning us about mess in the SDK headers
include_directories(SYSTEM
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src/core1
    ${DECOMP_ROOT}/src/core2
)

# --- Source Collection ---
file(GLOB_RECURSE CORE1_SOURCES 
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core2/*.c"
)

# Filter out MIPS-specific assembly or problematic files
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*memory.c")
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*osAuthenticate.c")

# --- Library Target ---
add_library(bkawrapper SHARED 
    ${CORE1_SOURCES} 
    ultra/NativeBridge.cpp
)

# Applying flags specifically to our library
target_compile_options(bkawrapper PRIVATE ${COMMON_FLAGS})

# --- Linking ---
# atomic is necessary for 64-bit integer operations on some ARM v8 devices
target_link_libraries(bkawrapper 
    log 
    android 
    z 
    GLESv2 
    EGL 
    m 
    atomic
)
