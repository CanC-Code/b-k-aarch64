cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

# ------------------------------
# Set C++ standard
# ------------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ------------------------------
# Source files
# ------------------------------
set(WRAPPER_SOURCES
    wrapper.cpp
    setinitmasks.cpp
    parameters.cpp
    exceptasm.cpp
)

add_library(wrapper SHARED ${WRAPPER_SOURCES})

# ------------------------------
# Include directories
# ------------------------------
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
)

# ------------------------------
# Find required Android libraries
# ------------------------------
find_library(log-lib log)
find_library(android-lib android)
find_library(glesv2-lib GLESv2)

# ------------------------------
# Link libraries
# ------------------------------
target_link_libraries(wrapper
    ${log-lib}
    ${android-lib}
    ${glesv2-lib}
)