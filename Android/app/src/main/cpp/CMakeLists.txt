cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../.." ABSOLUTE)
set(DECOMP_ROOT "${REPO_ROOT}/decomp-files")
set(BRIDGE_HEADER "${DECOMP_ROOT}/include/n64_types.h")

set(COMMON_FLAGS
    -w -fcommon -O2 -fno-strict-aliasing
    -D_FINALROM -D_LANGUAGE_C -D_ULTRATYPES_H_ -DANDROID
    -include "${BRIDGE_HEADER}"
)

# Include all emulator helpers and core directories
include_directories(SYSTEM
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src/core1
    ${DECOMP_ROOT}/src/core2
    ultra
    emulator
)

# Explicitly collect all C/CPP files from the core and emulator folders
file(GLOB_RECURSE CORE_SOURCES
    "${DECOMP_ROOT}/src/core1/*.c"
    "${DECOMP_ROOT}/src/core2/*.c"
    "ultra/*.cpp"
    "emulator/*.cpp"
)

# Exclude original memory manager (we use Android's malloc)
list(FILTER CORE_SOURCES EXCLUDE REGEX ".*memory.c")

add_library(bkawrapper SHARED ${CORE_SOURCES})
target_compile_options(bkawrapper PRIVATE ${COMMON_FLAGS})

target_link_libraries(bkawrapper
    log android z GLESv2 EGL m atomic
)
