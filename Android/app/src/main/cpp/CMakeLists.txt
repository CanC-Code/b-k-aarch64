cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

# Path setup
set(SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR})

# Add all your library source files
# Note: Ensure all necessary .cpp and .c files are listed or globbed correctly
file(GLOB_RECURSE LIB_SOURCES 
    "${SOURCE_DIR}/emulator/*.cpp"
    "${SOURCE_DIR}/ultra/*.cpp"
    "${SOURCE_DIR}/game_src/*.c"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# Include Directories - Order matters!
target_include_directories(bkawrapper PRIVATE
    ${SOURCE_DIR}
    ${SOURCE_DIR}/tools
    ${SOURCE_DIR}/emulator
    ${SOURCE_DIR}/ultra
    ${SOURCE_DIR}/game_src
    ${SOURCE_DIR}/include
    ${SOURCE_DIR}/include/2.0L
    ${SOURCE_DIR}/include/2.0L/PR  # Where renamed headers live
)

# Compiler Flags
target_compile_options(bkawrapper PRIVATE 
    -fcommon            # Essential for legacy N64 C code (global variable sharing)
    -fno-builtin        # Prevents Clang from optimizing away our custom N64 functions
    -w                  # Suppresses the massive amount of legacy warnings
    -fsigned-char
    -DN_AUDIO=1
    -DVERSION_US=1
    -D_LANGUAGE_C
)

# Standard Android Libraries
target_link_libraries(bkawrapper
    android
    log
    GLESv3
    z
)
