// File: app/src/main/cpp/menu/menu.cpp
#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BK_MENU"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

// Called from Java to initialize the menu system
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jobject thiz) {
    LOGI("Menu initialized");
    // TODO: Initialize menu state, load assets, etc.
}

// Called from Java when the back button is pressed
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv* env, jobject thiz) {
    LOGI("Back pressed in menu");
    // Return true if menu handled it, false to propagate
    return JNI_FALSE;
}

} // extern "C"