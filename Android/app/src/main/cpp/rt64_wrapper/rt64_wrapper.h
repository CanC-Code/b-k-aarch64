#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void* RT64Handle;

RT64Handle rt64_init(void* window, uint32_t width, uint32_t height);
void rt64_process_display_lists(RT64Handle handle, uint8_t* rdram, uint32_t dl_start, uint32_t dl_end, bool is_hle);
void rt64_destroy(RT64Handle handle);

#ifdef __cplusplus
}
#endif
