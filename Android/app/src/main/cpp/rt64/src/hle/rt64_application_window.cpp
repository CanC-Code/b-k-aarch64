#include "rt64_application_window.h"

namespace RT64 {

ApplicationWindow *ApplicationWindow::HookedApplicationWindow = nullptr;

ApplicationWindow::ApplicationWindow() {
    HookedApplicationWindow = this;
}

ApplicationWindow::~ApplicationWindow() {
    if (HookedApplicationWindow == this) HookedApplicationWindow = nullptr;
}

void ApplicationWindow::setup(RenderWindow window, Listener *listener, uint32_t threadId) {
    // Android: window already provided
    windowHandle = window;
    this->listener = listener;
}

void ApplicationWindow::setup(const char *windowTitle, Listener *listener) {
    // Android: no-op, window already set
    this->listener = listener;
}

void ApplicationWindow::setFullScreen(bool newFullScreen) { fullScreen = newFullScreen; }

void ApplicationWindow::makeResizable() { }

void ApplicationWindow::detectRefreshRate() { refreshRate = 60; }

uint32_t ApplicationWindow::getRefreshRate() const { return refreshRate; }

bool ApplicationWindow::detectWindowMoved() { return false; }

void ApplicationWindow::sdlCheckFilterInstallation() { }

int ApplicationWindow::sdlEventFilter(void *userdata, SDL_Event *event) { return 0; }

} // namespace RT64
