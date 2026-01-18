cmake_minimum_required(VERSION 3.18)

project(bkawrapper LANGUAGES C CXX)

# ------------------------------
# Set C++ standard
# ------------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ------------------------------
# Source files: main cpp folder + ultra/ + emulator/
# ------------------------------
file(GLOB_RECURSE WRAPPER_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/ultra/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/emulator/*.cpp"
)

# ------------------------------
# Include directories
# ------------------------------
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/otr_generator
    ${ANDROID_NDK}/sources/android/native_app_glue
    ${ANDROID_NDK}/sysroot/usr/include
)

# Ensure Android macro for conditional compilation
add_definitions(-DANDROID)

# ------------------------------
# Embed OTR YAML files at build time
# ------------------------------
set(OTR_PAL_YAML   ${CMAKE_CURRENT_SOURCE_DIR}/Android/app/src/main/assets/otr_yaml/decompressed.pal.yaml)
set(OTR_US_YAML    ${CMAKE_CURRENT_SOURCE_DIR}/Android/app/src/main/assets/otr_yaml/decompressed.us.v10.yaml)
set(EMBED_CPP      ${CMAKE_CURRENT_BINARY_DIR}/otr_assets.cpp)

# CMake function to convert binary file to C++ array
function(embed_yaml FILE_PATH VAR_NAME SIZE_NAME)
    file(READ ${FILE_PATH} BINARY DATA)
    file(WRITE ${EMBED_CPP} "#include \"otr_assets.hpp\"\n\n"  ) # initial write only once
    file(APPEND ${EMBED_CPP} "const uint8_t ${VAR_NAME}[] = {\n")
    foreach(i RANGE 0 $<LENGTH:${DATA}> 1)
        string(SUBSTRING "${DATA}" ${i} 1 CHAR)
        string(APPEND CHAR_HEX "0x" "$<FORMAT:%02X>" "${CHAR}", ")
        if((i + 1) % 12 EQUAL 0)
            file(APPEND ${EMBED_CPP} "${CHAR_HEX}\n")
            set(CHAR_HEX "")
        endif()
    endforeach()
    if(CHAR_HEX)
        file(APPEND ${EMBED_CPP} "${CHAR_HEX}\n")
    endif()
    file(APPEND ${EMBED_CPP} "};\n")
    file(APPEND ${EMBED_CPP} "const size_t ${SIZE_NAME} = sizeof(${VAR_NAME});\n\n")
endfunction()

# Embed both YAMLs
embed_yaml(${OTR_PAL_YAML} embedded_pal_yaml embedded_pal_size)
embed_yaml(${OTR_US_YAML} embedded_us_yaml embedded_us_size)

# Add the generated file to our sources
list(APPEND WRAPPER_SOURCES ${EMBED_CPP})

# ------------------------------
# Create shared library
# ------------------------------
add_library(wrapper SHARED ${WRAPPER_SOURCES})

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