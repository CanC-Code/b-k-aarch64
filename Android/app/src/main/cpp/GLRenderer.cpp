#include "GLRenderer.hpp"
#include <android/log.h>

#define LOG_TAG "GLRenderer"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

void GLRenderer::setOTRData(const std::vector<uint8_t>& data) {
    otrData = data;
    LOGI("OTR data set (%zu bytes)", data.size());
}

void GLRenderer::draw() {
    if (otrData.empty()) return;

    // Placeholder: implement actual OpenGL rendering using otrData
    LOGI("Drawing OTR data (%zu bytes)", otrData.size());
}

void GLRenderer::clear() {
    otrData.clear();
    LOGI("Cleared OTR data");
}