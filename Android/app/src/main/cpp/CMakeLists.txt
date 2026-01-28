cmake_minimum_required(VERSION 3.18)
project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Define the source files explicitly to ensure clean builds
set(WRAPPER_SOURCES
    ultra/NativeBridge.cpp
    ultra/otr_builder.cpp
    ultra/audio_helper.cpp
    ultra/exceptasm.cpp
    ultra/libm_vals.cpp
    emulator/stubs.cpp
    tools/rare_decompression.cpp
)

# Build the shared library
add_library(bkawrapper SHARED ${WRAPPER_SOURCES})

# Include directories - added '.' to ensure headers in the root of cpp/ are found
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

# Locate Android-specific system libraries
find_library(log-lib log)
find_library(android-lib android)
find_library(jnigraphics-lib jnigraphics) # Useful for advanced asset/buffer handling
find_library(z-lib z)

# Link everything together
target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${jnigraphics-lib}
    ${z-lib}
    atomic
    m
)
