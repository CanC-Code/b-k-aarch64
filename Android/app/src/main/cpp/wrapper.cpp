#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BKAWrapper_Main"

static JavaVM* g_vm = nullptr;

/**
 * JNI_OnLoad is the standard entry point for a native library.
 */
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    g_vm = vm;
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "BKAWrapper Library Loaded");
    return JNI_VERSION_1_6;
}
