#include <vector>
#include <GLES/gl.h>

static std::vector<uint8_t> gOTRData;

void GLRenderer::setOTRData(const std::vector<uint8_t>& data) {
    gOTRData = data;
}

void GLRenderer::draw() {
    if (gOTRData.empty()) return;

    // Example: simple quad render
    GLfloat vertices[] = {
        -1.f, -1.f, 0.f, 0.f,
         1.f, -1.f, 1.f, 0.f,
        -1.f,  1.f, 0.f, 1.f,
         1.f,  1.f, 1.f, 1.f
    };
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glVertexPointer(2, GL_FLOAT, 4 * sizeof(GLfloat), vertices);
    glTexCoordPointer(2, GL_FLOAT, 4 * sizeof(GLfloat), vertices + 2);
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
    glDisableClientState(GL_VERTEX_ARRAY);
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);
}