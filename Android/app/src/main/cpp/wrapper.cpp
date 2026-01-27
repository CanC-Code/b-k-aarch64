#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BKA_Wrapper"

extern "C" {

// 1. Library Entry Point
jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI_OnLoad called");
    return JNI_VERSION_1_6;
}

// 2. MainActivity Link (Matches com.bkawrapper.MainActivity)
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_initNative(JNIEnv* env, jobject thiz) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Native: initNative called successfully");
}

// 3. NativeBridge Link (Matches com.bkawrapper.NativeBridge)
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processFrame(JNIEnv* env, jobject thiz, jbyteArray data) {
    __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, "Native: processFrame called");
}

} // extern "C"
