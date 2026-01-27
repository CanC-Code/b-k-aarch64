#include <jni.h>
#include <thread>
#include <atomic>
#include <vector>
#include <android/log.h>
#include <unistd.h>
#include <fcntl.h>
#include "ultra/otr_builder.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::atomic<bool> g_running{false};
static std::atomic<bool> g_rom_loaded{false};
static std::thread g_thread;
static jobject g_mainActivityObj = nullptr; // Global ref to call UI updates

extern "C" {
    void core1_reset(uint8_t* ram);
    void core1_loadOTR(int fd);
    void n_audioStep();
}

static std::vector<uint8_t> g_ram(8 * 1024 * 1024, 0);

void emuLoop() {
    while(!g_rom_loaded.load() && g_running.load()) {
        usleep(100000); 
    }

    if (g_running.load()) {
        core1_reset(g_ram.data());
        LOGI("Emulator Loop Active");
        while (g_running.load()) {
            n_audioStep();
            usleep(16000); // ~60fps
        }
    }
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass, jobject activity) {
    // Store a global reference to the MainActivity so we can call UI updates later
    g_mainActivityObj = env->NewGlobalRef(activity);
    LOGI("Native Bridge Ready with Activity Context");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(JNIEnv* env, jclass, jobject resolver, jobject uri) {
    // 1. Get File Descriptor from URI
    jclass resCls = env->GetObjectClass(resolver);
    jmethodID openDoc = env->GetMethodID(resCls, "openFileDescriptor", "(Landroid/net/Uri;Ljava/lang/String;)Landroid/os/ParcelFileDescriptor;");
    jstring mode = env->NewStringUTF("r");
    jobject pfd = env->CallObjectMethod(resolver, openDoc, uri, mode);

    if (pfd) {
        jclass pfdCls = env->GetObjectClass(pfd);
        jmethodID getFd = env->GetMethodID(pfdCls, "getFd", "()I");
        int fd = env->CallIntMethod(pfd, getFd);

        // 2. Read ROM into memory for processing
        off_t size = lseek(fd, 0, SEEK_END);
        lseek(fd, 0, SEEK_SET);
        std::vector<uint8_t> romData(size);
        read(fd, romData.data(), size);

        // 3. Trigger Asset Extraction with UI Feedback
        // This calls the logic in otr_builder.cpp
        extract_assets_to_otr(env, g_mainActivityObj, romData.data(), size);

        // 4. Load the resulting OTR into the core
        core1_loadOTR(fd); 
        g_rom_loaded.store(true);
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    if (!g_running.load()) {
        g_running.store(true);
        g_thread = std::thread(emuLoop);
    }
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass) {
    g_running.store(false);
    if(g_thread.joinable()) g_thread.join();
    if(g_mainActivityObj) {
        env->DeleteGlobalRef(g_mainActivityObj);
        g_mainActivityObj = nullptr;
    }
}

JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv*, jclass) { return 1; }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv*, jclass, jint) {}

}
