cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# CMAKE_CURRENT_SOURCE_DIR is already .../Android/app/src/main/cpp
set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# Use GLOB to find sources properly without manual path duplication
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

# Essential Flags for N64 Porting
target_compile_options(bkawrapper PRIVATE 
    -fcommon 
    -w 
    -fno-builtin
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
