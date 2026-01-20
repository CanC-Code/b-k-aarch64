# File: Android/app/src/main/cpp/CMakeLists.txt

cmake_minimum_required(VERSION 3.18)
project(bk_wrapper)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Source files
set(WRAPPER_SOURCES
    wrapper.cpp
    menu/menu.cpp
    emulator/emulator.cpp
)

# Library
add_library(bk_wrapper SHARED ${WRAPPER_SOURCES})

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

# Link log for Android logging
find_library(log-lib log)
target_link_libraries(bk_wrapper ${log-lib})