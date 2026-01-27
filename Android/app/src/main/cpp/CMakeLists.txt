cmake_minimum_required(VERSION 3.18)
project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 1. Collect sources once via recursion
[span_19](start_span)file(GLOB_RECURSE WRAPPER_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")[span_19](end_span)

[span_20](start_span)add_library(bkawrapper SHARED ${WRAPPER_SOURCES})[span_20](end_span)

# 2. Include directory management
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    [span_21](start_span)${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include[span_21](end_span)
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L/PR
)

# 3. Locate and link system libraries
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
