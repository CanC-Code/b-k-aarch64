#include <sys/resource.h>
#include <sys/prctl.h>
#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <android/native_window.h>
#include <android/native_window_jni.h>
#include <string>
#include <cstdio>
#include <pthread.h>
#include <unistd.h>
#include <stdint.h>
#include <cstring>
#include <GLES2/gl2.h>
#include <EGL/egl.h>
#include <malloc.h>

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static JavaVM* g_jvm = nullptr;
static std::string g_otrPath;

// Exported globally for internal engine resource managers to access pre-embedded assets natively
AAssetManager* g_assetManager = nullptr;

static int g_surfaceWidth  = 320;
static int g_surfaceHeight = 240;
static bool g_engineThreadActive = false;

// FIXED: EGL is managed entirely by GLSurfaceView now. We no longer create our
// own EGL context/surface, which was conflicting with GLSurfaceView's internal
// context and causing "already connected" errors. These variables are kept for
// compatibility with DestroyEGL_Locked during surface teardown.
static EGLDisplay g_eglDisplay = EGL_NO_DISPLAY;
static EGLSurface g_eglSurface = EGL_NO_SURFACE;
static EGLContext g_eglContext = EGL_NO_CONTEXT;
static bool g_eglInitialized = false;

struct BKA_ControllerPad {
    uint16_t button;
    int8_t   stick_x;
    int8_t   stick_y;
    uint8_t  errno_val;
};

static BKA_ControllerPad g_inputMirror  = {0, 0, 0, 0};
static pthread_mutex_t   g_inputMutex   = PTHREAD_MUTEX_INITIALIZER;

static volatile bool   g_vblankRequested = false;
static pthread_cond_t  g_vblankCond      = PTHREAD_COND_INITIALIZER;
static pthread_mutex_t g_vblankMutex     = PTHREAD_MUTEX_INITIALIZER;

// Airtight Bridge-Level Resource Synchronization Gate
static pthread_mutex_t g_bridgeGateMutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  g_bridgeGateCond  = PTHREAD_COND_INITIALIZER;
static bool            g_bridgeResourcesReady = false;

// Native Window Synchronization State
static ANativeWindow*  g_nativeWindow = nullptr;
static pthread_mutex_t g_windowMutex  = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  g_windowCond   = PTHREAD_COND_INITIALIZER;

// FIXED: InitializeEGL_Locked no longer creates its own EGL context.
// GLSurfaceView manages the EGL context lifecycle. The native code just
// needs to signal vblank and output the frame texture. We keep this
// function as a no-op for compatibility with existing call sites.
static bool InitializeEGL_Locked() {
    // EGL is managed by GLSurfaceView. The active context is already
    // bound when onDrawFrame → updateTexture is called.
    g_eglInitialized = true;
    return true;
}

static void DestroyEGL_Locked() {
    // GLSurfaceView handles EGL teardown. Just reset our state.
    g_eglDisplay = EGL_NO_DISPLAY;
    g_eglSurface = EGL_NO_SURFACE;
    g_eglContext = EGL_NO_CONTEXT;
    g_eglInitialized = false;
    LOGI("NativeBridge: EGL state reset (surface destroyed).");
}

extern "C" {
    extern uint8_t* gN64_RDRAM;
    extern s32 gFramebufferWidth;
    extern s32 gFramebufferHeight;
    extern uint32_t* gN64_Reg_Base;

    void InitN64Registers(const char* assetDir);
    void HardwareRegs_Shutdown(void);

    void BKA_StartEngine(void);
    void BKA_DropEngineLock(void);
    void BKA_ClaimEngineLock(void);

    void ResourceMgr_Init(const char* assetDir);
    void BKA_SignalResourcesReady(void);

    extern BKA_ControllerPad gN64_ControllerData[4];
    void N64_TriggerVirtualVBlankInterrupt(void);
    void VideoPlugin_OutputFrameTexture(uint32_t hostTextureId);

    // Framebuffer copy helpers. The game renders into gFramebuffers
    // (a host-side array in lowlevel_bridge.cpp), but the video plugin
    // reads from gN64_RDRAM + g_active_fb_offset. We need to copy the
    // active framebuffer to RDRAM each frame.
    extern uint16_t gFramebuffers[2][292 * 216];
    extern uint32_t g_active_fb_offset;
    extern int getActiveFramebuffer(void);

    void BKA_FrameSyncHook(void) {
    static int hookCount = 0; if (++hookCount <= 3 || hookCount % 60 == 0) LOGI("BKA-FrameSync: frame %d", hookCount);
        extern int g_diag_null_task; if (g_diag_null_task) { LOGI("BKA-RDP: NULL task_data detected!"); g_diag_null_task = 0; }
        extern int g_diag_mesh_count; extern void* g_diag_mesh_ptr; if (g_diag_mesh_count) { LOGI("BKA-MESH: count=%d ptr=%p", g_diag_mesh_count, g_diag_mesh_ptr); g_diag_mesh_count = 0; }
        extern int g_diag_thread5_loop; static int _last_t5loop = 0; if (g_diag_thread5_loop != _last_t5loop) { LOGI("BKA-RDP: Thread5 loop count=%d", g_diag_thread5_loop); _last_t5loop = g_diag_thread5_loop; }
        pthread_mutex_lock(&g_vblankMutex);
        g_vblankRequested = true;

        BKA_DropEngineLock();


        // 16ms timeout prevents ANR if GL thread is blocked
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        ts.tv_nsec += 16666667;
        if (ts.tv_nsec >= 1000000000) { ts.tv_sec++; ts.tv_nsec -= 1000000000; }
        int ret = pthread_cond_timedwait(&g_vblankCond, &g_vblankMutex, &ts);
        if (ret == ETIMEDOUT) {
            g_vblankRequested = false;
            pthread_mutex_unlock(&g_vblankMutex);
            N64_TriggerVirtualVBlankInterrupt();
            pthread_mutex_lock(&g_vblankMutex);
        }
        while (g_vblankRequested) {
            pthread_cond_wait(&g_vblankCond, &g_vblankMutex);
        }

        pthread_mutex_unlock(&g_vblankMutex);

        pthread_mutex_lock(&g_windowMutex);
        while (g_nativeWindow == nullptr) {
            pthread_cond_wait(&g_windowCond, &g_windowMutex);
        }
        pthread_mutex_unlock(&g_windowMutex);

        BKA_ClaimEngineLock();

        BKA_ClaimEngineLock();
    }
}

#ifndef M_MTE
#define M_MTE 7
#endif

#ifndef M_MTE
#define M_MTE 7
#endif
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    mallopt(M_MTE, 0);
    struct rlimit rl = {16 * 1024 * 1024, 16 * 1024 * 1024};
    setrlimit(RLIMIT_STACK, &rl);
    g_jvm = vm;
    LOGI("NativeBridge: JNI Link established securely.");
    return JNI_VERSION_1_6;
}

void* game_thread_fn(void* arg) {
    struct rlimit rl = {16 * 1024 * 1024, 16 * 1024 * 1024};
    setrlimit(RLIMIT_STACK, &rl);
    LOGI("NativeBridge: Game thread execution loop initialized.");
    JNIEnv* env    = nullptr;
    bool  attached = false;

    if (g_jvm != nullptr) {
        if (g_jvm->AttachCurrentThread(&env, nullptr) == JNI_OK) {
            attached = true;
            LOGI("NativeBridge: Game thread securely attached to JVM environment.");
        } else {
            LOGE("NativeBridge: WARNING - Failed to attach game thread context to JVM.");
        }
    }

    // Heavy initialization moved off the UI thread onto the background game worker thread
    LOGI("NativeBridge: Executing ResourceMgr_Init sequence components on background thread...");
    ResourceMgr_Init(g_otrPath.c_str());
    LOGI("NativeBridge: ResourceMgr structural mapping complete.");

    LOGI("NativeBridge: Initializing N64 virtual architecture registers...");
    InitN64Registers(g_otrPath.c_str());

    // Signal safe unlocking states to allow render thread calls to proceed
    LOGI("NativeBridge: Synchronizing resource gate states to release execution threads...");
    pthread_mutex_lock(&g_bridgeGateMutex);
    g_bridgeResourcesReady = true;
    pthread_cond_broadcast(&g_bridgeGateCond);
    pthread_mutex_unlock(&g_bridgeGateMutex);

    BKA_SignalResourcesReady();

    LOGI("NativeBridge: Invoking BKA_StartEngine runtime entry point.");
    BKA_StartEngine();

    LOGI("NativeBridge: Bootloader finalized execution. Engine runtime loop active.");

    while (true) {
        sleep(1000);
    }

    HardwareRegs_Shutdown();

    if (attached && g_jvm != nullptr) {
        g_jvm->DetachCurrentThread();
    }

    g_engineThreadActive = false;
    return nullptr;
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject context) {
    if (g_jvm == nullptr) {
        env->GetJavaVM(&g_jvm);
        LOGI("NativeBridge: nativeInit configured JavaVM context reference.");
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz,
                                                 jstring otrPathStr,
                                                 jobject assetManagerObj) {
    LOGI("NativeBridge: nativeGameBoot sequence triggered.");

    if (!otrPathStr) {
        LOGE("NativeBridge: FATAL ERROR - Target configuration path parameter received as NULL.");
        return;
    }

    if (assetManagerObj != nullptr) {
        g_assetManager = AAssetManager_fromJava(env, assetManagerObj);
        LOGI("NativeBridge: Bound AAssetManager to handle directly pre-embedded configuration files.");
    } else {
        LOGE("NativeBridge: WARNING - AssetManager object is null. Pre-embedded assets may fail to deploy.");
    }

    const char* otrPath = env->GetStringUTFChars(otrPathStr, nullptr);
    if (!otrPath) {
        LOGE("NativeBridge: FATAL ERROR - JNI string layout conversion sequence failed.");
        return;
    }
    g_otrPath = otrPath;
    env->ReleaseStringUTFChars(otrPathStr, otrPath);

    LOGI("NativeBridge: Base tracking path resolved cleanly to: %s", g_otrPath.c_str());

    // Prevent re-initialization if thread is already running (e.g., Activity recreation)
    if (!g_engineThreadActive) {
        pthread_mutex_lock(&g_bridgeGateMutex);
        g_bridgeResourcesReady = false;
        pthread_mutex_unlock(&g_bridgeGateMutex);

        pthread_t gameThread;
        LOGI("NativeBridge: Allocating background worker thread contexts...");
        pthread_attr_t attr;
        pthread_attr_init(&attr);
        pthread_attr_setstacksize(&attr, 16 * 1024 * 1024); // 4MB stack
        if (pthread_create(&gameThread, &attr, game_thread_fn, nullptr) == 0) {
            pthread_detach(gameThread);
            g_engineThreadActive = true;
            LOGI("NativeBridge: Engine thread spawned and bound to waiting sequence state.");
        } else {
            LOGE("NativeBridge: FATAL ERROR - Engine execution context thread creation failed.");
            return;
        }
    } else {
        LOGI("NativeBridge: Engine thread is already active. Bypassing redundant creation.");
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_setSurface(JNIEnv* env, jclass clazz, jobject surface) {
    pthread_mutex_lock(&g_windowMutex);

    if (surface == nullptr) {
        // surfaceDestroyed sequence
        DestroyEGL_Locked();

        if (g_nativeWindow != nullptr) {
            ANativeWindow_release(g_nativeWindow);
            g_nativeWindow = nullptr;
            LOGI("NativeBridge: Surface destroyed. ANativeWindow safely released.");
        }

        // Unblock the engine thread if it is waiting for a VBlank that will never arrive 
        // now that the rendering surface is torn down.
        pthread_mutex_lock(&g_vblankMutex);
        g_vblankRequested = false;
        pthread_cond_broadcast(&g_vblankCond);
        pthread_mutex_unlock(&g_vblankMutex);

    } else {
        // surfaceCreated sequence
        if (g_nativeWindow != nullptr) {
            DestroyEGL_Locked();
            ANativeWindow_release(g_nativeWindow);
        }
        g_nativeWindow = ANativeWindow_fromSurface(env, surface);
        LOGI("NativeBridge: ANativeWindow successfully bound to native engine context.");

        // Wake up the background engine thread if it was sleeping while paused
        pthread_cond_broadcast(&g_windowCond);
    }

    pthread_mutex_unlock(&g_windowMutex);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_surfaceReady(JNIEnv* env, jclass clazz, jint w, jint h) {
    g_surfaceWidth  = w;
    g_surfaceHeight = h;
    LOGI("NativeBridge: Host viewport surface layout geometry set to: %dx%d", w, h);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint textureId) {
    if (gN64_RDRAM == nullptr || gN64_Reg_Base == nullptr) return;

    // Fast-path bypass: return immediately if engine resources are still initializing
    // Prevents GL thread stall while game_thread_fn is unpacking ROM/YAML assets
    pthread_mutex_lock(&g_bridgeGateMutex);
    bool ready = g_bridgeResourcesReady;
    pthread_mutex_unlock(&g_bridgeGateMutex);

    if (!ready) {
        return;
    }

    // FIXED: GLSurfaceView manages the EGL context. The active GL context is
    // already bound when onDrawFrame calls updateTexture. We just set the
    // viewport and proceed — no need to create a second EGL surface (which
    // was failing with "already connected").
    glViewport(0, 0, g_surfaceWidth, g_surfaceHeight);

    BKA_ClaimEngineLock();

    // ===================================================================
    // FRAMEBUFFER SYNC: Copy the game's host-side framebuffer to RDRAM.
    //
    // The game renders into gFramebuffers (host-side array in
    // lowlevel_bridge.cpp), but VideoPlugin_OutputFrameTexture reads
    // from gN64_RDRAM + g_active_fb_offset. On real N64 hardware,
    // the VI scans out directly from RDRAM. On Android, we must
    // explicitly copy the rendered frame to RDRAM for the plugin.
    // ===================================================================
    {
        int activeFb = getActiveFramebuffer();
        size_t fbSize = (size_t)gFramebufferWidth * gFramebufferHeight * sizeof(uint16_t);
        memcpy(gN64_RDRAM + g_active_fb_offset, gFramebuffers[activeFb], fbSize);
    }

    pthread_mutex_lock(&g_inputMutex);
    gN64_ControllerData[0] = g_inputMirror;
    pthread_mutex_unlock(&g_inputMutex);

    pthread_mutex_lock(&g_vblankMutex);
    if (g_vblankRequested) {
        N64_TriggerVirtualVBlankInterrupt();
        g_vblankRequested = false;
        pthread_cond_signal(&g_vblankCond);
    }
    pthread_mutex_unlock(&g_vblankMutex);

    VideoPlugin_OutputFrameTexture((uint32_t)textureId);

    BKA_DropEngineLock();

    // FIXED: GLSurfaceView calls eglSwapBuffers automatically after
    // onDrawFrame returns. We don't need to do it here.
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeUpdateInput(JNIEnv* env, jclass clazz,
                                                    jint buttons,
                                                    jfloat stickX, jfloat stickY) {
    pthread_mutex_lock(&g_inputMutex);
    g_inputMirror.button    = (uint16_t)buttons;
    g_inputMirror.stick_x   = (int8_t)(stickX * 80.0f);
    g_inputMirror.stick_y   = (int8_t)(stickY * 80.0f);
    g_inputMirror.errno_val = 0;
    pthread_mutex_unlock(&g_inputMutex);
}

} // extern "C"