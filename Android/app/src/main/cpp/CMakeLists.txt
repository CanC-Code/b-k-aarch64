# File: Android/app/src/main/cpp/CMakeLists.txt

cmake_minimum_required(VERSION 3.18.1)

project(bk_wrapper LANGUAGES C CXX)

# -----------------------------
# C++ standard & flags
# -----------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Android-specific flags
set(CMAKE_ANDROID_STL_TYPE c++_static)
set(CMAKE_ANDROID_ARCH_ABI arm64-v8a)

# -----------------------------
# Include directories
# -----------------------------
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
)

# -----------------------------
# Source files
# -----------------------------
set(SOURCE_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/wrapper.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/menu/menu.cpp
)

# -----------------------------
# Build the shared library
# -----------------------------
add_library(
    bk_wrapper
    SHARED
    ${SOURCE_FILES}
)

# -----------------------------
# Link libraries
# -----------------------------
find_library(log-lib log)

target_link_libraries(
    bk_wrapper
    ${log-lib}
)