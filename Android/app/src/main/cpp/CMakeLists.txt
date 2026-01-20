cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

file(GLOB_RECURSE WRAPPER_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/ultra/*.cpp"
)

add_library(bkawrapper SHARED ${WRAPPER_SOURCES})

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

find_library(log-lib log)
find_library(android-lib android)
find_library(glesv2-lib GLESv2)

target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${glesv2-lib}
)