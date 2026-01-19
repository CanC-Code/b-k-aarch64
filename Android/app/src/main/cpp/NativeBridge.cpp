#include <jni.h>
#include <vector>
#include <mutex>
#include <android/asset_manager_jni.h>
#include "otr_generator.hpp"
#include "GLRenderer.hpp"

static std::unique_ptr<OTRGenerator> g_otrGenerator;
static std::mutex g_mutex;
static std::vector<uint8_t> g_romData;

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initOTRGenerator(JNIEnv* env, jobject /*thiz*/, jobject assetManager) {
    std::lock_guard<std::mutex> lock(g_mutex);
    if (!g_otrGenerator) {
        g_otrGenerator = std::make_unique<OTRGenerator>(AAssetManager_fromJava(env, assetManager));
    }
}

JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_loadROM(JNIEnv* env, jobject /*thiz*/, jbyteArray romBytes) {
    std::lock_guard<std::mutex> lock(g_mutex);
    jsize len = env->GetArrayLength(romBytes);
    g_romData.resize(len);
    env->GetByteArrayRegion(romBytes, 0, len, reinterpret_cast<jbyte*>(g_romData.data()));
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_generateOTR(JNIEnv* env, jobject /*thiz*/) {
    std::lock_guard<std::mutex> lock(g_mutex);
    if (!g_otrGenerator || g_romData.empty()) return JNI_FALSE;

    bool success = g_otrGenerator->generateOTR(g_romData);
    if (success) {
        GLRenderer::getInstance().setOTRData(g_otrGenerator->getOTRBuffer());
    }
    return success ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_clearOTR(JNIEnv* env, jobject /*thiz*/) {
    std::lock_guard<std::mutex> lock(g_mutex);
    g_romData.clear();
    if (g_otrGenerator) g_otrGenerator->clear();
    GLRenderer::getInstance().clear();
}

} // extern "C"