#ifndef RT64_ANDROID_SDL_STUB
#define RT64_ANDROID_SDL_STUB

#ifdef __ANDROID__

// Minimal SDL stub for RT64 compilation on Android.
// It only needs type declarations used in headers, not actual functions.

typedef struct SDL_Window SDL_Window;
typedef void* SDL_GLContext;

#endif // __ANDROID__

#endif // RT64_ANDROID_SDL_STUB
