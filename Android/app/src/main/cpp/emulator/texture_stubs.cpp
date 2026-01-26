#include <jni.h>
#include <android/log.h>

#define LOG_TAG "BK_TEXTURE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv*, jclass) {
    LOGI("initTexture stub called");
    return 1; // dummy texture ID
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv*, jclass, jint) {
    // no-op stub
}

}
