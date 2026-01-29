cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# 1. Gather all source files
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
    "${CPP_ROOT}/game_src/*.c"
    "${CPP_ROOT}/tools/*.cpp"
    "${CPP_ROOT}/tools/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# 2. CRITICAL FIX: Forced Global Include
# This forces the compiler to prepend ultratypes.h to EVERY file.
# This solves the 'u8' unknown type errors once and for all.
target_compile_options(bkawrapper PRIVATE
    -include "${CPP_ROOT}/include/2.0L/PR/ultratypes.h"
)

# 3. Include Directories
# Note: We place ${CPP_ROOT}/include at the top so our "game_string.h" 
# and patched headers are prioritized.
target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}/include
    ${CPP_ROOT}
    ${CPP_ROOT}/include/ultra64
    ${CPP_ROOT}/include/core1
    ${CPP_ROOT}/include/core2
    ${CPP_ROOT}/include/2.0L
    ${CPP_ROOT}/include/2.0L/PR
    ${CPP_ROOT}/tools
    ${CPP_ROOT}/emulator
    ${CPP_ROOT}/ultra
    ${CPP_ROOT}/game_src
)

# 4. Link Libraries
target_link_libraries(bkawrapper android log z)

# 5. Architecture specific flags (Optional but recommended for N64 -> AArch64)
if(ANDROID_ABI STREQUAL "arm64-v8a")
    target_compile_definitions(bkawrapper PRIVATE __64BITS__ ADDRESS_64BIT)
endif()
