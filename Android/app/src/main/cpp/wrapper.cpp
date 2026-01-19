// wrapper.cpp
// Purpose: JNI bridge for core emulator and menu integration
// Cleaned version: menu logic handled via NativeMenu JNI

#include <jni.h>
#include <android/log.h>
#include <mutex>
#include "emulator.h" // your emulator core headers

#define LOG_TAG "EMULATOR_JNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static std::mutex menuMutex;
static bool menuInitialized = false;

// Forward declarations
extern "C" {
    JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativeInitMenu(JNIEnv* env, jclass clazz, jobject menuOverlay);
    JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativeOnBackPressed(JNIEnv* env, jclass clazz);
    JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativePauseEmulator(JNIEnv* env, jclass clazz);
    JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativeResumeEmulator(JNIEnv* env, jclass clazz);
}

// Called once to initialize menu overlay
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativeInitMenu(JNIEnv* env, jclass clazz, jobject menuOverlay) {
    std::lock_guard<std::mutex> lock(menuMutex);
    if (!menuInitialized) {
        // If needed, store menuOverlay global reference
        // jobject gMenuOverlay = env->NewGlobalRef(menuOverlay);

        LOGI("Menu initialized via JNI");
        menuInitialized = true;
    }
}

// Called when back button or swipe triggers menu toggle
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativeOnBackPressed(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(menuMutex);

    // Forward to emulator core menu logic
    // Example: toggle pause / display overlay
    LOGI("NativeMenu toggle requested");

    // Implement your own function to toggle menu in the emulator:
    Emulator::toggleMenu();
}

// Pause the emulator (menu or system triggered)
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativePauseEmulator(JNIEnv* env, jclass clazz) {
    LOGI("NativeMenu pause requested");
    Emulator::pause();
}

// Resume the emulator
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeMenu_nativeResumeEmulator(JNIEnv* env, jclass clazz) {
    LOGI("NativeMenu resume requested");
    Emulator::resume();
}