cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
# Define the path back to the decomp-files directory
set(DECOMP_ROOT ${CPP_ROOT}/../../../../decomp-files)

# Automatically collect all source files including the HLE bridge and core engine
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/*.cpp"
    "${CPP_ROOT}/*.c"
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core2/*.c"
    "${DECOMP_ROOT}/src/core1/os/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# Include Directories: These must match the renames performed by prepare_source.py
target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
)

# Link necessary Android libraries
target_link_libraries(bkawrapper 
    android
    log
    z # Required for rare_decompression.cpp if using zlib
)
