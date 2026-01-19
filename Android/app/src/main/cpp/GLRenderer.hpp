#pragma once
#include <vector>
#include <cstdint>

class GLRenderer {
public:
    static GLRenderer& getInstance() {
        static GLRenderer instance;
        return instance;
    }

    void setOTRData(const std::vector<uint8_t>& data);
    void draw();
    void clear();

private:
    GLRenderer() = default;
    std::vector<uint8_t> otrData;
};