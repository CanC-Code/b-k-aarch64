cmake_minimum_required(VERSION 3.18)
project(bkawrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 99)

# 1. Global Definitions
add_definitions(-DVERSION_US=1 -D_LANGUAGE_C -DN_AUDIO -D__BOOL_H__)

# 2. Source Collection
# This finds the 860+ files moved by the script
file(GLOB_RECURSE GAME_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/game_src/*.c")

set(WRAPPER_SOURCES
    ultra/NativeBridge.cpp
    ultra/otr_builder.cpp
    ultra/audio_helper.cpp
    ultra/exceptasm.cpp
    ultra/libm_vals.cpp
    emulator/stubs.cpp
    tools/rare_decompression.cpp
)

# 3. Build the shared library
add_library(bkawrapper SHARED ${WRAPPER_SOURCES} ${GAME_SOURCES})

# 4. Header Management
target_include_directories(bkawrapper SYSTEM PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR
)

target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/game_src
)

# 5. Compiler Flags
# Fixed: Explicitly repeating -include for each file
target_compile_options(bkawrapper PRIVATE
    -fno-builtin
    -w
    -fsigned-char
    -include "${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR/ultratypes.h"
    -include "${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR/gbi.h"
)

# 6. Linking
find_library(log-lib log)
find_library(android-lib android)
find_library(jnigraphics-lib jnigraphics)
find_library(z-lib z)

target_link_libraries(bkawrapper
    ${log-lib}
    ${android-lib}
    ${jnigraphics-lib}
    ${z-lib}
    atomic
    m
)
