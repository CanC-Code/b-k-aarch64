#include <jni.h>
#include <vector>
#include <atomic>
#include <thread>
#include <mutex>
#include <unistd.h>
#include <android/log.h>
#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// Global emulator state
// ------------------------------------------------------------
static constexpr size_t RAM_SIZE = 8 * 1024 * 1024;
static std::vector<uint8_t> g_ram(RAM_SIZE);
static std::atomic<bool> g_running{false};
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// Menu
static MenuHandler* g_menu = nullptr;
static JavaVM* g_vm = nullptr;

// Core stubs
extern "C" {
    void core1_reset(uint8_t* ram);
    void n_audioStep();
}

// ------------------------------------------------------------
// Emulation loop
// ------------------------------------------------------------
static void emulation_loop() {
    core1_reset(g_ram.data());

    JNIEnv* env = nullptr;
    if (g_vm->AttachCurrentThread(&env, nullptr) != JNI_OK) {
        LOGI("Failed to attach thread");
        return;
    }

    while (g_running.load()) {
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);

            // Pause if menu visible
            if (g_menu && g_menu->isVisible()) {
                usleep(16 * 1000);
                continue;
            }

            n_audioStep(); // stub
        }
        usleep(16 * 1000);
    }

    g_vm->DetachCurrentThread();
    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI exports
// ------------------------------------------------------------
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game cleaned up");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (!g_menu)
        g_menu = new MenuHandler(g_vm, activity);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv*, jclass) {
    if (g_menu) g_menu->toggleVisibility();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeToggleMenu(JNIEnv*, jclass) {
    if (g_menu) g_menu->toggleVisibility();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativePauseEmulator(JNIEnv*, jclass) {
    // emulator paused by menu visibility
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeResumeEmulator(JNIEnv*, jclass) {
    // emulator resumes when menu hidden
}

// ------------------------------------------------------------
// JNI load
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}

} // extern "C"