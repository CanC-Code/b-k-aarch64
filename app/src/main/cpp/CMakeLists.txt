cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

add_library(wrapper SHARED wrapper.cpp)

find_library(log-lib log)

target_link_libraries(wrapper ${log-lib})