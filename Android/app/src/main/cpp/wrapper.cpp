// File: app/src/main/cpp/wrapper.cpp
#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

// Example: core initialization function
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitCore(JNIEnv* env, jobject thiz) {
    LOGI("Core initialized");
    // TODO: Core setup (ROMs, renderer, etc.)
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnCoreStep(JNIEnv* env, jobject thiz) {
    // Called per frame/tick
}

// JNI_OnLoad only exists here
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    LOGI("Wrapper JNI_OnLoad called");
    return JNI_VERSION_1_6;
}

} // extern "C"