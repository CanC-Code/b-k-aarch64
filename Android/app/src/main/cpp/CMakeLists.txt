// File: wrapper.cpp
// Author: CCVO
// Purpose: JNI wrapper for BKA / N64 emulator integration
// Updated to fix undeclared 'env' issues for Android NDK build
#include <jni.h>
#include <string>
#include <fstream>
#include <mutex>

#include "ultra/parameters.h"
#include "ultra/libm_vals.h"
#include "ultra/otr_builder.h"
#include "ultra/setintmask.h"
#include "ultra/exceptasm.h"
#include "emulator/stubs.h"
#include "emulator/texture_stubs.h"

static std::mutex gMutex;

// Example OTR buffer (replace with your real data)
static unsigned char* gOtrData = nullptr;
static size_t gOtrSize = 0;

extern "C" {

// Save OTR data to file
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(JNIEnv* env, jclass clazz, jstring path) {
    const char* cpath = env->GetStringUTFChars(path, nullptr);
    std::lock_guard<std::mutex> lock(gMutex);

    if (gOtrData && gOtrSize > 0) {
        std::ofstream out(cpath, std::ios::binary);
        if (out.is_open()) {
            out.write(reinterpret_cast<const char*>(gOtrData), gOtrSize);
            out.close();
        }
    }

    env->ReleaseStringUTFChars(path, cpath);
}

// Set OTR data from Java byte array
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_setOtrData(JNIEnv* env, jclass clazz, jbyteArray data) {
    std::lock_guard<std::mutex> lock(gMutex);

    jsize len = env->GetArrayLength(data);
    if (len > 0) {
        delete[] gOtrData;
        gOtrData = new unsigned char[len];
        env->GetByteArrayRegion(data, 0, len, reinterpret_cast<jbyte*>(gOtrData));
        gOtrSize = len;
    }
}

// Clear OTR buffer
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_clearOtrData(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gMutex);
    delete[] gOtrData;
    gOtrData = nullptr;
    gOtrSize = 0;
}

// Stub: Initialize emulator (placeholder)
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initEmulator(JNIEnv* env, jclass clazz) {
    // Initialize emulator components if needed
}

// Stub: Load ROM
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(JNIEnv* env, jclass clazz, jstring romPath) {
    const char* cpath = env->GetStringUTFChars(romPath, nullptr);
    // TODO: Implement actual ROM loading here
    env->ReleaseStringUTFChars(romPath, cpath);
}

// Stub: Run emulator frame
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runFrame(JNIEnv* env, jclass clazz) {
    // TODO: Run one frame of the emulator
}

// Stub: Shutdown emulator
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_shutdownEmulator(JNIEnv* env, jclass clazz) {
    // TODO: Clean up emulator state
    std::lock_guard<std::mutex> lock(gMutex);
    delete[] gOtrData;
    gOtrData = nullptr;
    gOtrSize = 0;
}

} // extern "C"