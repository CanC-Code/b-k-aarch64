// wrapper.cpp
// JNI bridge + wrapper logic
#include <jni.h>
#include <android/log.h>

#define LOG_TAG "Wrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

// Declare stub/OTR functions without defining them
void core1_stepCPU();
void core2_stepFrame();
void n_audioStep();
void n_audioGetBuffer();
void n_audioInit();
void core1_reset();

// OTR functions from otr_builder.cpp
int core1_loadOTR(const char* path);
void* getOTRData();
int saveOTRToFile(const char* path);

} // extern "C"

// Example JNI function calling stubs
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stepCPU(JNIEnv* env, jobject /*thiz*/) {
    core1_stepCPU();
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stepFrame(JNIEnv* env, jobject /*thiz*/) {
    core2_stepFrame();
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_audioStep(JNIEnv* env, jobject /*thiz*/) {
    n_audioStep();
}