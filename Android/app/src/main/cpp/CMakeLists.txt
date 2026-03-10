cmake_minimum_required(VERSION 3.22.1)

project(bkawrapper)

# Enable C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Path to decomp-files at repo root (5 levels up from Android/app/src/main/cpp/)
set(DECOMP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files)

# Include directories for the project
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
    ${DECOMP_ROOT}/include/gc
)

# Glob core1 sources properly
file(GLOB CORE1_ROOT_SOURCES
    "${DECOMP_ROOT}/src/core1/*.c"
)
file(GLOB CORE1_GU_SOURCES
    "${DECOMP_ROOT}/src/core1/gu/*.c"
)
file(GLOB CORE1_IO_SOURCES
    "${DECOMP_ROOT}/src/core1/io/*.c"
)
file(GLOB CORE1_OS_SOURCES
    "${DECOMP_ROOT}/src/core1/os/*.c"
)
file(GLOB CORE1_AUDIO_SOURCES
    "${DECOMP_ROOT}/src/core1/audio/*.c"
)

set(CORE1_SOURCES
    ${CORE1_ROOT_SOURCES}
    ${CORE1_GU_SOURCES}
    ${CORE1_IO_SOURCES}
    ${CORE1_OS_SOURCES}
    ${CORE1_AUDIO_SOURCES}
)

# Glob all assembly files
file(GLOB_RECURSE ASM_SOURCES
    "${DECOMP_ROOT}/asm/ultra/*.s"
    "${DECOMP_ROOT}/asm/core1/ultra/*.s"
)

# Add emulator and menu sources
set(EMULATOR_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/pi_hle.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/resource_mgr.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/stubs.cpp
)

set(MENU_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/menu/menu.cpp
)

set(ULTRA_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/NativeBridge.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/audio_helper.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/exceptasm.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/libm_vals.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_builder.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/parameters.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/setintmask.cpp
)

# Combine all sources
set(ALL_SOURCES
    ${CORE1_SOURCES}
    ${ASM_SOURCES}
    ${EMULATOR_SOURCES}
    ${MENU_SOURCES}
    ${ULTRA_SOURCES}
)

# Create the shared library
add_library(
    bkawrapper
    SHARED
    ${ALL_SOURCES}
)

# Link against log and OpenGL ES
find_library(log-lib log)
target_link_libraries(
    bkawrapper
    ${log-lib}
    GLESv2
    android
    EGL
)

# Disable warnings as errors for decomp code
target_compile_options(
    bkawrapper
    PRIVATE
    -w
    -fcommon
)

# Android-specific flags
set_target_properties(
    bkawrapper
    PROPERTIES
    C_VISIBILITY_PRESET "hidden"
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
)

# Enable ASM support for N64 assembly files
enable_language(ASM)
set_source_files_properties(
    ${ASM_SOURCES}
    PROPERTIES LANGUAGE ASM
)

# Disable optimizations for debug builds
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(
        bkawrapper
        PRIVATE
        -O0
        -g
    )
endif()