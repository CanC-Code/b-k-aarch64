cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# Use C++17 for NativeBridge and modern OTR logic
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CPP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")
set(GAME_SRC_DIR "${CPP_ROOT}/src")
set(GAME_INC_DIR "${CPP_ROOT}/include")

# --- Harmonizer v6.3 Smart Discovery ---
# We discover all files but filter out NDK/Platform duplicates
file(GLOB_RECURSE ALL_C_FILES 
    "${GAME_SRC_DIR}/*.c" 
    "${GAME_SRC_DIR}/*.cpp"
)

foreach(FILE_PATH ${ALL_C_FILES})
    # Exclude lib/ and specific duplicates identified in build logs
    if(NOT FILE_PATH MATCHES "src/lib/" AND 
       NOT FILE_PATH MATCHES "inflate.c" AND 
       NOT FILE_PATH MATCHES "rarezip.c" AND
       NOT FILE_PATH MATCHES "gu")
        list(APPEND FILTERED_GAME_SOURCES ${FILE_PATH})
    endif()
endforeach()

add_library(bkawrapper SHARED
    ${FILTERED_GAME_SOURCES}
    "${ULTRA_DIR}/NativeBridge.cpp"
    "${ULTRA_DIR}/otr_builder.cpp"
    "${ULTRA_DIR}/audio_helper.cpp"
    "${ULTRA_DIR}/exceptasm.cpp"
    # Essential low-level assembly
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
    ${GAME_INC_DIR}/core1
    ${GAME_INC_DIR}/core2
)

# _LANGUAGE_C is needed for the decompiled headers to behave correctly
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)

# -fcommon handles multiple global definitions in decomp projects
# -w suppresses non-critical warnings from legacy source
target_compile_options(bkawrapper PRIVATE -w -fcommon -O3)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

# 'm' (math) and 'atomic' are required for the emulator/bridge logic
target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
