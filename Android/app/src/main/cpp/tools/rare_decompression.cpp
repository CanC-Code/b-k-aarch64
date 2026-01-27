#include "rare_decompression.h"
#include <zlib.h>
#include <stdlib.h>
#include <string.h>

extern "C" {

uint8_t* decompress_rare_asset(const uint8_t* src, uint32_t src_size, uint32_t* out_size) {
    if (!src || src_size < 6) return nullptr;

    // Rare Magic 0x1172
    if (src[0] != 0x11 || src[1] != 0x72) return nullptr;

    // Decompressed size is Big Endian
    uint32_t decompLen = (src[2] << 24) | (src[3] << 16) | (src[4] << 8) | src[5];

    // Sanity check: don't allocate more than 32MB for a single asset (adjust if needed)
    if (decompLen == 0 || decompLen > 32 * 1024 * 1024) return nullptr;

    uint8_t* outBuf = (uint8_t*)malloc(decompLen);
    if (!outBuf) return nullptr;

    z_stream strm;
    memset(&strm, 0, sizeof(strm));

    strm.next_in = (Bytef*)(src + 6); 
    strm.avail_in = src_size - 6; 
    strm.next_out = (Bytef*)outBuf;
    strm.avail_out = decompLen;

    // raw inflate
    if (inflateInit2(&strm, -15) != Z_OK) {
        free(outBuf);
        return nullptr;
    }

    int ret = inflate(&strm, Z_FINISH);
    inflateEnd(&strm);

    if (ret != Z_STREAM_END) {
        // If it fails, we free the buffer so we don't leak memory during the "stuck" phase
        free(outBuf);
        return nullptr;
    }

    if (out_size) *out_size = decompLen;
    return outBuf;
}

}
