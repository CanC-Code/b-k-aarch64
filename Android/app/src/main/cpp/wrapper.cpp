#include <jni.h>
#include <thread>
#include <atomic>
#include <vector>
#include <android/log.h>
#include <unistd.h>
#include <fcntl.h>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::atomic<bool> g_running{false};
static std::atomic<bool> g_rom_loaded{false};
static std::thread g_thread;
static jobject g_activityObj = nullptr; // For callbacks

extern "C" {
    void core1_reset(uint8_t* ram);
    void core1_loadOTR(int fd);
    void n_audioStep();
    // Assuming this is your extraction function in your builder code
    void run_otr_extraction(JNIEnv* env, jobject activity, int romFd);
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
            usleep(16000);
        }
    }
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass, jobject activity) {
    g_activityObj = env->NewGlobalRef(activity);
    LOGI("Native Bridge Initialized with Activity Ref");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(JNIEnv* env, jclass, jobject resolver, jobject uri) {
    jclass resCls = env->GetObjectClass(resolver);
    jmethodID openDoc = env->GetMethodID(resCls, "openFileDescriptor", "(Landroid/net/Uri;Ljava/lang/String;)Landroid/os/ParcelFileDescriptor;");
    jstring mode = env->NewStringUTF("r");
    jobject pfd = env->CallObjectMethod(resolver, openDoc, uri, mode);

    if (pfd) {
        jclass pfdCls = env->GetObjectClass(pfd);
        jmethodID getFd = env->GetMethodID(pfdCls, "getFd", "()I");
        int fd = env->CallIntMethod(pfd, getFd);

        // 1. Run the actual asset extraction logic
        // Ensure this function uses the activity reference to call updateOtrProgress
        run_otr_extraction(env, g_activityObj, fd);

        // 2. Load the final OTR into the emulator core
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
    if(g_activityObj) {
        env->DeleteGlobalRef(g_activityObj);
        g_activityObj = nullptr;
    }
}

JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv*, jclass) { return 1; }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv*, jclass, jint) {}

}
