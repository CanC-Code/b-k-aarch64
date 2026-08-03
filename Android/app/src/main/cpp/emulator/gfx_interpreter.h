#pragma once
#include "n64_os_types_cpp.h"
#include <stdint.h>

// =======================================================================
// N64 F3DEX Display List → Software Rasterizer
//
// Intercepts Gfx tasks submitted via osSpTaskStartGo, parses the
// F3DEX command stream, and renders directly into gFramebuffers
// in RGB565 format. This is a complete software implementation of
// the N64 Reality Display Processor pipeline for 2D operations.
//
// Thread safety: Must be called while holding the engine GIL.
// Writes to gFramebuffers[getActiveFramebuffer()].
// =======================================================================

#ifdef __cplusplus
extern "C" {
#endif

void RSP_ProcessGfxTask(OSTask* tp);

#ifdef __cplusplus
}
#endif