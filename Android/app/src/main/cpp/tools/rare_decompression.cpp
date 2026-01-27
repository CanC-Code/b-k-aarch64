#include <vector>
#include <cstdint>
#include <zlib.h>

extern "C" {

void decompress_rare_asset(const std::vector<uint8_t>& input, std::vector<uint8_t>& output) {
    if (input.size() < 2) return;

    // Rare compression often uses a custom header (0x1172)
    // and raw deflate (wbits -15)
    z_stream strm;
    strm.zalloc = Z_NULL;
    strm.zfree = Z_NULL;
    strm.opaque = Z_NULL;
    strm.avail_in = input.size();
    strm.next_in = (Bytef*)input.data();

    // -15 for raw deflate without zlib/gzip headers
    if (inflateInit2(&strm, -15) != Z_OK) return;

    output.resize(input.size() * 4); // Initial guess
    strm.avail_out = output.size();
    strm.next_out = (Bytef*)output.data();

    int ret = inflate(&strm, Z_FINISH);
    if (ret == Z_STREAM_END || ret == Z_OK) {
        output.resize(strm.total_out);
    }

    inflateEnd(&strm);
}

} // extern "C"
