cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

# ------------------------------
# Set C++ standard
# ------------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ------------------------------
# Source files: cpp/, ultra/, emulator/
# ------------------------------
file(GLOB_RECURSE WRAPPER_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/ultra/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/*.cpp"
)

# ------------------------------
# Include directories
# ------------------------------
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/otr_generator
    ${ANDROID_NDK}/sources/android/native_app_glue
    ${ANDROID_NDK}/sysroot/usr/include
)

# Ensure Android macro for conditional compilation
add_definitions(-DANDROID)

# ------------------------------
# Embed OTR YAMLs at build time
# ------------------------------
set(OTR_PAL_YAML   ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_yaml/decompressed.pal.yaml)
set(OTR_US_YAML    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_yaml/decompressed.us.v10.yaml)
set(EMBED_CPP      ${CMAKE_CURRENT_BINARY_DIR}/otr_assets.cpp)
set(EMBED_HPP      ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_assets.hpp)

# Add the preexisting ultra/otr_assets.cpp to sources
list(APPEND WRAPPER_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_assets.cpp)

# ------------------------------
# Create shared library
# ------------------------------
add_library(wrapper SHARED ${WRAPPER_SOURCES})

# ------------------------------
# Find required Android libraries
# ------------------------------
find_library(log-lib log)
find_library(android-lib android)
find_library(glesv2-lib GLESv2)

# ------------------------------
# Link libraries
# ------------------------------
target_link_libraries(wrapper
    ${log-lib}
    ${android-lib}
    ${glesv2-lib}
)