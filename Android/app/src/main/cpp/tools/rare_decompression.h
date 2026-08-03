// File: rare_decompression.h
#ifndef RARE_DECOMPRESSION_H
#define RARE_DECOMPRESSION_H

#include <stdint.h>
#include <stdlib.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Decompresses a Rare-compressed asset into a pre-allocated buffer at a specific offset.
 * Preserves the original ROM layout by writing to the exact offset.
 *
 * @param src          Pointer to the compressed asset buffer.
 * @param src_size     Size of the compressed buffer.
 * @param out_buffer   Pre-allocated output buffer (e.g., rom_base.bin in memory).
 * @param out_offset   Offset in out_buffer to write the decompressed data.
 * @param out_size     Expected decompressed size (from the asset header).
 * @return             Number of bytes written, or 0 on failure.
 */
uint32_t decompress_rare_to_offset(
    const uint8_t* src,
    uint32_t src_size,
    uint8_t* out_buffer,
    uint32_t out_offset,
    uint32_t out_size);

#ifdef __cplusplus
}
#endif

#endif // RARE_DECOMPRESSION_H