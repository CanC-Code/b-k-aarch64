cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

file(GLOB_RECURSE GAME_SOURCES 
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
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
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/include/2.0L/PR
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
)

# Remove the complex PCH generation for now—it's likely masking the real include errors
# target_compile_options(bkawrapper PRIVATE "-include" "${GLOBAL_PCH}")

target_compile_options(bkawrapper PRIVATE -w -fcommon)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)