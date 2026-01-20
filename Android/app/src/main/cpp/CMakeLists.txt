# File: app/src/main/cpp/CMakeLists.txt
cmake_minimum_required(VERSION 3.18)
project(bk_wrapper)

add_library(
    bk_wrapper
    SHARED
    wrapper.cpp
    menu/menu.cpp
)

find_library(log-lib log)

target_link_libraries(
    bk_wrapper
    ${log-lib}
)