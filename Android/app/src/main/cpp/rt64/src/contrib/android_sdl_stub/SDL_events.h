#ifndef RT64_ANDROID_SDL_STUB_SDL_EVENTS_H
#define RT64_ANDROID_SDL_STUB_SDL_EVENTS_H

#include "SDL_stdinc.h"
#include "SDL_scancode.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct SDL_KeyboardEvent {
    unsigned int type;
    unsigned int timestamp;
    unsigned int windowID;
    unsigned int state;
    unsigned int repeat;
    struct {
        unsigned int scancode;
        unsigned int sym;
        unsigned int mod;
    } keysym;
} SDL_KeyboardEvent;

typedef struct SDL_MouseMotionEvent {
    unsigned int type;
    unsigned int timestamp;
    unsigned int windowID;
    int x, y, xrel, yrel;
} SDL_MouseMotionEvent;

typedef struct SDL_MouseButtonEvent {
    unsigned int type;
    unsigned int timestamp;
    unsigned int windowID;
    unsigned int button;
    unsigned int state;
    int x, y;
} SDL_MouseButtonEvent;

typedef struct SDL_MouseWheelEvent {
    unsigned int type;
    unsigned int timestamp;
    unsigned int windowID;
    int x, y;
} SDL_MouseWheelEvent;

typedef union SDL_Event {
    unsigned int type;
    SDL_KeyboardEvent key;
    SDL_MouseMotionEvent motion;
    SDL_MouseButtonEvent button;
    SDL_MouseWheelEvent wheel;
    char padding[64];
} SDL_Event;

typedef int (*SDL_EventFilter)(void *userdata, SDL_Event *event);

#define SDL_KEYDOWN         0x300
#define SDL_KEYUP           0x301
#define SDL_MOUSEMOTION     0x400
#define SDL_MOUSEBUTTONDOWN 0x401
#define SDL_MOUSEBUTTONUP   0x402
#define SDL_MOUSEWHEEL      0x403

#ifdef __cplusplus
}
#endif

#endif
