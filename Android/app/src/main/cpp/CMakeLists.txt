cmake_minimum_required(VERSION 3.18)
project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# 1. Be careful with GLOB_RECURSE. 
# Ensure there are no 'old' or 'backup' .cpp files in your folders.
file(GLOB_RECURSE WRAPPER_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

add_library(bkawrapper SHARED ${WRAPPER_SOURCES})

# 2. Include paths
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/menu
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    # Your external decomp-files paths
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L/PR
)

# 3. Find NDK system libraries
find_library(log-lib log)
find_library(android-lib android)
find_library(glesv2-lib GLESv2)
find_library(z-lib z) # This is essential for rare_decompression.cpp

# 4. Link everything
target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${glesv2-lib}
    ${z-lib}    # This provides inflateInit2, inflate, etc.
    atomic      # Needed for some 64-bit operations
    m           # Math library (often needed by ultra/ components)
)
