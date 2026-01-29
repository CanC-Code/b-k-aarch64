cmake_minimum_required(VERSION 3.22.1)

project("bkawrapper")

# Define include directories based on the compiler command line in the logs
include_directories(
    src/main/cpp
    src/main/cpp/include
    src/main/cpp/include/ultra64
    src/main/cpp/include/core1
    src/main/cpp/include/core2
    src/main/cpp/include/2.0L
    src/main/cpp/include/2.0L/PR
    src/main/cpp/tools
    src/main/cpp/emulator
    src/main/cpp/ultra
    src/main/cpp/game_src
)

# Add all relevant source files found in the build logs
add_library(bkawrapper SHARED
    tools/rare_decompression.cpp
    ultra/otr_builder.cpp
    # Add other .c and .cpp files from your src/main/cpp directories here
)

# Link against the Android log library (standard for NDK projects)
find_library(log-lib log)
target_link_libraries(bkawrapper ${log-lib})
