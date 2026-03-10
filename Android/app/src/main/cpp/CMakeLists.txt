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
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/include
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/include/2.0L
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/include/core1
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/include/core2
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/include/gc
)

# Explicitly list core1 sources
set(CORE1_SOURCES
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_0.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_11AC0.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_15B30.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_1D00.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_1D5D0.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_3250.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_5650.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_660.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_7090.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_72B0.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_7F60.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_8C50.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/code_CE60.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/crccalc.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/data_1E820.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/debugtext.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/defragmanager.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/depthbuffer.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/eeprom.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/framebufferdraw.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/cosf.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/mtxutil.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/normalize.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/ortho.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/rotate.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/sinf.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/sqrtf.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/gu/translate.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/initthread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/inflate.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/ai.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/aigetlen.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/aisetfreq.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/aisetnextbuf.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/cartrominit.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/conteeplongread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/conteeplongwrite.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/conteepread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/conteepwrite.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/contpfs.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/contramread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/contramwrite.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/contreaddata.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/controller.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/contsetch.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/crc.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/devmgr.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/dpgetstat.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/dpsetstat.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/epirawdma.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/epirawread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/epirawwrite.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/leodiskinit.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/leointerrupt.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/ll.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/ll_cvt.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/lookup.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/memory.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/ml.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/mlmtx.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/motor.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/musicplayer.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/n_reverb_add01.c_
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/n_reverb_add02.c_
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/n_reverb_add03.c_
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/n_reverb_add04.c_
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/overlay.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/overlaymanager.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pfsgetstatus.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pfsinit.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pfsisplug.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pfsmanager.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/piacs.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pigetcmdq.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pirawdma.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pirawread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/pimgr.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/si.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/siacs.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sirawdma.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sirawread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sirawwrite.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sns.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sp.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/spgetstat.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/spsetpc.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/spsetstat.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sptask.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sptaskyield.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/sptaskyielded.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/stub_13640.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/stub_1D590.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/stub_2FA0.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/stub_3A70.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/syncprintf.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/vimgr.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/vimodempallan1.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/vimodentsclan1.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/vimodepallan1.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/visetevent.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/visetmode.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/visetspecial.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/viswapbuf.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/io/viswapcontext.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/createmesgqueue.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/destroythread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/getthreadpri.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/gettime.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/initialize.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/jammesg.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/kdebugserver.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/pidma.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/recvmesg.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/resetglobalintmask.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/sendmesg.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/seteventmesg.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/setglobalintmask.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/setthreadpri.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/startthread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/thread.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/timerintr.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/virtualtophysical.c
    /home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/src/core1/os/yieldthread.c
)

# Add all assembly files
file(GLOB_RECURSE ASM_SOURCES
    "/home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/asm/ultra/*.s"
    "/home/runner/work/b-k-aarch64/b-k-aarch64/decomp-files/asm/core1/ultra/*.s"
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