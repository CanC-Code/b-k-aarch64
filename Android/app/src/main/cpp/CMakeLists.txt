cmake_minimum_required(VERSION 3.22.1)

project(bkawrapper LANGUAGES C CXX)

# Build the native shared library
add_library(bkawrapper SHARED
    ultra/NativeBridge.cpp
    ultra/otr_builder.cpp
    ultra/audio_helper.cpp
    ultra/exceptasm.cpp

    emulator/resource_mgr.cpp
    emulator/pi_hle.cpp
    emulator/stubs.cpp

    tools/rare_decompression.cpp
)

# Target-scoped include directories
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/game_src
)

# [span_5](start_span)Fix "unknown type name" errors (u8, s32, etc.)[span_5](end_span)
# We re-enable the essential definitions at the target level
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# Target-level header injection to ensure N64 types are available globally
# This is cleaner than build.gradle injection as it only affects this target
target_compile_options(bkawrapper PRIVATE
    -include "${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR/ultratypes.h"
)

# Android system libraries
find_library(log-lib log)
find_library(android-lib android)
find_library(jnigraphics-lib jnigraphics)
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
