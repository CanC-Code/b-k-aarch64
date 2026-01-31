cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX)

set(CPP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")
set(GAME_SRC_DIR "${CPP_ROOT}/src")
set(GAME_INC_DIR "${CPP_ROOT}/include")

file(GLOB_RECURSE GAME_SOURCES "${GAME_SRC_DIR}/*.c" "${GAME_SRC_DIR}/*.cpp")

add_library(bkawrapper SHARED
    ${GAME_SOURCES}
    "${ULTRA_DIR}/NativeBridge.cpp"
    "${ULTRA_DIR}/otr_builder.cpp"
    "${ULTRA_DIR}/audio_helper.cpp"
    "${ULTRA_DIR}/exceptasm.cpp"
)

target_include_directories(bkawrapper PRIVATE
    ${CPP_ROOT}
    ${ULTRA_DIR}
    ${GAME_INC_DIR}
    ${GAME_INC_DIR}/2.0L
    ${GAME_INC_DIR}/2.0L/PR
)

target_compile_definitions(bkawrapper PRIVATE _LANGUAGE_C)
target_compile_options(bkawrapper PRIVATE -w -fcommon -O3)

find_library(log-lib log)
find_library(android-lib android)
find_library(z-lib z)

target_link_libraries(bkawrapper ${log-lib} ${android-lib} ${z-lib} atomic m)
