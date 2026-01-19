#include "GLRenderer.hpp"
#include <android/log.h>

#define LOG_TAG "GLRenderer"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void GLRenderer::init() {
    // OpenGL initialization code
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    LOGI("GLRenderer initialized");
}

void GLRenderer::setOTRMemory(uint8_t* data, int size) {
    mOTR = data;
    mOTRSize = size;
    LOGI("OTR memory set: %d bytes", size);
    // Here you could parse OTR into textures, meshes, etc.
}

void GLRenderer::renderFrame() {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    if (!mOTR || mOTRSize == 0) return;

    // Minimal placeholder: in real code, you decode OTR and draw
    // For example, use VBOs, shaders, textures from OTR memory
}