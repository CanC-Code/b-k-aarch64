cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)
set(DECOMP_ROOT "${REPO_ROOT}/decomp-files")
set(BRIDGE_HEADER "${DECOMP_ROOT}/include/n64_types.h")

# Flags defined as a list for correct Clang argument expansion
set(COMMON_FLAGS -w -fcommon -O2 -D_FINALROM -D_LANGUAGE_C -D_ULTRATYPES_H_ -DANDROID)

include_directories(SYSTEM
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src/core1
)

file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")
list(FILTER CORE1_SOURCES EXCLUDE REGEX ".*memory.c")

add_library(bkawrapper SHARED ${CORE1_SOURCES} ultra/NativeBridge.cpp)

target_compile_options(bkawrapper PRIVATE ${COMMON_FLAGS} -include "${BRIDGE_HEADER}")
target_link_libraries(bkawrapper log android z GLESv2 EGL m atomic)
