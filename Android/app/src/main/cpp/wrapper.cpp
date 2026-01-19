// File: Android/app/src/main/cpp/wrapper.cpp

#include <jni.h>
#include <atomic>
#include <mutex>

static JavaVM* g_vm = nullptr;
static jobject g_activity = nullptr;
static jobject g_menuOverlay = nullptr;

static std::atomic<bool> g_menuVisible{false};
static std::atomic<bool> g_emulatorPaused{false};

static std::mutex g_menuMutex;

static JNIEnv* getEnv(bool& didAttach) {
    JNIEnv* env = nullptr;
    didAttach = false;

    if (g_vm->GetEnv((void**)&env, JNI_VERSION_1_6) != JNI_OK) {
        g_vm->AttachCurrentThread(&env, nullptr);
        didAttach = true;
    }
    return env;
}

static void setMenuVisibility(bool visible) {
    std::lock_guard<std::mutex> lock(g_menuMutex);

    if (!g_menuOverlay) return;

    bool didAttach = false;
    JNIEnv* env = getEnv(didAttach);

    jclass viewCls = env->GetObjectClass(g_menuOverlay);
    jmethodID setVisibility =
        env->GetMethodID(viewCls, "setVisibility", "(I)V");

    env->CallVoidMethod(
        g_menuOverlay,
        setVisibility,
        visible ? 0 /* View.VISIBLE */ : 8 /* View.GONE */
    );

    if (didAttach) {
        g_vm->DetachCurrentThread();
    }
}

extern "C" {

// Called from Menu.java constructor
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeInitMenu(
        JNIEnv* env,
        jclass,
        jobject activity,
        jobject menuOverlay) {

    if (!g_activity) {
        g_activity = env->NewGlobalRef(activity);
    }

    if (!g_menuOverlay) {
        g_menuOverlay = env->NewGlobalRef(menuOverlay);
    }

    g_menuVisible = false;
    g_emulatorPaused = false;

    setMenuVisibility(false);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeToggleMenu(
        JNIEnv*,
        jclass) {

    bool newState = !g_menuVisible.load();
    g_menuVisible = newState;

    setMenuVisibility(newState);

    // Menu open == emulator paused
    g_emulatorPaused = newState;
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativePauseEmulator(
        JNIEnv*,
        jclass) {
    g_emulatorPaused = true;
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeResumeEmulator(
        JNIEnv*,
        jclass) {
    g_emulatorPaused = false;
}

// Called from your emulation loop
bool isEmulatorPaused() {
    return g_emulatorPaused.load();
}

} // extern "C"

jint JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    return JNI_VERSION_1_6;
}