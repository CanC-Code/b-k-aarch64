#include "NativeBridge.hpp"
#include "otr_generator.hpp"
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <fstream>
#include <mutex>

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static std::vector<uint8_t> sOTRMemory;
static std::mutex sOTRMutex;
static OTRGenerator sOTRGenerator;

// Progress callback
static float sProgress = 0.0f;

extern "C" {

// Initialize native system (if needed)
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject assetManager) {
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) {
        LOGE("Failed to get AAssetManager");
        return;
    }
    // Nothing else needed at init for now
}

// Generate OTR: ROM bytes + YAML from assets
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env, jclass clazz,
        jbyteArray romData,
        jstring yamlAssetPath,
        jstring outputPath
) {
    if (!romData || !yamlAssetPath || !outputPath) return JNI_FALSE;

    jsize romSize = env->GetArrayLength(romData);
    std::vector<uint8_t> romBuffer(romSize);
    env->GetByteArrayRegion(romData, 0, romSize, reinterpret_cast<jbyte*>(romBuffer.data()));

    const char* yamlPathC = env->GetStringUTFChars(yamlAssetPath, nullptr);
    const char* outputPathC = env->GetStringUTFChars(outputPath, nullptr);

    // Load YAML from APK assets
    AAssetManager* mgr = AAssetManager_fromJava(env, env->CallObjectMethod(clazz, env->GetMethodID(clazz, "getAssetManager", "()Landroid/content/res/AssetManager;")));
    if (!mgr) {
        LOGE("Invalid AssetManager");
        env->ReleaseStringUTFChars(yamlAssetPath, yamlPathC);
        env->ReleaseStringUTFChars(outputPath, outputPathC);
        return JNI_FALSE;
    }

    std::vector<uint8_t> yamlBuffer = OTRGenerator::loadYAMLAsset(mgr, yamlPathC);
    if (yamlBuffer.empty()) {
        LOGE("Failed to load YAML asset");
        env->ReleaseStringUTFChars(yamlAssetPath, yamlPathC);
        env->ReleaseStringUTFChars(outputPath, outputPathC);
        return JNI_FALSE;
    }

    sOTRGenerator.setProgressCallback([](float p) {
        std::lock_guard<std::mutex> lock(sOTRMutex);
        sProgress = p;
    });

    std::vector<uint8_t> localOTR;
    bool success = sOTRGenerator.generateOTR(
            romBuffer.data(), romBuffer.size(),
            reinterpret_cast<const char*>(yamlBuffer.data()), yamlBuffer.size(),
            localOTR
    );

    if (!success) {
        env->ReleaseStringUTFChars(yamlAssetPath, yamlPathC);
        env->ReleaseStringUTFChars(outputPath, outputPathC);
        LOGE("OTR generation failed");
        return JNI_FALSE;
    }

    {
        std::lock_guard<std::mutex> lock(sOTRMutex);
        sOTRMemory = std::move(localOTR);
    }

    // Save generated OTR to persistent storage
    std::ofstream ofs(outputPathC, std::ios::binary);
    if (!ofs.is_open()) {
        LOGE("Failed to open output path: %s", outputPathC);
    } else {
        ofs.write(reinterpret_cast<const char*>(sOTRMemory.data()), sOTRMemory.size());
        ofs.close();
        LOGI("OTR saved to %s (%zu bytes)", outputPathC, sOTRMemory.size());
    }

    env->ReleaseStringUTFChars(yamlAssetPath, yamlPathC);
    env->ReleaseStringUTFChars(outputPath, outputPathC);
    return success ? JNI_TRUE : JNI_FALSE;
}

// Return current progress [0.0f – 1.0f]
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> lock(sOTRMutex);
    return sProgress;
}

// Provide pointer to in-memory OTR for rendering
JNIEXPORT jlong JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetOTRPointer(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> lock(sOTRMutex);
    return reinterpret_cast<jlong>(sOTRMemory.data());
}

// Get size of in-memory OTR
JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetOTRSize(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> lock(sOTRMutex);
    return static_cast<jint>(sOTRMemory.size());
}

} // extern "C"