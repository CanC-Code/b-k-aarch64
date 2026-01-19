#include <jni.h>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include "OTRGenerator.hpp"

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Store OTR generator and generated OTR globally (single instance for now)
static OTRGenerator* gOTRGen = nullptr;
static std::vector<uint8_t> gGeneratedOTR;
static float gProgress = 0.0f;

// Forward declaration for JNI helper
static void reportProgress(float p) {
    gProgress = p;
}

// ------------------------------
// JNI EXPORTS
// ------------------------------

extern "C" {

// Initialize native generator with AssetManager
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass, jobject assetManager) {
    if (gOTRGen) delete gOTRGen;

    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    gOTRGen = new OTRGenerator(mgr);
    gOTRGen->setProgressCallback(reportProgress);

    LOGI("NativeBridge initialized with AssetManager");
}

// Generate OTR from ROM + YAML asset path
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env,
        jclass,
        jbyteArray romData,
        jstring yamlAssetPath
) {
    if (!gOTRGen) {
        LOGE("OTRGenerator not initialized!");
        return JNI_FALSE;
    }

    // Convert Java byte array to C++ vector
    jsize romSize = env->GetArrayLength(romData);
    std::vector<uint8_t> romBuffer(romSize);
    env->GetByteArrayRegion(romData, 0, romSize, reinterpret_cast<jbyte*>(romBuffer.data()));

    // Convert Java string to C string
    const char* yamlPathC = env->GetStringUTFChars(yamlAssetPath, nullptr);

    LOGI("Generating OTR from ROM (%d bytes) and YAML: %s", romSize, yamlPathC);

    bool success = gOTRGen->generateOTR(romBuffer.data(), romBuffer.size(), yamlPathC);
    gGeneratedOTR = gOTRGen->getOTR();

    env->ReleaseStringUTFChars(yamlAssetPath, yamlPathC);

    LOGI("OTR generation %s, size: %zu", success ? "succeeded" : "failed", gGeneratedOTR.size());

    return success ? JNI_TRUE : JNI_FALSE;
}

// Return progress [0.0 – 1.0]
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv*, jclass) {
    return gProgress;
}

// Load generated OTR into renderer
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeLoadOTR(JNIEnv*, jclass) {
    if (gGeneratedOTR.empty()) {
        LOGE("No OTR generated to load!");
        return;
    }

    // TODO: pass gGeneratedOTR.data() and gGeneratedOTR.size() to your renderer
    // This depends on how your OpenGL renderer or emulator reads the OTR
    LOGI("OTR ready to load into renderer, size: %zu bytes", gGeneratedOTR.size());

    // Example:
    // Renderer::get()->loadOTR(gGeneratedOTR.data(), gGeneratedOTR.size());
}

} // extern "C"