cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# CPP_ROOT is now correctly absolute: .../Android/app/src/main/cpp
set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# Automatically collect all source files
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
    "${CPP_ROOT}/game_src/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# Include Directories
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
    -fcommon            # Allows multiple definitions of global variables
    -w                  # Suppress legacy warnings
    -fno-builtin        # Don't let Clang replace game functions with built-ins
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
