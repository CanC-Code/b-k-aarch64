cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper)

set(CPP_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

# Automatically collect all source files now that they are local to the cpp folder
file(GLOB_RECURSE LIB_SOURCES 
    "${CPP_ROOT}/src/*.c"
    "${CPP_ROOT}/src/*.cpp"
    "${CPP_ROOT}/tools/*.cpp"
    "${CPP_ROOT}/emulator/*.cpp"
    "${CPP_ROOT}/ultra/*.cpp"
)

add_library(bkawrapper SHARED ${LIB_SOURCES})

# Include Directories - Pointing to the newly moved and renamed headers
target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${CPP_ROOT}/include
    ${CPP_ROOT}/include/2.0L
    ${CPP_ROOT}/include/2.0L/PR
    ${CPP_ROOT}/include/core1
    ${CPP_ROOT}/include/core2
)

target_link_libraries(bkawrapper android log z)
