// Android/app/src/main/cpp/tools/rare_decompression.cpp
#include "rare_decompression.h"
#include <zlib.h>
#include <stdlib.h>

uint8_t* decompress_rare_asset(const uint8_t* src, uint32_t* out_size) {
    [span_6](start_span)[span_7](start_span)// Rare Magic Header check (0x1172) used in Banjo-Kazooie[span_6](end_span)[span_7](end_span)
    if (src[0] != 0x11 || src[1] != 0x72) return nullptr;

    // Grab decompressed size (Big Endian) from the 6-byte header
    uint32_t decompLen = (src[2] << 24) | (src[3] << 16) | (src[4] << 8) | src[5];
    *out_size = decompLen;

    uint8_t* outBuf = (uint8_t*)malloc(decompLen);
    
    z_stream strm = {0};
    strm.next_in = (Bytef*)(src + 6); // Skip the Rare header
    strm.avail_in = 0xFFFFFF;        // Large enough for the compressed chunk
    strm.next_out = (Bytef*)outBuf;
    strm.avail_out = decompLen;

    [span_8](start_span)[span_9](start_span)// -15 is the window bit for raw deflate (no zlib/gzip headers)[span_8](end_span)[span_9](end_span)
    if (inflateInit2(&strm, -15) != Z_OK) {
        free(outBuf);
        return nullptr;
    }
    
    int ret = inflate(&strm, Z_FINISH);
    inflateEnd(&strm);

    if (ret != Z_STREAM_END && ret != Z_OK) {
        free(outBuf);
        return nullptr;
    }

    return outBuf;
}
