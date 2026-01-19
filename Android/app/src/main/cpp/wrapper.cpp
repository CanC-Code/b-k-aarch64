#include <jni.h>
#include <cstdint>
#include <thread>
#include <atomic>
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <mutex>
#include <cstdio>

#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// External core symbols
// ------------------------------------------------------------
extern "C" {
    void core1_reset(uint8_t* ram);
    void core1_stepCPU(uint8_t* ram);
    void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int w, int h);

    void n_audioInit();
    void n_audioStep();

    void core1_loadOTR(uint8_t* romData, size_t romSize);
}

// ------------------------------------------------------------
// Global emulator state
// ------------------------------------------------------------
static constexpr size_t RAM_SIZE = 8 * 1024 * 1024;

static std::vector<uint8_t> g_ram(RAM_SIZE);
static std::vector<uint32_t> g_framebuffer;
static int g_fbWidth  = 320;
static int g_fbHeight = 240;

static std::atomic<bool> g_running{false};
static std::atomic<bool> g_paused{false};
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// In-memory OTR
static std::vector<uint8_t> g_OTR;

// ------------------------------------------------------------
// Menu system (native-owned)
// ------------------------------------------------------------
static JavaVM* g_vm = nullptr;
static MenuHandler* g_menu = nullptr;
static std::atomic<bool> g_menuVisible{false};

// ------------------------------------------------------------
// Emulation loop
// ------------------------------------------------------------
static void emulation_loop() {
    LOGI("Emulation thread started");

    n_audioInit();
    core1_reset(g_ram.data());

    while (g_running.load()) {

        if (g_paused.load()) {
            usleep(16 * 1000);
            continue;
        }

        {
            std::lock_guard<std::mutex> lock(g_stateMutex);

            core1_stepCPU(g_ram.data());

            if (!g_framebuffer.empty()) {
                core2_stepFrame(
                    g_ram.data(),
                    g_framebuffer.data(),
                    g_fbWidth,
                    g_fbHeight
                );
            }

            n_audioStep();
        }

        usleep(16 * 1000); // ~60Hz
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI API
// ------------------------------------------------------------
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(
        JNIEnv* env, jclass, jobject /* resolver */, jobject uri) {
    // stub: user will implement ContentResolver reading
    // For now assume g_ram is preloaded externally
    LOGI("loadRomFromUri stub called");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(
        JNIEnv*, jclass) {
    LOGI("initTexture called");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(
        JNIEnv*, jclass) {

    if (g_running.load()) {
        LOGI("Game loop already running");
        return;
    }

    g_running.store(true);
    g_paused.store(false);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stopGameLoop(
        JNIEnv*, jclass) {

    if (!g_running.load()) return;

    g_running.store(false);

    if (g_emulationThread.joinable()) {
        g_emulationThread.join();
    }

    LOGI("Game loop stopped");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(
        JNIEnv*, jclass) {

    Java_com_bkawrapper_NativeBridge_stopGameLoop(nullptr, nullptr);

    std::lock_guard<std::mutex> lock(g_stateMutex);
    g_framebuffer.clear();

    LOGI("Game cleaned up");
}

JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv*, jclass) {
    // stub: return dummy progress
    return 1.0f;
}

// ------------------------------------------------------------
// Menu JNI hooks
// ------------------------------------------------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(
        JNIEnv* env, jclass, jobject activity) {

    if (g_menu) return;

    g_menu = new MenuHandler(g_vm, activity);
    LOGI("Native menu initialized");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(
        JNIEnv*, jclass) {

    if (!g_menu) return;

    if (!g_menuVisible.load()) {
        g_menuVisible.store(true);
        g_paused.store(true);
        g_menu->showMenu();
        LOGI("Menu shown, emulator paused");
    } else {
        g_menuVisible.store(false);
        g_paused.store(false);
        g_menu->hideMenu();
        LOGI("Menu hidden, emulator resumed");
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativePauseEmulator(JNIEnv*, jclass) {
    g_paused.store(true);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeResumeEmulator(JNIEnv*, jclass) {
    g_paused.store(false);
}

} // extern "C"

// ------------------------------------------------------------
// JNI load
// ------------------------------------------------------------
JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}