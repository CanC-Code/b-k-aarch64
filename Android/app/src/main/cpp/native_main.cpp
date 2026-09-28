// native_main.cpp — NativeActivity entry and EGL render loop.
#include <android_native_app_glue.h>
#include <jni.h>
#include <android/native_window.h>
#include <android/asset_manager.h>
#include <android/log.h>
#include <EGL/egl.h>
#include <GLES2/gl2.h>
#include <cstring>
#include <cstdio>
#include <ctime>
#include <unistd.h>

#define LOG_TAG "BKA-Native"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" void bka_surface_ready(int w, int h);
extern "C" void bka_update_texture(int texId);
extern "C" void bka_native_game_boot(const char* dir, AAssetManager* mgr);

static bool g_booted = false;

struct RS {
    EGLDisplay dpy = EGL_NO_DISPLAY;
    EGLSurface surf = EGL_NO_SURFACE;
    EGLContext ctx = EGL_NO_CONTEXT;
    int w = 0, h = 0;
    bool ready = false;
    GLuint prog = 0, tex = 0, vboV = 0, vboT = 0;
    int posLoc = -1, texLoc = -1, uTex = -1;
    int64_t lastNs = 0;
    int frames = 0;
} g_rs;

static const char* VS =
    "attribute vec4 aPosition;attribute vec2 aTexCoord;"
    "varying vec2 vTexCoord;"
    "void main(){gl_Position=aPosition;vTexCoord=aTexCoord;}";
static const char* FS =
    "precision mediump float;varying vec2 vTexCoord;"
    "uniform sampler2D uTexture;"
    "void main(){gl_FragColor=texture2D(uTexture,vTexCoord);}";

static GLuint mkShader(GLenum t, const char* s) {
    GLuint x = glCreateShader(t);
    glShaderSource(x, 1, &s, nullptr);
    glCompileShader(x);
    GLint ok = 0; glGetShaderiv(x, GL_COMPILE_STATUS, &ok);
    if (!ok) { char l[512]={0}; glGetShaderInfoLog(x,511,nullptr,l); LOGE("shader: %s", l); return 0; }
    return x;
}

static void initGL() {
    GLuint v = mkShader(GL_VERTEX_SHADER, VS);
    GLuint f = mkShader(GL_FRAGMENT_SHADER, FS);
    if (!v || !f) return;
    g_rs.prog = glCreateProgram();
    glAttachShader(g_rs.prog, v); glAttachShader(g_rs.prog, f);
    glLinkProgram(g_rs.prog);
    g_rs.posLoc = glGetAttribLocation(g_rs.prog, "aPosition");
    g_rs.texLoc = glGetAttribLocation(g_rs.prog, "aTexCoord");
    g_rs.uTex   = glGetUniformLocation(g_rs.prog, "uTexture");

    glGenTextures(1, &g_rs.tex);
    glBindTexture(GL_TEXTURE_2D, g_rs.tex);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    // DIAG 2026-09-24: bright red placeholder -- if the screen turns red
    // the quad + swap path is working and the failure is in the framebuffer
    // upload.  If it stays green-sliver, the quad is off-screen or the
    // surface is wrong.  Restore to magenta once diagnosed.
    uint8_t placeholder_rgba[4*4*4];
    for (int i = 0; i < 64; i += 4) {
        placeholder_rgba[i+0] = 0xFF;  // R
        placeholder_rgba[i+1] = 0x00;  // G
        placeholder_rgba[i+2] = 0x00;  // B
        placeholder_rgba[i+3] = 0xFF;  // A
    }
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 4, 4, 0, GL_RGBA, GL_UNSIGNED_BYTE, placeholder_rgba);

    static const float V[8] = { -1,-1,  1,-1, -1,1,  1,1 };
    static const float T[8] = {  0, 1,  1, 1,  0,0,  1,0 };
    glGenBuffers(1, &g_rs.vboV);
    glBindBuffer(GL_ARRAY_BUFFER, g_rs.vboV);
    glBufferData(GL_ARRAY_BUFFER, sizeof(V), V, GL_STATIC_DRAW);
    glGenBuffers(1, &g_rs.vboT);
    glBindBuffer(GL_ARRAY_BUFFER, g_rs.vboT);
    glBufferData(GL_ARRAY_BUFFER, sizeof(T), T, GL_STATIC_DRAW);
}

extern "C" {
extern uint8_t* gN64_RDRAM;
extern uint32_t g_active_fb_offset;
extern volatile int g_bka_pixels_drawn;
}

static ANativeWindow* g_native_window = nullptr;

static void termEGL();   // forward — defined below initEGL
static bool initEGL(ANativeWindow* win) {
    g_native_window = win;
    if (g_rs.dpy != EGL_NO_DISPLAY) termEGL();

    g_rs.dpy = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (g_rs.dpy == EGL_NO_DISPLAY) return false;
    if (!eglInitialize(g_rs.dpy, nullptr, nullptr)) return false;

    const EGLint cfg[] = {
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_SURFACE_TYPE,    EGL_PBUFFER_BIT,
        EGL_RED_SIZE,8, EGL_GREEN_SIZE,8, EGL_BLUE_SIZE,8, EGL_ALPHA_SIZE,8,
        EGL_DEPTH_SIZE,16, EGL_NONE };
    EGLConfig c; EGLint n = 0;
    if (!eglChooseConfig(g_rs.dpy, cfg, &c, 1, &n) || n == 0) return false;

    const EGLint ca[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    g_rs.ctx = eglCreateContext(g_rs.dpy, c, EGL_NO_CONTEXT, ca);
    if (g_rs.ctx == EGL_NO_CONTEXT) return false;

    const EGLint pbAttr[] = { EGL_WIDTH, 292, EGL_HEIGHT, 216, EGL_NONE };
    g_rs.surf = eglCreatePbufferSurface(g_rs.dpy, c, pbAttr);
    if (g_rs.surf == EGL_NO_SURFACE) return false;
    if (!eglMakeCurrent(g_rs.dpy, g_rs.surf, g_rs.surf, g_rs.ctx)) return false;

    initGL();
    g_rs.w = 292; g_rs.h = 216;
    g_rs.ready = true;
    LOGI("EGL pbuffer up 292x216");
    return true;
}

// Destroy only the window surface; keep the EGL context alive.  The
// Android 14 Motorola libgui UAF is triggered by window-handle churn
// (window destroy + create); holding the context across pause/resume
// minimises the number of lifetimes the framework's transaction
// listener has to track.
static void termSurfaceOnly() {
    if (g_rs.dpy == EGL_NO_DISPLAY) return;
    eglMakeCurrent(g_rs.dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, g_rs.ctx);
    if (g_rs.surf != EGL_NO_SURFACE) {
        eglDestroySurface(g_rs.dpy, g_rs.surf);
        g_rs.surf = EGL_NO_SURFACE;
    }
    g_rs.ready = false;
}

// Full EGL teardown.  Only called when the process is exiting.
static void termEGL() {
    if (g_rs.dpy == EGL_NO_DISPLAY) return;
    eglMakeCurrent(g_rs.dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    if (g_rs.surf != EGL_NO_SURFACE) eglDestroySurface(g_rs.dpy, g_rs.surf);
    if (g_rs.ctx  != EGL_NO_CONTEXT) eglDestroyContext(g_rs.dpy, g_rs.ctx);
    eglTerminate(g_rs.dpy);
    g_rs.dpy = EGL_NO_DISPLAY; g_rs.surf = EGL_NO_SURFACE; g_rs.ctx = EGL_NO_CONTEXT;
    g_rs.ready = false;
}

static int64_t nowNs() {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return (int64_t)t.tv_sec * 1000000000LL + t.tv_nsec;
}

static void dumpFramebufferPPM(int frame_num) {
    if (!gN64_RDRAM) return;
    uint16_t* fb = (uint16_t*)(gN64_RDRAM + g_active_fb_offset);
    char path[256];
    snprintf(path, sizeof(path), "/data/data/com.bkawrapper/files/fb_%04d.ppm", frame_num);
    FILE* f = fopen(path, "wb");
    if (!f) return;
    fprintf(f, "P6\n292 216\n255\n");
    for (int i = 0; i < 292 * 216; i++) {
        uint16_t px = fb[i];
        uint8_t r = (px >> 11) & 0x1F; r = (r << 3) | (r >> 2);
        uint8_t g = (px >> 5) & 0x3F;  g = (g << 2) | (g >> 4);
        uint8_t b = px & 0x1F;         b = (b << 3) | (b >> 2);
        fputc(r, f); fputc(g, f); fputc(b, f);
    }
    fclose(f);
    LOGI("PPM written: %s", path);
}
extern "C" void bka_dump_fb(int n) { dumpFramebufferPPM(n); }

static void renderFrame() {
    if (!g_rs.ready || !g_native_window) return;
    if (!gN64_RDRAM) return;

    int64_t t = nowNs();
    if (g_rs.lastNs && t - g_rs.lastNs < 33000000LL) return;
    g_rs.lastNs = t;

    uint16_t* src = (uint16_t*)(gN64_RDRAM + g_active_fb_offset);

    ANativeWindow_Buffer buf;
    if (ANativeWindow_lock(g_native_window, &buf, nullptr) == 0) {
        int W = 292, H = 216;
        int dw = buf.width, dh = buf.height;
        int scale = dw / W < dh / H ? dw / W : dh / H;
        if (scale < 1) scale = 1;
        int outW = W * scale, outH = H * scale;
        int ox = (dw - outW) / 2, oy = (dh - outH) / 2;
        uint32_t* dst = (uint32_t*)buf.bits;
        memset(dst, 0, (size_t)dw * dh * 4);
        for (int y = 0; y < outH; y++) {
            int sy = y / scale;
            const uint16_t* srow = src + sy * W;
            uint32_t* drow = dst + (oy + y) * dw + ox;
            for (int x = 0; x < outW; x++) {
                uint16_t px = srow[x / scale];
                uint8_t r = (px >> 11) & 0x1F; r = (r << 3) | (r >> 2);
                uint8_t g = (px >> 5)  & 0x3F; g = (g << 2) | (g >> 4);
                uint8_t b = px & 0x1F;         b = (b << 3) | (b >> 2);
                drow[x] = 0xFF000000u | (b << 16) | (g << 8) | r;
            }
        }
        ANativeWindow_unlockAndPost(g_native_window);
    }

    if (++g_rs.frames <= 3 || g_rs.frames % 120 == 0) LOGI("frame %d", g_rs.frames);
}

static void onAppCmd(android_app* app, int32_t cmd) {
    switch (cmd) {
        case APP_CMD_INIT_WINDOW:
            if (app->window) {
                g_native_window = app->window;
                ANativeWindow_setBuffersGeometry(app->window, 0, 0, WINDOW_FORMAT_RGBA_8888);
                initEGL(app->window);
                if (!g_booted) {
                    g_booted = true;
                    const char* dir = app->activity->internalDataPath;
                    LOGI("boot engine dir=%s", dir);
                    bka_native_game_boot(dir, app->activity->assetManager);
                }
            }
            break;
        case APP_CMD_TERM_WINDOW:
            g_native_window = nullptr;
            break;
        case APP_CMD_WINDOW_RESIZED:
            if (app->window) g_native_window = app->window;
            break;
        default: break;
    }
}

static int32_t onInput(android_app*, AInputEvent*) { return 0; }

// Watchdog: if the render loop never produces frames (SurfFlinger UAF,
// game-thread deadlock, etc.), exit cleanly so the user can relaunch
// without the "app has stopped" dialog.
static void* bka_startup_watchdog(void* arg) {
    android_app* app = (android_app*)arg;
    for (int i = 0; i < 30; i++) {      // up to 15s
        usleep(500000);
        // Not healthy merely because the loop ran — the game must have
        // produced at least one frame with actual pixels.  Check the
        // value that lowlevel_bridge.cpp updates on every upload.
        extern volatile int g_bka_real_frame_count;
        if (g_bka_real_frame_count > 0) return nullptr;
    }
    LOGE("Watchdog: no frames in 12s — exiting for clean retry");
    ANativeActivity_finish(app->activity);
    return nullptr;
}

void android_main(android_app* app) {
    app->onAppCmd = onAppCmd;
    app->onInputEvent = onInput;
    LOGI("android_main enter");

    // Watchdog disabled for diagnostic run
    (void)bka_startup_watchdog;

    for (;;) {
        int events = 0;
        android_poll_source* src = nullptr;
        int timeout = (app->window && g_rs.ready) ? 0 : -1;
        while (ALooper_pollAll(timeout, nullptr, &events, (void**)&src) >= 0) {
            if (src) src->process(app, src);
            if (app->destroyRequested) { termEGL(); return; }
            timeout = 0;
        }
        if (app->window && g_rs.ready) renderFrame();
    }
}


extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_Native_fillArgb(JNIEnv* env, jobject /*thiz*/, jintArray outArr) {
    extern uint8_t* gN64_RDRAM;
    extern uint32_t g_active_fb_offset;
    if (!gN64_RDRAM || !outArr) return;
    jint* out = env->GetIntArrayElements(outArr, nullptr);
    if (!out) return;
    uint16_t* src = (uint16_t*)(gN64_RDRAM + g_active_fb_offset);
    const int W = 292, H = 216;
    for (int i = 0; i < W * H; i++) {
        uint16_t px = src[i];
        uint8_t r = (px >> 11) & 0x1F; r = (r << 3) | (r >> 2);
        uint8_t g = (px >> 5)  & 0x3F; g = (g << 2) | (g >> 4);
        uint8_t b = px & 0x1F;         b = (b << 3) | (b >> 2);
        out[i] = (jint)(0xFF000000u | ((uint32_t)r << 16) | ((uint32_t)g << 8) | (uint32_t)b);
    }
    env->ReleaseIntArrayElements(outArr, out, 0);
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_Native_startEngine(JNIEnv* env, jobject /*thiz*/, jstring dir) {
    if (!dir) return;
    const char* cdir = env->GetStringUTFChars(dir, nullptr);
    if (!cdir) return;
    bka_native_game_boot(cdir, nullptr);
    env->ReleaseStringUTFChars(dir, cdir);
}
