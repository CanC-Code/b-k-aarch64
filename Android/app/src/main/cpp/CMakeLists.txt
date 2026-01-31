cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Explicitly define paths to Harmonized sources
set(GAME_SRC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src")
set(GAME_INC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")

# 2. Collect ALL harmonized game source files
file(GLOB_RECURSE GAME_SOURCES 
    "${GAME_SRC_DIR}/*.c"
    "${GAME_SRC_DIR}/*.cpp"
)

# 3. Define the library with absolute paths for bridge files
add_library(bkawrapper SHARED
    ${GAME_SOURCES}
    "${CMAKE_CURRENT_SOURCE_DIR}/NativeBridge.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/otr_builder.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/audio_helper.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/exceptasm.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/resource_mgr.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/pi_hle.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/stubs.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/tools/rare_decompression.cpp"
)

# 4. Include paths
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${GAME_INC_DIR}
    ${GAME_INC_DIR}/2.0L
    ${GAME_INC_DIR}/2.0L/PR
    ${GAME_SRC_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

# 5. Compiler Flags
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)
target_compile_options(bkawrapper PRIVATE -w -fcommon -O3)

# 6. Link standard Android & System libraries
find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper 
    ${log-lib} 
    ${android-lib} 
    ${z-lib} 
    atomic 
    m
)
