cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# 1. Collect all source files
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
    "${CPP_ROOT}/game_src/*.c"
    "${CPP_ROOT}/tools/*.cpp"
    "${CPP_ROOT}/tools/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# 2. Set include paths
target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${CPP_ROOT}/include
    ${CPP_ROOT}/include/ultra64
    ${CPP_ROOT}/include/2.0L
    ${CPP_ROOT}/include/2.0L/PR
    ${CPP_ROOT}/tools
    ${CPP_ROOT}/emulator
    ${CPP_ROOT}/ultra
    ${CPP_ROOT}/game_src
)

# 3. FIX: Properly format the forced includes
# Each file needs its own "-include" flag
target_compile_options(bkawrapper PRIVATE 
    "-include" "stddef.h"
    "-include" "${CPP_ROOT}/include/2.0L/PR/ultratypes.h"
)

# 4. Link libraries
target_link_libraries(bkawrapper android log z)
