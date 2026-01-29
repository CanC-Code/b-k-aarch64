cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# 1. Source Collection
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
    "${CPP_ROOT}/game_src/*.c"
    "${CPP_ROOT}/tools/*.cpp"
    "${CPP_ROOT}/tools/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# 2. THE FIX: Forced Global Type Definitions
# We now include stddef.h first to ensure size_t and NULL are defined 
# before any N64 headers are parsed.
target_compile_options(bkawrapper PRIVATE
    -include "stddef.h"
    -include "${CPP_ROOT}/include/2.0L/PR/ultratypes.h"
)

# 3. Critical Architectural Flags
# These flags tell the N64 headers they are running on a 64-bit Android system.
target_compile_definitions(bkawrapper PRIVATE 
    _LANGUAGE_C
    _FINALROM
    TARGET_N64
    __64BITS__
    ADDRESS_64BIT
)

# 4. Search Path Priority
target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}/include
    ${CPP_ROOT}/include/2.0L
    ${CPP_ROOT}/include/2.0L/PR
    ${CPP_ROOT}
    ${CPP_ROOT}/include/ultra64
    ${CPP_ROOT}/tools
    ${CPP_ROOT}/emulator
    ${CPP_ROOT}/ultra
    ${CPP_ROOT}/game_src
)

# 5. Link Dependencies
target_link_libraries(bkawrapper android log z)
