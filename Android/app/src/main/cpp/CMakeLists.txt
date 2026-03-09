cmake_minimum_required(VERSION 3.22.1)

project(bkawrapper)

# Enable C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set output directories
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# Include directories for the project
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator
    ${CMAKE_CURRENT_SOURCE_DIR}/tools
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/2.0L
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/core1
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/core2
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/include/gc
)

# Explicitly list core1 sources (where mainLoop is defined)
set(CORE1_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_0.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_11AC0.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_15B30.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_1D00.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_1D5D0.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_3250.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_5650.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_660.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_7090.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_72B0.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_7F60.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_8C50.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/code_CE60.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/crccalc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/data_1E820.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/debugtext.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/defragmanager.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/depthbuffer.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/eeprom.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/framebufferdraw.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/cosf.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/mtxutil.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/normalize.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/ortho.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/rotate.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/sinf.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/sqrtf.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/gu/translate.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/initthread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/inflate.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/ai.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/aigetlen.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/aisetfreq.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/aisetnextbuf.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/cartrominit.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/conteeplongread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/conteeplongwrite.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/conteepread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/conteepwrite.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/contpfs.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/contramread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/contramwrite.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/contreaddata.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/controller.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/contsetch.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/crc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/devmgr.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/dpgetstat.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/dpsetstat.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/epirawdma.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/epirawread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/epirawwrite.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/leodiskinit.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/leointerrupt.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/ll.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/ll_cvt.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/lookup.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/memory.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/ml.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/mlmtx.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/motor.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/musicplayer.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/n_reverb_add01.c_
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/n_reverb_add02.c_
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/n_reverb_add03.c_
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/n_reverb_add04.c_
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/overlay.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/overlaymanager.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pfsgetstatus.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pfsinit.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pfsisplug.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pfsmanager.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/piacs.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pigetcmdq.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pirawdma.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pirawread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/pimgr.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/si.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/siacs.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/siint.h
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sirawdma.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sirawread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sirawwrite.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sns.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sp.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/spgetstat.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/spsetpc.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/spsetstat.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sptask.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sptaskyield.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/sptaskyielded.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/stub_13640.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/stub_1D590.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/stub_2FA0.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/stub_3A70.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/syncprintf.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/vimgr.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/vimodempallan1.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/vimodentsclan1.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/vimodepallan1.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/visetevent.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/visetmode.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/visetspecial.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/viswapbuf.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/io/viswapcontext.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/createmesgqueue.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/destroythread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/getthreadpri.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/gettime.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/initialize.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/jammesg.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/kdebugserver.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/pidma.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/recvmesg.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/resetglobalintmask.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/sendmesg.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/seteventmesg.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/setglobalintmask.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/setthreadpri.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/startthread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/thread.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/timerintr.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/virtualtophysical.c
    ${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/src/core1/os/yieldthread.c
)

# Add all assembly files
file(GLOB_RECURSE ASM_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/asm/ultra/*.s"
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../../decomp-files/asm/core1/ultra/*.s"
)

# Add emulator and menu sources
set(EMULATOR_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/pi_hle.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/resource_mgr.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/emulator/stubs.cpp
)

set(MENU_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/menu/menu.cpp
)

set(ULTRA_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/NativeBridge.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/audio_helper.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/exceptasm.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/libm_vals.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/otr_builder.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/parameters.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/ultra/setintmask.cpp
)

# Combine all sources
set(ALL_SOURCES
    ${CORE1_SOURCES}
    ${ASM_SOURCES}
    ${EMULATOR_SOURCES}
    ${MENU_SOURCES}
    ${ULTRA_SOURCES}
)

# Create the shared library
add_library(
    bkawrapper
    SHARED
    ${ALL_SOURCES}
)

# Link against log and OpenGL ES
find_library(log-lib log)
target_link_libraries(
    bkawrapper
    ${log-lib}
    GLESv2
    android
    EGL
)

# Disable warnings as errors for decomp code
target_compile_options(
    bkawrapper
    PRIVATE
    -w
    -fcommon
)

# Android-specific flags
set_target_properties(
    bkawrapper
    PROPERTIES
    C_VISIBILITY_PRESET "hidden"
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN ON
)

# Enable ASM support for N64 assembly files
enable_language(ASM)
set_source_files_properties(
    ${ASM_SOURCES}
    PROPERTIES LANGUAGE ASM
)

# Disable optimizations for debug builds
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(
        bkawrapper
        PRIVATE
        -O0
        -g
    )
endif()