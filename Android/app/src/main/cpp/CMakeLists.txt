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

# ------------------------------
# Ensure Android macro for conditional compilation
# ------------------------------
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