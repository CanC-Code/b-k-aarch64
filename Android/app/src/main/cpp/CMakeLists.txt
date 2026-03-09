cmake_minimum_required(VERSION 3.22.1)

project(bkawrapper)

# Enable C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set output directories
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Include directories for the project
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/core1
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/core2
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/gc
)

# Add all source files from decomp-files/src
file(GLOB_RECURSE DECOMP_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/*.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/asm/ultra/*.s"
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/asm/core1/ultra/*.s"
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
    ${DECOMP_SOURCES}
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
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/asm/ultra/*.s
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/asm/core1/ultra/*.s
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