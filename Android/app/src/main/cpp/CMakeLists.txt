cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# Define paths relative to the CMake file
set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/src/main/cpp)

add_library(bkawrapper SHARED
    # Add your source files here
    ${CPP_ROOT}/emulator/stubs.cpp
    ${CPP_ROOT}/ultra/NativeBridge.cpp
    # ... other files
)

target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${CPP_ROOT}/tools
    ${CPP_ROOT}/emulator
    ${CPP_ROOT}/ultra
    ${CPP_ROOT}/game_src
    ${CPP_ROOT}/include
    ${CPP_ROOT}/include/2.0L
    ${CPP_ROOT}/include/2.0L/PR # This is where game_stdlib.h likely lives
)

# Force the compiler to handle legacy 'fcommon' behavior which many N64 ports need
target_compile_options(bkawrapper PRIVATE 
    -fcommon 
    -w 
    -fno-builtin
)

target_link_libraries(bkawrapper
    android
    log
    GLESv3
)
