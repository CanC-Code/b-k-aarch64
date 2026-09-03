#ifndef RT64_ANDROID_SDL_STUB_SDL_EVENTS_H
#define RT64_ANDROID_SDL_STUB_SDL_EVENTS_H

#ifdef __cplusplus
extern "C" {
#endif

typedef union SDL_Event {
    unsigned int type;
    char padding[64];
} SDL_Event;

typedef int (SDLCALL *SDL_EventFilter)(void *userdata, SDL_Event *event);

#ifdef __cplusplus
}
#endif

#endif // RT64_ANDROID_SDL_STUB_SDL_EVENTS_H
