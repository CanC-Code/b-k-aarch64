cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# CMAKE_CURRENT_SOURCE_DIR is /home/runner/work/.../Android/app/src/main/cpp
set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# Automatically find all source files in the project subdirectories
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
    "${CPP_ROOT}/game_src/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# Include Directories - Rooted correctly to avoid src/main/cpp/src/main/cpp
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

# Build flags for legacy N64 source compatibility
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
