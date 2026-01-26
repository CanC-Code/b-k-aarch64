#include <zlib.h>
#include <vector>
#include <stdint.h>

// Mirroring the Python rareunzip.py logic
bool decompress_rare_asset(const std::vector<uint8_t>& compressed, std::vector<uint8_t>& out) {
    if (compressed.size() < 2 || compressed[0] != 0x11 || compressed[1] != 0x72) {
        return false; // Not a Rare-compressed asset
    }

    // Skip the 2-byte header (0x1172)
    const uint8_t* data_ptr = compressed.data() + 2;
    size_t data_len = compressed.size() - 2;

    z_stream strm = {0};
    strm.next_in = (Bytef*)data_ptr;
    strm.avail_in = (uInt)data_len;

    // windowBits -15 is for raw deflate (no zlib/gzip headers)
    if (inflateInit2(&strm, -15) != Z_OK) return false;

    uint8_t buffer[4096];
    int ret;
    do {
        strm.next_out = buffer;
        strm.avail_out = sizeof(buffer);
        ret = inflate(&strm, Z_NO_FLUSH);
        if (ret == Z_OK || ret == Z_STREAM_END) {
            out.insert(out.end(), buffer, buffer + (sizeof(buffer) - strm.avail_out));
        }
    } while (ret == Z_OK);

    inflateEnd(&strm);
    return ret == Z_STREAM_END;
}
