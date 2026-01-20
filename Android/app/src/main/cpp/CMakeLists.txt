# File: Android/app/src/main/cpp/CMakeLists.txt
cmake_minimum_required(VERSION 3.18.1)

project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Source files
file(GLOB WRAPPER_SOURCES
    "wrapper.cpp"
    "menu/menu.cpp"
)

add_library(bk_wrapper SHARED ${WRAPPER_SOURCES})

# Includes
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
)

find_library(log-lib log)
target_link_libraries(bk_wrapper ${log-lib})