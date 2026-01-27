// Android/app/src/main/cpp/ultra/NativeBridge.cpp

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    // DUPLICATE THE FD TO ENSURE NATIVE OWNERSHIP
    int nativeFd = dup(romFd); 
    if (nativeFd == -1) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to duplicate FD");
        return;
    }

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);

    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        // PASS THE DUPLICATED FD
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              nativeFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }

    // CLOSE THE NATIVE FD AFTER GENERATION IS COMPLETE
    close(nativeFd); 
    env->ReleaseStringUTFChars(outputDir, outDir);
}
