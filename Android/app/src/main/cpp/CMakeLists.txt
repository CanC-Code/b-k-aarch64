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

# 2. THE FIX: Force standard types BEFORE N64 types
# This ensures size_t, NULL, and ptrdiff_t are defined for the Android NDK headers.
target_compile_options(bkawrapper PRIVATE
    -include "stddef.h"
    -include "${CPP_ROOT}/include/2.0L/PR/ultratypes.h"
)

# 3. Critical Architectural Flags
# These flags help N64 headers coexist with a 64-bit environment.
target_compile_definitions(bkawrapper PRIVATE 
    _LANGUAGE_C
    _FINALROM
    TARGET_N64
    __64BITS__
    ADDRESS_64BIT
)

# 4. Search Path Priority
# Note: ${CPP_ROOT}/include is first to prioritize your patched/promoted headers.
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
