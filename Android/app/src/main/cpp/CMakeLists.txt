cmake_minimum_required(VERSION 3.22.1)
project(bkawrapper LANGUAGES C CXX ASM)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(DECOMP_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../decomp-files" ABSOLUTE)

set(CPP_ROOT  "${CMAKE_CURRENT_SOURCE_DIR}")
set(ULTRA_DIR "${CPP_ROOT}/ultra")

set(COMMON_C_FLAGS "-w -fcommon -O2 -fno-builtin -D_ULTRATYPES_H_ -include stdint.h -D_FINALROM")
set(CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   ${COMMON_C_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -w -fcommon -O2 -D_FINALROM")

add_definitions(-D_LANGUAGE_C -DF3DEX_GBI_2)

include_directories(
    ${DECOMP_ROOT}/include/2.0L/PR
    ${DECOMP_ROOT}/include/2.0L
    ${DECOMP_ROOT}/include
    ${CPP_ROOT}
    ${ULTRA_DIR}
    ${DECOMP_ROOT}/include/core1
    ${DECOMP_ROOT}/include/core2
    ${DECOMP_ROOT}/include/gc
    ${DECOMP_ROOT}/src/core1
    ${DECOMP_ROOT}/src/core1/audio
)

set(FORCED_INCLUDES "-include ${DECOMP_ROOT}/include/2.0L/PR/gbi.h -include ${DECOMP_ROOT}/include/2.0L/PR/abi.h")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${FORCED_INCLUDES}")

file(GLOB_RECURSE CORE1_SOURCES "${DECOMP_ROOT}/src/core1/*.c")
file(GLOB ASM_SOURCES "${DECOMP_ROOT}/asm/ultra/*.s" "${DECOMP_ROOT}/asm/core1/ultra/*.s")
set_source_files_properties(${ASM_SOURCES} PROPERTIES LANGUAGE ASM)

set(WRAPPER_SOURCES
    ${ULTRA_DIR}/NativeBridge.cpp ${ULTRA_DIR}/otr_builder.cpp
    ${ULTRA_DIR}/audio_helper.cpp ${ULTRA_DIR}/exceptasm.cpp
    ${ULTRA_DIR}/setintmask.cpp ${ULTRA_DIR}/libm_vals.cpp
    ${ULTRA_DIR}/parameters.cpp ${CPP_ROOT}/emulator/pi_hle.cpp
    ${CPP_ROOT}/emulator/resource_mgr.cpp ${CPP_ROOT}/emulator/stubs.cpp
    ${CPP_ROOT}/menu/menu.cpp
)

add_library(bkawrapper SHARED ${CORE1_SOURCES} ${ASM_SOURCES} ${WRAPPER_SOURCES})
target_link_libraries(bkawrapper log android z GLESv2 EGL atomic m)
