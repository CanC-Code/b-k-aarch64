cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 1. [span_3](start_span)Expanded Glob: Added "tools" to pick up decompression and utility logic[span_3](end_span)
file(GLOB_RECURSE WRAPPER_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/ultra/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/menu/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/tools/*.cpp"
)

add_library(bkawrapper SHARED ${WRAPPER_SOURCES})

# 2. [span_4](start_span)Included tools directory for headers like zlib usage[span_4](end_span)
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
)

# 3. Standard Android Libraries
find_library(log-lib log)
find_library(android-lib android)
find_library(glesv2-lib GLESv2)
# 4. [span_5](start_span)[span_6](start_span)Added zlib: Required by tools/rare_decompression.cpp[span_5](end_span)[span_6](end_span)
find_library(z-lib z)

target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${glesv2-lib}
    ${z-lib}
)

# 5. Fix for core1_loadOTR:
# [span_7](start_span)Since stubs.cpp references core1_loadOTR as an extern[span_7](end_span), 
# ensure your compiler doesn't optimize it away if it's defined elsewhere.
