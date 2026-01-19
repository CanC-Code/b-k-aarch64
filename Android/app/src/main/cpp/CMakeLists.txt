cmake_minimum_required(VERSION 3.18.1)

project(BKA_N64 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ---------------------------------------------------
# NDK / Android specific
# ---------------------------------------------------
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -O2")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -O2 -std=c++17 -fexceptions -frtti")

# ---------------------------------------------------
# Include directories
# ---------------------------------------------------
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

# ---------------------------------------------------
# Source files
# ---------------------------------------------------
file(GLOB_RECURSE CPP_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/ultra/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/*.cpp"
)

file(GLOB_RECURSE CPP_HEADERS
    "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/ultra/*.hpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/*.hpp"
)

# ---------------------------------------------------
# Shared library
# ---------------------------------------------------
add_library(
    bka_native
    SHARED
    ${CPP_SOURCES}
    ${CPP_HEADERS}
)

# ---------------------------------------------------
# Link libraries
# ---------------------------------------------------
find_library(log-lib log)
find_library(android-lib android)
find_library(EGL-lib EGL)
find_library(GLESv2-lib GLESv2)

target_link_libraries(
    bka_native
    ${log-lib}
    ${android-lib}
    ${EGL-lib}
    ${GLESv2-lib}
)