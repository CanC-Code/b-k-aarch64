cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Path Discovery
get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)
set(DECOMP_ROOT "${REPO_ROOT}/decomp-files")

# 2. Bridge & Flags
set(BRIDGE_HEADER "${DECOMP_ROOT}/include/n64_types.h")
# Define flags as a list to avoid Clang argument errors
set(COMMON_FLAGS 
    -w 
    -fcommon 
    -O2 
    -D_FINALROM 
    -D_LANGUAGE_C 
    -D_ULTRATYPES_H_ 
    -DANDROID
)

# 3. Include Search Paths
include_directories(SYSTEM
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src/core1
)

# 4. Source Collection
file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")

# Exclude original memory manager if you are using a modern malloc wrapper
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*memory.c")
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*n_reverb.*")

# 5. Build Library
add_library(bkawrapper SHARED 
    ${CORE1_SOURCES} 
    ultra/NativeBridge.cpp 
)

# 6. Apply Precision Compile Options
target_compile_options(bkawrapper PRIVATE ${COMMON_FLAGS} -include "${BRIDGE_HEADER}")

# 7. Linkage
target_link_libraries(bkawrapper 
    log 
    android 
    z 
    GLESv2 
    EGL 
    m 
    atomic
)
