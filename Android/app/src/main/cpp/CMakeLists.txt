cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

# 1. Define absolute path to the decompilation root
get_filename_component(DECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

# 2. Recursively collect ALL source files
file(GLOB_RECURSE GAME_SOURCES
    "${DECOMP_ROOT}/src/*.c"
    "${DECOMP_ROOT}/src/**/*.c"
)

# 3. Add all extra C++/utility files
list(APPEND GAME_SOURCES
    ultra/NativeBridge.cpp
    ultra/otr_builder.cpp
    ultra/audio_helper.cpp
    ultra/exceptasm.cpp
    emulator/resource_mgr.cpp
    emulator/pi_hle.cpp
    emulator/stubs.cpp
    tools/rare_decompression.cpp
)

add_library(bkawrapper SHARED ${GAME_SOURCES})

# 4. Automatically include ALL header directories
file(GLOB_RECURSE INCLUDE_DIRS "${DECOMP_ROOT}/include/*")
foreach(dir ${INCLUDE_DIRS})
    if(IS_DIRECTORY "${dir}")
        target_include_directories(bkawrapper PRIVATE "${dir}")
    endif()
endforeach()

# 5. Add project/local includes
target_include_directories(bkawrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
)

# 6. Compiler flags
target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)
target_compile_options(bkawrapper PRIVATE -w -fcommon)

# 7. Link libraries
find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)
target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)