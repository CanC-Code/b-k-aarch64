#include <jni.h>
#include <android/log.h>
#include <atomic>

// Menu system
#include "menu/menu.hpp"

// Emulator stubs (Android-specific)
#include "emulator/stubs.h"
#include "emulator/texture_stubs.h"

// Ultra / OTR
#include "ultra/otr_builder.h"

#define LOG_TAG "BKA_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

/*
 * Global state
 */
static std::atomic<bool> g_paused{false};
static MenuHandler* g_menu = nullptr;

extern "C" {

/*
 * JNI: Menu initialization
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeInitMenu(
        JNIEnv* env,
        jclass,
        jobject menuView) {

    if (!g_menu) {
        g_menu = new MenuHandler(env, menuView);
        LOGI("Menu initialized");
    }
}

/*
 * JNI: Back press / toggle menu
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeOnBackPressed(
        JNIEnv*,
        jclass) {

    if (!g_menu) {
        return;
    }

    if (g_menu->isVisible()) {
        g_menu->hide();
        g_paused.store(false);
    } else {
        g_menu->show();
        g_paused.store(true);
    }
}

/*
 * JNI: Pause emulator
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativePauseEmulator(
        JNIEnv*,
        jclass) {

    g_paused.store(true);
    LOGI("Emulator paused");
}

/*
 * JNI: Resume emulator
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeResumeEmulator(
        JNIEnv*,
        jclass) {

    if (g_menu) {
        g_menu->hide();
    }

    g_paused.store(false);
    LOGI("Emulator resumed");
}

} // extern "C"