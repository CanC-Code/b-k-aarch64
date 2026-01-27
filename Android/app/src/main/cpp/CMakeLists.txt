cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Collect all CPP files exactly once using a single recursive search
file(GLOB_RECURSE WRAPPER_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

add_library(bkawrapper SHARED ${WRAPPER_SOURCES})

target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L/PR
)

find_library(log-lib log)
find_library(android-lib android)
find_library(glesv2-lib GLESv2)
find_library(z-lib z)

target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${glesv2-lib}
    ${z-lib}
    atomic
)
