cmake_minimum_required(VERSION 3.18.1)

project(bk_wrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_ANDROID_STL_TYPE c++_static)
set(CMAKE_ANDROID_ARCH_ABI arm64-v8a)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

file(GLOB_RECURSE WRAPPER_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/wrapper.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/menu/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/stubs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/texture_stubs.cpp"
)

add_library(
    bk_wrapper
    SHARED
    ${WRAPPER_SOURCES}
)

find_library(log-lib log)

target_link_libraries(
    bk_wrapper
    ${log-lib}
)