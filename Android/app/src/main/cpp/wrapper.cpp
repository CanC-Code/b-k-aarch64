#include <jni.h>
#include <vector>
#include <atomic>
#include <thread>
#include <mutex>
#include <cstdio>
#include <unistd.h>
#include <android/log.h>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// External core symbols
// ------------------------------------------------------------
extern "C" {
    void core1_reset(uint8_t* ram);
    void n_audioStep();
    void NativeBridge_loadRomFromUri();
    void NativeBridge_initTexture();
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
            // Emulation step
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

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    g_running.store(true);
    g_paused.store(false);

    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game cleaned up");
}

// Pause emulator
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativePauseEmulator(JNIEnv*, jclass) {
    g_paused.store(true);
    LOGI("Emulator paused");
}

// Resume emulator
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeResumeEmulator(JNIEnv*, jclass) {
    g_paused.store(false);
    LOGI("Emulator resumed");
}

} // extern "C"

// ------------------------------------------------------------
// JNI load
// ------------------------------------------------------------
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}