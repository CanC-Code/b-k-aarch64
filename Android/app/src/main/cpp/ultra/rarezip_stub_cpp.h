#pragma once
// C++-safe rarezip declarations - does NOT include ultra64.h
// Only the declarations needed by stubs.cpp and resource_mgr.cpp

#include "n64_types_cpp.h"

#ifdef __cplusplus
extern "C" {
#endif

// Decompression buffer pointers (defined in rarezip.c)
extern u8 *D_80007284;
extern u8 *D_80007290;
extern u8 *inbuf;

// Rare decompression functions
uint8_t* decompress_rare_asset(uint8_t* srcBuffer, uint32_t srcSize, uint32_t* bytesWritten);
uint32_t decompress_rare_to_offset(uint8_t* src, uint32_t src_size, uint8_t* out_buffer, uint32_t out_offset, uint32_t out_size);

// RareZip inflate
int rarezip_inflate(void* compressed, void* uncompressed);
u32 rarezip_get_uncompressed_size(void* compressed);

#ifdef __cplusplus
}
#endif
