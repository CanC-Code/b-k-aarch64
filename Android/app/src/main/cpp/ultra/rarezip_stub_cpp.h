#pragma once
// C++-safe rarezip declarations - does NOT include ultra64.h

#include "n64_types_cpp.h"

#ifdef __cplusplus
extern "C" {
#endif

extern u8 *D_80007284;
extern u8 *D_80007290;
extern u8 *inbuf;

uint8_t* decompress_rare_asset(uint8_t* srcBuffer, uint32_t srcSize, uint32_t* bytesWritten);

#ifdef __cplusplus
}
#endif
