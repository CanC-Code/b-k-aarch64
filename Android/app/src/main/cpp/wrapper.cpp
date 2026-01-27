#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BKA_Wrapper"

// This is the main entry point called by Android when the library loads
extern "C"
jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI_OnLoad: Native Library Loading...");
    
    JNIEnv* env;
    if (vm->GetEnv((void**)&env, JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }

    return JNI_VERSION_1_6;
}

// Matches your MainActivity.java 'initNative' call
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_initNative(JNIEnv* env, jobject thiz) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Native Bridge Linked to MainActivity");
}
