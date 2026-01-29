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
# Instead of relying on header ordering, we force these definitions globally.
# We also force the compiler to include ultratypes.h at the very start of every file.
target_compile_options(bkawrapper PRIVATE
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
# We place ${CPP_ROOT}/include first so your 'game_string.h' and other 
# promoted headers are found before NDK system headers.
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
