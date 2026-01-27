#include <jni.h>
#include <android/log.h>

#define LOG_TAG "NativeBridge"

// JNI_OnLoad removed from this file to resolve conflict with wrapper.cpp

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processFrame(JNIEnv* env, jobject thiz, jbyteArray data) {
    // Original logic preserved
    __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, "NativeBridge: processing frame");
}
