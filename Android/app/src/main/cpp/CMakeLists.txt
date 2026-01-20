# File: Android/app/src/main/cpp/CMakeLists.txt
cmake_minimum_required(VERSION 3.18.1)

project(bk_wrapper LANGUAGES C CXX)

# Specify C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Set Android-specific flags
set(CMAKE_ANDROID_STL_TYPE c++_static)
set(CMAKE_ANDROID_ARCH_ABI arm64-v8a)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

# Collect source files
file(GLOB_RECURSE WRAPPER_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/wrapper.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/ultra/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/menu/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/stubs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/texture_stubs.cpp"
)

# Create the shared library
add_library(
    bk_wrapper
    SHARED
    ${WRAPPER_SOURCES}
)

# Link libraries (if needed)
find_library(log-lib log)

target_link_libraries(
    bk_wrapper
    ${log-lib}
)