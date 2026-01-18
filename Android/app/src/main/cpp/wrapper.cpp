#include <jni.h>
#include <vector>
#include <cstdint>
#include <atomic>
#include <mutex>
#include <android/log.h>
#include <GLES2/gl2.h>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// -----------------------------
// Global state for texture
// -----------------------------
static std::mutex g_texMutex;
static GLuint g_textureId = 0;

// -----------------------------
// Create standard texture (placeholder)
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv*, jclass)
{
    std::lock_guard<std::mutex> lock(g_texMutex);

    if (g_textureId != 0) {
        glDeleteTextures(1, &g_textureId);
        g_textureId = 0;
    }

    glGenTextures(1, &g_textureId);
    glBindTexture(GL_TEXTURE_2D, g_textureId);

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

    // initialize with a 1x1 black pixel
    uint8_t pixel[4] = {0, 0, 0, 255};
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixel);

    LOGI("Standard texture initialized (ID=%u)", g_textureId);
}

// -----------------------------
// Initialize texture with OTR data
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTextureWithOTR(
        JNIEnv* env, jclass, jbyteArray otrData)
{
    if (!otrData) {
        LOGE("initTextureWithOTR: null byte array");
        return;
    }

    const jsize size = env->GetArrayLength(otrData);
    if (size <= 0) {
        LOGE("initTextureWithOTR: empty array");
        return;
    }

    std::vector<uint8_t> data(size);
    env->GetByteArrayRegion(otrData, 0, size, reinterpret_cast<jbyte*>(data.data()));

    std::lock_guard<std::mutex> lock(g_texMutex);

    if (g_textureId == 0) {
        glGenTextures(1, &g_textureId);
    }

    glBindTexture(GL_TEXTURE_2D, g_textureId);

    // For demonstration, assume OTR bytes are RGBA 256x256
    const int width = 256;
    const int height = 256;

    if (data.size() < width * height * 4) {
        LOGE("OTR data too small for 256x256 RGBA texture");
        return;
    }

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA,
                 GL_UNSIGNED_BYTE, data.data());

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

    LOGI("OTR texture uploaded (ID=%u, %d bytes)", g_textureId, size);
}

// -----------------------------
// Get texture ID
// -----------------------------
extern "C"
JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_getTextureId(JNIEnv*, jclass)
{
    std::lock_guard<std::mutex> lock(g_texMutex);
    return static_cast<jint>(g_textureId);
}

// -----------------------------
// Update texture each frame
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv*, jclass, jint texId)
{
    // For now, assume OTR texture does not change every frame
    glBindTexture(GL_TEXTURE_2D, static_cast<GLuint>(texId));
}