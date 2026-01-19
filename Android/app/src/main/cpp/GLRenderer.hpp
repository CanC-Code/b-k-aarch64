#pragma once
#include <jni.h>
#include <GLES3/gl3.h>
#include <cstdint>

class GLRenderer {
public:
    GLRenderer() = default;

    void init();
    void renderFrame();
    void setOTRMemory(uint8_t* data, int size);

private:
    uint8_t* mOTR = nullptr;
    int mOTRSize = 0;
};