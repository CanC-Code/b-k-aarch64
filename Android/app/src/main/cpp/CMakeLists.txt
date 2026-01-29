cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# Automatically collect all source files
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
    "${CPP_ROOT}/game_src/*.c"
    "${CPP_ROOT}/tools/*.cpp"
    "${CPP_ROOT}/tools/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# Include Directories
# Added core1 and core2 to ensure game_sched.h and game_stdlib.h are found
target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${CPP_ROOT}/include
    ${CPP_ROOT}/include/core1
    ${CPP_ROOT}/include/core2
    ${CPP_ROOT}/include/2.0L
    ${CPP_ROOT}/include/2.0L/PR
    ${CPP_ROOT}/tools
    ${CPP_ROOT}/emulator
    ${CPP_ROOT}/ultra
    ${CPP_ROOT}/game_src
)

# Link standard Android libraries
target_link_libraries(bkawrapper
    android
    log
    z
)
