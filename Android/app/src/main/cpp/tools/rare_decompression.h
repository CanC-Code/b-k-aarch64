#ifndef RARE_DECOMPRESSION_H
#define RARE_DECOMPRESSION_H

#include <stdint.h>
#include <stdlib.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Decompresses a Rare asset starting with the 0x1172 header.
 * * @param src Pointer to the start of the compressed data in the ROM
 * @param out_size Pointer to a uint32_t where the resulting size will be stored
 * @return Pointer to the newly allocated decompressed buffer. 
 * The caller is responsible for calling free() on this pointer.
 */
uint8_t* decompress_rare_asset(const uint8_t* src, uint32_t* out_size);

#ifdef __cplusplus
}
#endif

#endif // RARE_DECOMPRESSION_H
