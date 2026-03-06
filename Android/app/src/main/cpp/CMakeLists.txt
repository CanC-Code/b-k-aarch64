cmake_minimum_required(VERSION 3.22.1)
project("bkawrapper")

# Add Zlib for Rare Decompression
find_package(ZLIB REQUIRED)

add_library(bkawrapper SHARED
    # Main Bridges
    ultra/NativeBridge.cpp
    
    # Emulator Core / PI HLE
    emulator/resource_mgr.cpp
    emulator/pi_hle.cpp
    emulator/stubs.cpp
    
    # Tools & Decompression
    tools/rare_decompression.cpp
    
    # Exception & Context Handling
    ultra/exceptasm.cpp
)

# Link Android logging and Zlib
find_library(log-lib log)
target_link_libraries(bkawrapper 
    ${log-lib} 
    ${ZLIB_LIBRARIES}
    android
)

# Ensure C++17 for Harmonizer compatibility
target_compile_features(bkawrapper PRIVATE cxx_std_17)
