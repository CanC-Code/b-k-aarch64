cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Dynamic Path Calculation
# We go up until we hit the root where 'decomp-files' lives
get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)
set(DECOMP_ROOT "${REPO_ROOT}/decomp-files")

# 2. Forced Include Logic
# This ensures every .c file sees our ARM64 types before anything else
set(BRIDGE_HEADER "${DECOMP_ROOT}/include/n64_types.h")
set(FORCED_FLAGS "-include ${BRIDGE_HEADER}")

# 3. Compiler Configuration
set(COMMON_FLAGS "-w -fcommon -O2 -D_FINALROM -D_LANGUAGE_C -D_ULTRATYPES_H_ -DANDROID")
set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   ${COMMON_FLAGS} ${FORCED_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${COMMON_FLAGS} ${FORCED_FLAGS}")

# 4. Include Search Paths
include_directories(SYSTEM
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src/core1
)

# 5. Source Management
file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")

# Exclude files we are replacing with system versions
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*memory.c")
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*n_reverb.*")

# 6. Build the Library
add_library(bkawrapper SHARED 
    ${CORE1_SOURCES} 
    NativeBridge.cpp # Your JNI entry point
)

target_link_libraries(bkawrapper 
    log 
    android 
    z 
    GLESv2 
    EGL 
    m 
    atomic
)
