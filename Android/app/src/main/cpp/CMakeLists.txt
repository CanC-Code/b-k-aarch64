cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

# ------------------------------
# Set C++ standard
# ------------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ------------------------------
# Source files
# ------------------------------
set(SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR})

set(WRAPPER_SOURCES
    ${SRC_DIR}/NativeBridge.cpp
    ${SRC_DIR}/GLRenderer.cpp
    ${SRC_DIR}/otr_generator.cpp
)

# Include emulator/ and ultra/ sources if needed
file(GLOB_RECURSE EXTRA_SOURCES
    ${SRC_DIR}/emulator/*.cpp
    ${SRC_DIR}/ultra/*.cpp
)
list(APPEND WRAPPER_SOURCES ${EXTRA_SOURCES})

# ------------------------------
# Include directories
# ------------------------------
include_directories(
    ${SRC_DIR}
    ${SRC_DIR}/ultra
    ${SRC_DIR}/emulator
    ${SRC_DIR}/otr_generator
    ${ANDROID_NDK}/sources/android/native_app_glue
    ${ANDROID_NDK}/sysroot/usr/include
)

# Android macro
add_definitions(-DANDROID)

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