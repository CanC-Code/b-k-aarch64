#include <jni.h>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <unistd.h>
#include <android/log.h>

#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// External core symbols (real or stubbed elsewhere)
// ------------------------------------------------------------
extern "C" {
    void core1_reset(uint8_t* ram);
    void n_audioStep();
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
    core1_reset(g_ram.data());

    while (g_running.load()) {
        if (g_paused.load()) {
            usleep(16 * 1000);
            continue;
        }

        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            // TODO: step CPU, update framebuffer, etc.
            n_audioStep();
        }

        usleep(16 * 1000); // ~60Hz
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI Exports
// ------------------------------------------------------------
extern "C" {

// ---------------- ROM / OTR ----------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(
        JNIEnv*, jclass, jobject resolver, jobject uri) {
    LOGI("ROM load requested (stub)");
}

JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv*, jclass) {
    if (g_OTR.empty()) return 1.0f;
    return 1.0f; // stub, assume done
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(
        JNIEnv* env, jclass, jstring path) {
    const char* cpath = env->GetStringUTFChars(path, nullptr);
    FILE* f = fopen(cpath, "wb");
    if (f) {
        fwrite(g_OTR.data(), 1, g_OTR.size(), f);
        fclose(f);
        LOGI("Saved BK.OTR: %zu bytes", g_OTR.size());
    }
    env->ReleaseStringUTFChars(path, cpath);
}

// ---------------- Game loop ----------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(
        JNIEnv*, jclass) {
    g_running.store(true);
    g_paused.store(false);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(
        JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game cleaned up");
}

// ---------------- Menu ----------------
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

// ---------------- GL Renderer ----------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(
        JNIEnv*, jclass) {
    LOGI("initTexture called (stub)");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(
        JNIEnv*, jclass, jint textureId) {
    LOGI("updateTexture called: %d", textureId);
}

// ---------------- JNI Load ----------------
JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}

} // extern "C"