cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# CPP_ROOT points to .../Android/app/src/main/cpp
set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# Automatically collect all source files recursively
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
    "${CPP_ROOT}/game_src/*.c"
    "${CPP_ROOT}/tools/*.cpp"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# Include Directories
# We include all possible locations where game_*.h might end up
target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${CPP_ROOT}/tools
    ${CPP_ROOT}/emulator
    ${CPP_ROOT}/ultra
    ${CPP_ROOT}/game_src
    ${CPP_ROOT}/include
    ${CPP_ROOT}/include/2.0L
    ${CPP_ROOT}/include/2.0L/PR
)

# Compile Flags for N64 Porting
target_compile_options(bkawrapper PRIVATE 
    -fcommon            # Necessary for global variable definitions in C
    -w                  # Suppress legacy warnings to keep logs clean
    -fno-builtin        # Prevents Clang from "optimizing" game functions into Bionic ones
    -DN_AUDIO=1
    -DVERSION_US=1
    -D_LANGUAGE_C
)

target_link_libraries(bkawrapper
    android
    log
    GLESv3
    z
)
