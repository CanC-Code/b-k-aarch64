// File: Android/app/src/main/cpp/wrapper.cpp

#include <jni.h>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <android/log.h>
#include <unistd.h>

#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// Emulator stub symbols (until real core is wired)
// ------------------------------------------------------------
extern "C" void core1_reset(void*) {}
extern "C" void n_audioStep() {}

// ------------------------------------------------------------
// Global emulator state
// ------------------------------------------------------------
static constexpr size_t RAM_SIZE = 8 * 1024 * 1024;
static std::vector<uint8_t> g_ram(RAM_SIZE);

static std::atomic<bool> g_running{false};
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// ------------------------------------------------------------
// Menu (owned by menu.cpp)
// ------------------------------------------------------------
extern MenuHandler* g_menu;
static JavaVM* g_vm = nullptr;

// ------------------------------------------------------------
// Emulation loop (stub)
// ------------------------------------------------------------
static void emulation_loop() {
    core1_reset(g_ram.data());

    while (g_running.load()) {
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            n_audioStep();
        }

        usleep(16 * 1000); // ~60 FPS stub
    }
}

// ------------------------------------------------------------
// JNI functions
// ------------------------------------------------------------
extern "C" {

// ----------------------
// Game loop control
// ----------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    if (g_running.load()) return;

    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable())
        g_emulationThread.join();

    LOGI("Game loop paused");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv*, jclass) {
    if (g_running.load()) return;

    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop resumed");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable())
        g_emulationThread.join();

    LOGI("Game cleaned up");
}

// ----------------------
// Menu initialization
// ----------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (!g_menu) {
        JavaVM* vm = nullptr;
        env->GetJavaVM(&vm);
        g_menu = new MenuHandler(vm, activity);
        LOGI("Menu initialized from NativeBridge");
    }
}

// ----------------------
// Back button → toggle menu
// ----------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv*, jclass) {
    if (g_menu)
        g_menu->toggleVisibility();
}

// ----------------------
// JNI_OnLoad
// ----------------------
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad bk_wrapper");
    return JNI_VERSION_1_6;
}

} // extern "C"