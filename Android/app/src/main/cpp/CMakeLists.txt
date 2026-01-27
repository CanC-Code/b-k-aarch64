cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Collect all CPP files exactly once. 
# Using a single recursive glob is safer than listing subdirectories individually 
# when using GLOB_RECURSE.
file(GLOB_RECURSE WRAPPER_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

add_library(bkawrapper SHARED ${WRAPPER_SOURCES})

target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
)

# Link necessary Android libraries
find_library(log-lib log)
find_library(android-lib android)
find_library(gles2-lib GLESv2)
find_library(z-lib z)

target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${gles2-lib}
    ${z-lib}
    atomic
)
