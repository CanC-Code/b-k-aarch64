#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>

extern "C" {
    extern void initInterruptTables();
    extern void boot();
    extern void Engine_RunFrame(); 
    extern void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize);
}

extern "C" {

// BRIDGES TO JAVA: com.bkawrapper.NativeBridge
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath, jobject assetManager) {
    const char* cOtrPath = env->GetStringUTFChars(otrPath, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Load the manifest from assets
    AAsset* manifestAsset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (manifestAsset) {
        uint8_t* buf = (uint8_t*)AAsset_getBuffer(manifestAsset);
        uint32_t size = (uint32_t)AAsset_getLength(manifestAsset);
        [span_5](start_span)ResourceMgr_Init(cOtrPath, buf, size);[span_5](end_span)
        AAsset_close(manifestAsset);
    }

    [span_6](start_span)initInterruptTables();[span_6](end_span)
    [span_7](start_span)boot();[span_7](end_span)
    env->ReleaseStringUTFChars(otrPath, cOtrPath);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeMainLoop(JNIEnv* env, jclass clazz) {
    [span_8](start_span)Engine_RunFrame();[span_8](end_span)
}

}
