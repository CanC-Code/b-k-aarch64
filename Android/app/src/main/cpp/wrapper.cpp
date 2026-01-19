#include <jni.h>
#include <atomic>
#include <android/log.h>

#define LOG_TAG "BK_NATIVE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::atomic<bool> gPaused{false};
static std::atomic<bool> gMenuVisible{false};

/* =========================================================
   INTERNAL EMULATOR CONTROL (replace with real calls)
   ========================================================= */

static void emulator_pause() {
    LOGI("Emulator paused");
    gPaused.store(true);
}

static void emulator_resume() {
    LOGI("Emulator resumed");
    gPaused.store(false);
}

/* =========================================================
   JNI MENU / CONTROL BRIDGE
   ========================================================= */

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(
        JNIEnv* env,
        jclass,
        jobject /* activity */) {
    LOGI("Native menu initialized");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(
        JNIEnv*,
        jclass) {

    bool visible = gMenuVisible.load();
    gMenuVisible.store(!visible);

    if (!visible) {
        emulator_pause();
        LOGI("Menu shown");
    } else {
        emulator_resume();
        LOGI("Menu hidden");
    }
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativePauseEmulator(
        JNIEnv*,
        jclass) {
    emulator_pause();
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeResumeEmulator(
        JNIEnv*,
        jclass) {
    emulator_resume();
}

/* =========================================================
   OPTIONAL QUERY (if Java ever asks)
   ========================================================= */

extern "C"
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeIsPaused(
        JNIEnv*,
        jclass) {
    return gPaused.load() ? JNI_TRUE : JNI_FALSE;
}