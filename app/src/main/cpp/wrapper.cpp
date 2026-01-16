#include <jni.h>
#include <string>

extern "C"
JNIEXPORT jstring JNICALL
Java_com_bkawrapper_MainActivity_stringFromJNI(JNIEnv* env, jobject /* this */) {
    std::string hello = "BKA Wrapper APK";
    return env->NewStringUTF(hello.c_str());
}