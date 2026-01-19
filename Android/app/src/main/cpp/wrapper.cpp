// File: Android/app/src/main/cpp/wrapper.cpp
// Purpose: JNI wrapper to expose OTR generation to Java/Kotlin

#include "otr_generator.hpp"
#include "NativeBridge.hpp"
#include <android/asset_manager_jni.h>
#include <jni.h>
#include <vector>
#include <cstdint>

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeWrapper_generateOTR(JNIEnv* env, jobject thiz, jobject assetManager) {
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    OTRGenerator generator;

    // Load assets via readAsset
    auto palData = readAsset(mgr, "otr_yaml/decompressed.pal.yaml");
    auto usData  = readAsset(mgr, "otr_yaml/decompressed.us.v10.yaml");

    generator.generateOTR(palData, usData);
}

}