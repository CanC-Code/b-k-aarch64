#include <jni.h>
#include <android/log.h>
#include <mutex>
#include "emulator.h"

#define LOG_TAG "EMULATOR_JNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::mutex menuMutex;
static bool menuInitialized = false;

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeInitMenu(JNIEnv* env, jclass clazz, jobject menuOverlay) {
    std::lock_guard<std::mutex> lock(menuMutex);
    if (!menuInitialized) {
        // Optionally store menuOverlay reference
        LOGI("Menu initialized via JNI");
        menuInitialized = true;
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeOnBackPressed(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(menuMutex);
    LOGI("NativeMenu toggle requested");
    Emulator::toggleMenu();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativePauseEmulator(JNIEnv* env, jclass clazz) {
    LOGI("NativeMenu pause requested");
    Emulator::pause();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeResumeEmulator(JNIEnv* env, jclass clazz) {
    LOGI("NativeMenu resume requested");
    Emulator::resume();
}

} // extern "C"