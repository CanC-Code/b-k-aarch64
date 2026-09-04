#pragma once
#include <cstdint>
#include <memory>

namespace RT64 {
    class Application;
}

class RT64Renderer {
public:
    static RT64Renderer& get();
    void initialize();
    void shutdown();
    void processDisplayLists(uint8_t* rdram, uint32_t dlStart, uint32_t dlEnd, bool isHLE);
private:
    RT64Renderer() = default;
    std::unique_ptr<RT64::Application> app_;
    bool initialized_ = false;
};
