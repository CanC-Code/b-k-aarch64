#include "NativeBridge.hpp"
#include <android/log.h>

#define LOG_TAG "NativeBridge"

// Static member initialization
JavaVM* NativeBridge::s_vm = nullptr;

void NativeBridge::initialize(JavaVM* vm) {
    s_vm = vm;
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "NativeBridge initialized with VM");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processFrame(JNIEnv* env, jobject thiz, jbyteArray data) {
    // Implementation for frame processing
}
