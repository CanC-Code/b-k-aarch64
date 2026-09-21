// native_main.cpp — NativeActivity entry and EGL render loop.
#include <android_native_app_glue.h>
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
    uint32_t magenta[16]; for (int i=0;i<16;i++) magenta[i]=0xFFFF00FF;
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 4, 4, 0, GL_RGBA, GL_UNSIGNED_BYTE, magenta);

    static const float V[8] = { -1,-1,  1,-1, -1,1,  1,1 };
    static const float T[8] = {  0, 1,  1, 1,  0,0,  1,0 };
    glGenBuffers(1, &g_rs.vboV);
    glBindBuffer(GL_ARRAY_BUFFER, g_rs.vboV);
    glBufferData(GL_ARRAY_BUFFER, sizeof(V), V, GL_STATIC_DRAW);
    glGenBuffers(1, &g_rs.vboT);
    glBindBuffer(GL_ARRAY_BUFFER, g_rs.vboT);
    glBufferData(GL_ARRAY_BUFFER, sizeof(T), T, GL_STATIC_DRAW);
}

static void termEGL();   // forward — defined below initEGL
static bool initEGL(ANativeWindow* win) {
    // Context already exists — recreate only the window surface.
    if (g_rs.dpy != EGL_NO_DISPLAY && g_rs.ctx != EGL_NO_CONTEXT) {
        EGLConfig c;
        EGLint numCfg = 0;
        const EGLint cfgAttr[] = {
            EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
            EGL_SURFACE_TYPE,    EGL_WINDOW_BIT,
            EGL_RED_SIZE,5, EGL_GREEN_SIZE,6, EGL_BLUE_SIZE,5, EGL_ALPHA_SIZE,0,
            EGL_DEPTH_SIZE,16, EGL_NONE };
        eglChooseConfig(g_rs.dpy, cfgAttr, &c, 1, &numCfg);
        if (numCfg > 0) {
            g_rs.surf = eglCreateWindowSurface(g_rs.dpy, c, win, nullptr);
            if (g_rs.surf != EGL_NO_SURFACE &&
                eglMakeCurrent(g_rs.dpy, g_rs.surf, g_rs.surf, g_rs.ctx)) {
                eglQuerySurface(g_rs.dpy, g_rs.surf, EGL_WIDTH,  &g_rs.w);
                eglQuerySurface(g_rs.dpy, g_rs.surf, EGL_HEIGHT, &g_rs.h);
                eglSwapInterval(g_rs.dpy, 1);
                glViewport(0, 0, g_rs.w, g_rs.h);
                g_rs.ready = true;
                bka_surface_ready(g_rs.w, g_rs.h);
                LOGI("EGL surface recreated %dx%d (context preserved)", g_rs.w, g_rs.h);
                return true;
            }
        }
        LOGI("EGL surface recreation failed; falling back to full reinit");
        termEGL();
    }

    g_rs.dpy = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if (g_rs.dpy == EGL_NO_DISPLAY) return false;
    if (!eglInitialize(g_rs.dpy, nullptr, nullptr)) return false;

    const EGLint cfg[] = {
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_SURFACE_TYPE,    EGL_WINDOW_BIT,
        EGL_RED_SIZE,5, EGL_GREEN_SIZE,6, EGL_BLUE_SIZE,5, EGL_ALPHA_SIZE,0,
        EGL_DEPTH_SIZE,16, EGL_NONE };
    EGLConfig c; EGLint n = 0;
    if (!eglChooseConfig(g_rs.dpy, cfg, &c, 1, &n) || n == 0) { LOGE("chooseConfig"); return false; }
    EGLint fmt = 0;
    eglGetConfigAttrib(g_rs.dpy, c, EGL_NATIVE_VISUAL_ID, &fmt);
    ANativeWindow_setBuffersGeometry(win, 0, 0, fmt);

    const EGLint ca[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    g_rs.ctx = eglCreateContext(g_rs.dpy, c, EGL_NO_CONTEXT, ca);
    if (g_rs.ctx == EGL_NO_CONTEXT) { LOGE("createContext"); return false; }
    g_rs.surf = eglCreateWindowSurface(g_rs.dpy, c, win, nullptr);
    if (g_rs.surf == EGL_NO_SURFACE) { LOGE("createWindowSurface"); return false; }
    if (!eglMakeCurrent(g_rs.dpy, g_rs.surf, g_rs.surf, g_rs.ctx)) { LOGE("makeCurrent"); return false; }
    eglQuerySurface(g_rs.dpy, g_rs.surf, EGL_WIDTH,  &g_rs.w);
    eglQuerySurface(g_rs.dpy, g_rs.surf, EGL_HEIGHT, &g_rs.h);
    LOGI("EGL up %dx%d", g_rs.w, g_rs.h);

    initGL();
    glViewport(0, 0, g_rs.w, g_rs.h);
    g_rs.ready = true;
    bka_surface_ready(g_rs.w, g_rs.h);
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

static void renderFrame() {
    if (!g_rs.ready) return;
    int64_t t = nowNs();
    if (g_rs.lastNs && t - g_rs.lastNs < 33000000LL) return;
    g_rs.lastNs = t;

    bka_update_texture((int)g_rs.tex);

    glClearColor(0,0,0,1);
    glClear(GL_COLOR_BUFFER_BIT);
    glUseProgram(g_rs.prog);
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, g_rs.tex);
    glUniform1i(g_rs.uTex, 0);

    glBindBuffer(GL_ARRAY_BUFFER, g_rs.vboV);
    glEnableVertexAttribArray(g_rs.posLoc);
    glVertexAttribPointer(g_rs.posLoc, 2, GL_FLOAT, GL_FALSE, 0, nullptr);
    glBindBuffer(GL_ARRAY_BUFFER, g_rs.vboT);
    glEnableVertexAttribArray(g_rs.texLoc);
    glVertexAttribPointer(g_rs.texLoc, 2, GL_FLOAT, GL_FALSE, 0, nullptr);

    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
    glDisableVertexAttribArray(g_rs.posLoc);
    glDisableVertexAttribArray(g_rs.texLoc);
    // Present at a heavily throttled rate.  The Motorola/Android-14
    // libgui UAF at 0x7b15010110 fires on buffer-transaction callbacks;
    // reducing the swap rate to ~6 fps cuts the framework's churn to
    // ~1/5th of 30fps and stays below the UAF trigger threshold in
    // observed runs.
    static int64_t s_lastSwapNs = 0;
    if (t - s_lastSwapNs >= 100000000LL) {   // 100ms ≈ 10 fps
        s_lastSwapNs = t;
        eglSwapBuffers(g_rs.dpy, g_rs.surf);
    }

    if (++g_rs.frames <= 3 || g_rs.frames % 120 == 0) LOGI("frame %d", g_rs.frames);
}

static void onAppCmd(android_app* app, int32_t cmd) {
    switch (cmd) {
        case APP_CMD_INIT_WINDOW:
            if (app->window) {
                initEGL(app->window);
                if (!g_booted) {
                    g_booted = true;
                    const char* dir = app->activity->internalDataPath;
                    LOGI("boot engine dir=%s", dir);
                    bka_native_game_boot(dir, app->activity->assetManager);
                }
            }
            break;
        case APP_CMD_TERM_WINDOW: termSurfaceOnly(); break;
        case APP_CMD_WINDOW_RESIZED:
            if (g_rs.ready && app->window) {
                eglQuerySurface(g_rs.dpy, g_rs.surf, EGL_WIDTH, &g_rs.w);
                eglQuerySurface(g_rs.dpy, g_rs.surf, EGL_HEIGHT, &g_rs.h);
                glViewport(0, 0, g_rs.w, g_rs.h);
                bka_surface_ready(g_rs.w, g_rs.h);
            }
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

    pthread_t wd;
    pthread_create(&wd, nullptr, bka_startup_watchdog, app);
    pthread_detach(wd);

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
