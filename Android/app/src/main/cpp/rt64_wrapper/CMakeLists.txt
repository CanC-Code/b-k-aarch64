cmake_minimum_required(VERSION 3.20)
project(rt64_wrapper LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)

set(RT64_STATIC ON CACHE BOOL "Build RT64 static" FORCE)
set(PLUME_X11_ENABLED OFF CACHE BOOL "" FORCE)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../rt64 rt64-build)

add_library(rt64_wrapper SHARED rt64_wrapper.cpp)
target_compile_definitions(rt64_wrapper PRIVATE HLSL_CPU=1 F3DEX_GBI=1 __ANDROID__=1)
target_include_directories(rt64_wrapper PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../rt64/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../rt64/src
    ${CMAKE_CURRENT_SOURCE_DIR}/../rt64/src/hle
    ${CMAKE_CURRENT_SOURCE_DIR}/../rt64/src/common
    ${CMAKE_CURRENT_SOURCE_DIR}/../rt64/src/contrib/hlslpp/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../rt64/src/contrib
    ${CMAKE_CURRENT_SOURCE_DIR}/../rt64/src/contrib/android_sdl_stub
)
target_link_libraries(rt64_wrapper rt64)
