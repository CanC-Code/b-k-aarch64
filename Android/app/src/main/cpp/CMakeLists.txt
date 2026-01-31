cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# Use C++17 for NativeBridge and modern OTR logic
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CPP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")
set(GAME_SRC_DIR "${CPP_ROOT}/src")
set(GAME_INC_DIR "${CPP_ROOT}/include")

# GLOB_RECURSE is necessary because Harmonizer v3 preserves the tree structure
file(GLOB_RECURSE GAME_SOURCES 
    "${GAME_SRC_DIR}/*.c" 
    "${GAME_SRC_DIR}/*.cpp"
)

add_library(bkawrapper SHARED
    ${GAME_SOURCES}
    "${ULTRA_DIR}/NativeBridge.cpp"
    "${ULTRA_DIR}/otr_builder.cpp"
    "${ULTRA_DIR}/audio_helper.cpp"
    "${ULTRA_DIR}/exceptasm.cpp"
    # Ensure any .s files in ultra/ are included if they aren't C++ wrapped
    "${ULTRA_DIR}/setintmask.s"
    "${ULTRA_DIR}/libm_vals.s"
    "${ULTRA_DIR}/parameters.s"
)

target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${ULTRA_DIR}
    ${GAME_INC_DIR}
    ${GAME_INC_DIR}/2.0L
    ${GAME_INC_DIR}/2.0L/PR
    # Add the core1/core2 includes specifically if Harmonizer places them there
    ${GAME_INC_DIR}/core1
    ${GAME_INC_DIR}/core2
)

# _LANGUAGE_C is needed for the decompiled headers to behave correctly
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# -fcommon is critical for decompilation projects to handle multiple global definitions
target_compile_options(bkawrapper PRIVATE -w -fcommon -O3)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

# 'm' (math) and 'atomic' are required for the emulator/bridge logic
target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
