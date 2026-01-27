#include <jni.h>
#include <thread>
#include <atomic>
#include <vector>
#include <android/log.h>
#include <unistd.h>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::atomic<bool> g_running{false};
static std::atomic<bool> g_rom_loaded{false};
static std::thread g_thread;
static jobject g_activityObj = nullptr;

// External functions implemented in your emulator core or OTR builder
extern "C" {
    void core1_reset(uint8_t* ram);
    void n_audioStep();
    void core1_loadOTR(int fd); 
}

static std::vector<uint8_t> g_ram(8 * 1024 * 1024, 0);

void emuLoop() {
    // Wait until the OTR generation in NativeBridge.cpp signals it is done
    while(!g_rom_loaded.load() && g_running.load()) {
        usleep(100000); 
    }

    if (g_running.load()) {
        core1_reset(g_ram.data());
        LOGI("Emulator Loop Active");
        while (g_running.load()) {
            n_audioStep();
            usleep(16000); // ~60fps target
        }
    }
}

extern "C" {

// FIX: This is the ONLY definition of nativeInit in the project
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    if (g_activityObj != nullptr) {
        env->DeleteGlobalRef(g_activityObj);
    }
    g_activityObj = env->NewGlobalRef(activity);
    LOGI("Native Bridge Initialized with Activity Ref");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) {
    if (!g_running.load()) {
        g_running.store(true);
        // We assume the ROM is ready once this is called from Java
        g_rom_loaded.store(true); 
        g_thread = std::thread(emuLoop);
    }
}

JNIEXPORT void JNICALL 
Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) {
    // Implement pause logic if needed
}

JNIEXPORT void JNICALL 
Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) {
    // Implement resume logic if needed
}

JNIEXPORT void JNICALL 
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) {
    g_running.store(false);
    if(g_thread.joinable()) g_thread.join();
    if(g_activityObj) {
        env->DeleteGlobalRef(g_activityObj);
        g_activityObj = nullptr;
    }
    LOGI("Native Bridge Cleaned Up");
}

// Graphics Stubs (implemented here to satisfy NativeBridge.java)
JNIEXPORT jint JNICALL 
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) { 
    return 1; 
}

JNIEXPORT void JNICALL 
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) {
    // Texture update logic
}

} // extern "C"
