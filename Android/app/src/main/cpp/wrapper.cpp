#include <jni.h>
#include <android/log.h>
#include "ultra/NativeBridge.hpp"

#define LOG_TAG "BKA_Wrapper"

// Global variable to store the VM reference if needed elsewhere
JavaVM* g_vm = nullptr;

extern "C"
jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI_OnLoad: Initializing BKA Wrapper");
    
    g_vm = vm;
    JNIEnv* env;
    if (vm->GetEnv((void**)&env, JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }

    // Initialize the NativeBridge components
    // If NativeBridge had specific class registration logic, it goes here
    NativeBridge::initialize(vm);

    return JNI_VERSION_1_6;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_initNative(JNIEnv* env, jobject thiz) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Native library initialized from Java");
}
