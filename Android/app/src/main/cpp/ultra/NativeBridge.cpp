#include <jni.h>
#include <android/log.h>

#define LOG_TAG "NativeBridge"

extern "C" {

// Matches: com.bkawrapper.NativeBridge.processFrame()
// This is the ONLY definition of this function in the whole project.
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processFrame(JNIEnv* env, jobject thiz, jbyteArray data) {
    // Logic for frame processing
    __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, "Processing frame in NativeBridge.cpp");
}

} // extern "C"
