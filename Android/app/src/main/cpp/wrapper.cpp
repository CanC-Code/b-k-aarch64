#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BKA_Wrapper"

// The JVM calls this once when the library is loaded.
// Consolidation here fixes the 'duplicate symbol' error.
extern "C"
jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI_OnLoad: Library successfully linked");
    
    JNIEnv* env;
    if (vm->GetEnv((void**)&env, JNI_VERSION_1_6) != JNI_OK) {
        return JNI_ERR;
    }

    return JNI_VERSION_1_6;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_initNative(JNIEnv* env, jobject thiz) {
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "MainActivity native bridge initialized");
}
