#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

extern "C" {

// Keep nativeInit if it's not defined in wrapper.cpp. 
// If the linker still complains, remove this and use the one in wrapper.cpp.
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    g_mainActivityObj = env->NewGlobalRef(activity);
    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
}

/* REMOVED: Java_com_bkawrapper_NativeBridge_runOtrGeneration 
   [span_5](start_span)Reason: Duplicate symbol; implemented in OtrBridge.cpp[span_5](end_span)
*/

/* REMOVED: Game Loop and Texture Stubs 
   [span_6](start_span)Reason: Duplicate symbols; implemented in wrapper.cpp[span_6](end_span)
*/

} // extern "C"
