cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# Detect repository root dynamically
get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)
set(DECOMP_ROOT "${REPO_ROOT}/decomp-files")

message(STATUS "DECOMP_ROOT is set to: ${DECOMP_ROOT}")

# Define types bridge
set(BRIDGE_HEADER "${DECOMP_ROOT}/include/n64_types.h")
set(COMMON_FLAGS "-w -fcommon -O2 -D_FINALROM -D_LANGUAGE_C -D_ULTRATYPES_H_ -DANDROID")

# Include Directories
include_directories(SYSTEM
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src/core1
)

# Source Discovery
file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")

# Debug: Print found sources
list(LENGTH CORE1_SOURCES SRC_COUNT)
message(STATUS "Found ${SRC_COUNT} source files in core1")

if(SRC_COUNT EQUAL 0)
    message(FATAL_ERROR "No source files found in ${DECOMP_ROOT}/src/core1! Check your paths.")
endif()

# Filter exclusions
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*memory.c")
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*n_reverb.*")

# Library Target
add_library(bkawrapper SHARED 
    ${CORE1_SOURCES} 
    NativeBridge.cpp
)

set_target_properties(bkawrapper PROPERTIES COMPILE_FLAGS "-include ${BRIDGE_HEADER}")
target_compile_options(bkawrapper PRIVATE ${COMMON_FLAGS})

target_link_libraries(bkawrapper log android z GLESv2 EGL m atomic)
