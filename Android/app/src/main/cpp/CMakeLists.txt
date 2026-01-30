cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# [span_1](start_span)Build the native shared library[span_1](end_span)
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

# [span_2](start_span)Target-scoped include directories[span_2](end_span)
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

# [span_3](start_span)Fix "unknown type name" errors (u8, s32, size_t, etc.)[span_3](end_span)
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# [span_4](start_span)FIXED: Target-level header injection[span_4](end_span)
# Each header MUST have its own "-include" string to avoid Clang parsing errors.
# This resolves the "multiple output files" error seen in the recent log.
target_compile_options(bkawrapper PRIVATE
    "-include" "stddef.h"
    "-include" "stdint.h"
    "-include" "string.h"
    "-include" "${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR/ultratypes.h"
)

# [span_5](start_span)Android system libraries[span_5](end_span)
find_library(log-lib log)
find_library(android-lib android)
find_library(jnigraphics-lib jnigraphics)
find_library(z-lib z)

# [span_6](start_span)Link everything together[span_6](end_span)
target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${jnigraphics-lib}
    ${z-lib}
    atomic
    m
)
