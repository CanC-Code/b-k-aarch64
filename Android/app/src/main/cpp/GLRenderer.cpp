#include <jni.h>
#include <GLES2/gl2.h>
#include <android/log.h>
#include <mutex>

#define LOG_TAG "GLRenderer"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Thread-safe storage for OTR
static std::vector<uint8_t> gOTRData;
static std::mutex gOTRMutex;

// OpenGL handles
static GLuint gTexture = 0;

// Simple 2D texture rendering
static void setupGL() {
    glEnable(GL_TEXTURE_2D);
    glGenTextures(1, &gTexture);
    glBindTexture(GL_TEXTURE_2D, gTexture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
}

// Upload OTR data to texture
static void uploadOTR() {
    std::lock_guard<std::mutex> lock(gOTRMutex);
    if (gOTRData.empty()) return;

    glBindTexture(GL_TEXTURE_2D, gTexture);

    // Mock: treat OTR as RGBA 256x256 image for demo purposes
    GLint width = 256;
    GLint height = 256;

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, gOTRData.data());
}

// Draw full-screen quad
static void renderQuad() {
    glClearColor(0, 0, 0, 1);
    glClear(GL_COLOR_BUFFER_BIT);

    glBindTexture(GL_TEXTURE_2D, gTexture);

    GLfloat vertices[] = {
        -1, -1, 0, 0,
         1, -1, 1, 0,
        -1,  1, 0, 1,
         1,  1, 1, 1
    };

    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);

    glVertexPointer(2, GL_FLOAT, 4 * sizeof(GLfloat), vertices);
    glTexCoordPointer(2, GL_FLOAT, 4 * sizeof(GLfloat), vertices + 2);

    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);

    glDisableClientState(GL_VERTEX_ARRAY);
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);
}

extern "C" {

// Initialize renderer
JNIEXPORT void JNICALL
Java_com_bkawrapper_GLRenderer_nativeInit(JNIEnv* env, jobject thiz) {
    setupGL();
    LOGI("GLRenderer initialized");
}

// Provide OTR bytes to renderer
JNIEXPORT void JNICALL
Java_com_bkawrapper_GLRenderer_nativeSetOTR(JNIEnv* env, jobject thiz, jbyteArray otrBytes) {
    if (!otrBytes) return;

    jsize size = env->GetArrayLength(otrBytes);
    std::vector<uint8_t> tmp(size);
    env->GetByteArrayRegion(otrBytes, 0, size, reinterpret_cast<jbyte*>(tmp.data()));

    {
        std::lock_guard<std::mutex> lock(gOTRMutex);
        gOTRData = std::move(tmp);
    }

    uploadOTR();
    LOGI("OTR uploaded to texture, size: %d", size);
}

// Render callback
JNIEXPORT void JNICALL
Java_com_bkawrapper_GLRenderer_nativeRender(JNIEnv* env, jobject thiz) {
    renderQuad();
}

} // extern "C"