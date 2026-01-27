#include <jni.h>
#include <android/log.h>

#define LOG_TAG "NativeBridge"

// REMOVED JNI_OnLoad from here to fix the "Duplicate Symbol" error.
// The JNI_OnLoad in wrapper.cpp now handles the library startup.

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processFrame(JNIEnv* env, jobject thiz, jbyteArray data) {
    // This connects to the processFrame method in your NativeBridge.java
    __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, "Processing frame data from Java");
}
