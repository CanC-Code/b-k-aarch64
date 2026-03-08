cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# Define the root of your decompiled source relative to this file
set(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../decomp-files")

# Correct the GLOB to point to the actual source tree
file(GLOB_RECURSE GAME_SOURCES 
    "${DECOMP_ROOT}/src/*.c"
    "${DECOMP_ROOT}/src/*.cpp"
)

add_library(bkawrapper SHARED
    ${GAME_SOURCES}
    ultra/NativeBridge.cpp
    ultra/otr_builder.cpp
    ultra/audio_helper.cpp
    ultra/exceptasm.cpp
    emulator/resource_mgr.cpp
    emulator/pi_hle.cpp
    emulator/stubs.cpp
    tools/rare_decompression.cpp
)

# Crucial: Add -D_LANGUAGE_C and the include paths for the N64 headers
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${DECOMP_ROOT}/include
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
)

target_compile_options(bkawrapper PRIVATE -w -fcommon)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
