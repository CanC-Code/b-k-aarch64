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
static std::thread g_thread;

extern "C" {
    void core1_reset(uint8_t* ram);
    void core1_loadOTR(int fd);
    void n_audioStep();
}

static std::vector<uint8_t> g_ram(8 * 1024 * 1024, 0);

void emuLoop() {
    core1_reset(g_ram.data());
    while (g_running.load()) {
        n_audioStep();
        usleep(16000);
    }
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    LOGI("Native Bridge Initialized");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) {
    if (!g_running.load()) {
        g_running.store(true);
        g_thread = std::thread(emuLoop);
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(JNIEnv* env, jclass clazz, jobject resolver, jobject uri) {
    jclass resCls = env->GetObjectClass(resolver);
    jmethodID openDoc = env->GetMethodID(resCls, "openFileDescriptor", "(Landroid/net/Uri;Ljava/lang/String;)Landroid/os/ParcelFileDescriptor;");
    jstring mode = env->NewStringUTF("r");
    jobject pfd = env->CallObjectMethod(resolver, openDoc, uri, mode);

    if (pfd) {
        jclass pfdCls = env->GetObjectClass(pfd);
        jmethodID getFd = env->GetMethodID(pfdCls, "getFd", "()I");
        int fd = env->CallIntMethod(pfd, getFd);
        core1_loadOTR(fd);
    }
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv*, jclass) { g_running.store(false); }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv*, jclass) { /* Not implemented */ }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if(g_thread.joinable()) g_thread.join();
}

}
