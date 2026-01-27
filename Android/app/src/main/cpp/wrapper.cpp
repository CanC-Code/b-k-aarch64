#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BKA_Wrapper"

extern "C" {

// Library Entry Point - Only defined here
jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI_OnLoad: Library Loaded");
    return JNI_VERSION_1_6;
}

// Matches: com.bkawrapper.MainActivity.initNative()
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_initNative(JNIEnv* env, jobject thiz) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "MainActivity linked to native");
}

} // extern "C"
