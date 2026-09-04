#include "rt64_application_window.h"

namespace RT64 {

ApplicationWindow::ApplicationWindow(const WindowHandle &window, Listener *listener) {
    this->windowHandle = window;
    this->listener = listener;
}

ApplicationWindow::~ApplicationWindow() { }

void ApplicationWindow::setup(const char *windowTitle, Listener *listener) {
    // Android: window already provided via constructor; nothing to do.
}

void ApplicationWindow::update() { }

void ApplicationWindow::setWindowTitle(const char *windowTitle) { }

void ApplicationWindow::setWindowIcon(const void *iconData, size_t iconSize) { }

void ApplicationWindow::getWindowBounds(int *left, int *top, int *width, int *height) {
    // Return a default 1280x720 centered (or actual from ANativeWindow later)
    *left = 0; *top = 0; *width = 1280; *height = 720;
}

void ApplicationWindow::setWindowBounds(int left, int top, int width, int height) { }

void ApplicationWindow::showCursor() { }

void ApplicationWindow::hideCursor() { }

float ApplicationWindow::getRefreshRate() const {
    return 60.0f;
}

void *ApplicationWindow::getWindowHandle() const {
    return windowHandle;
}

bool ApplicationWindow::usesWindowMessageFilter() const {
    return false;
}

void ApplicationWindow::setWindowMessageFilter() { }

} // namespace RT64
