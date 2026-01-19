// NativeBridge.cpp
#include <jni.h>
#include "otr_generator.hpp"
#include <vector>

static OTRGenerator* g_otrGenerator = nullptr;

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initOTRGenerator(JNIEnv* env, jobject thiz, jobject assetManager) {
    if (g_otrGenerator) delete g_otrGenerator;
    g_otrGenerator = new OTRGenerator(AAssetManager_fromJava(env, assetManager));
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_generateOTR(JNIEnv* env, jobject thiz, jbyteArray romBuffer, jstring yamlPath) {
    if (!g_otrGenerator) return JNI_FALSE;

    jsize size = env->GetArrayLength(romBuffer);
    std::vector<uint8_t> buffer(size);
    env->GetByteArrayRegion(romBuffer, 0, size, reinterpret_cast<jbyte*>(buffer.data()));

    const char* path = env->GetStringUTFChars(yamlPath, nullptr);
    bool success = g_otrGenerator->generate(buffer, path); // must implement generate()
    env->ReleaseStringUTFChars(yamlPath, path);
    return success ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(JNIEnv* env, jobject thiz) {
    return g_otrGenerator ? g_otrGenerator->getProgress() : 0.0f;
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadOTRIntoRenderer(JNIEnv* env, jobject thiz) {
    if (g_otrGenerator) g_otrGenerator->loadIntoRenderer(); // implement this
}