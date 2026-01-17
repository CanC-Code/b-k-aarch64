#include <jni.h>
#include <cstdint>
#include <thread>
#include <atomic>
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <mutex>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// External core symbols (real or stubbed elsewhere)
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
// Global state
// ------------------------------------------------------------
static constexpr size_t RAM_SIZE = 8 * 1024 * 1024;

static std::vector<uint8_t> g_ram(RAM_SIZE);
static std::vector<uint32_t> g_framebuffer;
static int g_fbWidth  = 320;
static int g_fbHeight = 240;

static std::atomic<bool> g_running{false};
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// ------------------------------------------------------------
// Emulation loop
// ------------------------------------------------------------
static void emulation_loop() {
    LOGI("Emulation thread started");

    n_audioInit();
    core1_reset(g_ram.data());

    while (g_running.load()) {
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

        // ~60Hz pacing
        usleep(16 * 1000);
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI API (matches NativeBridge.java)
// ------------------------------------------------------------
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(
        JNIEnv* env, jclass, jbyteArray romData) {

    if (!romData) return;

    jsize len = env->GetArrayLength(romData);
    if (len > RAM_SIZE) len = RAM_SIZE;

    env->GetByteArrayRegion(
        romData, 0, len,
        reinterpret_cast<jbyte*>(g_ram.data())
    );

    LOGI("ROM loaded: %d bytes", len);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv*, jclass) {

    core1_loadOTR(g_ram.data(), g_ram.size());
    LOGI("OTR processing complete");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initGame(
        JNIEnv*, jclass, jobject /* surface */) {

    std::lock_guard<std::mutex> lock(g_stateMutex);

    g_framebuffer.resize(g_fbWidth * g_fbHeight);
    std::fill(g_framebuffer.begin(), g_framebuffer.end(), 0);

    core1_reset(g_ram.data());
    LOGI("Game initialized");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(
        JNIEnv*, jclass) {

    if (g_running.load()) {
        LOGI("Game loop already running");
        return;
    }

    g_running.store(true);
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

} // extern "C"

// ------------------------------------------------------------
// JNI load
// ------------------------------------------------------------
JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM*, void*) {
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}