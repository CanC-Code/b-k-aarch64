#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BKAWrapper_Main"

static JavaVM* g_vm = nullptr;

/**
 * JNI_OnLoad is the standard entry point for a native library.
 * It is only defined here to prevent duplicate symbol errors.
 */
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    g_vm = vm;
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "BKAWrapper Library Loaded");
    return JNI_VERSION_1_6;
}

/** * REMOVAL NOTICE:
 * The following JNI functions have been removed from this file:
 * - Java_com_bkawrapper_NativeBridge_nativeInit
 * - Java_com_bkawrapper_NativeBridge_runOtrGeneration
 * - Java_com_bkawrapper_NativeBridge_startGameLoop
 * - Java_com_bkawrapper_NativeBridge_pauseGameLoop
 * - Java_com_bkawrapper_NativeBridge_resumeGameLoop
 * - Java_com_bkawrapper_NativeBridge_cleanupGame
 * - Java_com_bkawrapper_NativeBridge_initTexture
 * - Java_com_bkawrapper_NativeBridge_updateTexture
 * * These are all fully implemented in NativeBridge.cpp. 
 * Defining them here caused the linker to fail with "duplicate symbol" errors.
 */
