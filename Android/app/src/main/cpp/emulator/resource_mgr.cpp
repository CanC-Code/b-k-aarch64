#include "n64_os_types_cpp.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <cerrno>
#include <algorithm>
#include <string>
#include <vector>
#include <android/log.h>
#include <pthread.h>

#include "bka_safe_base.h"
#include "rare_decompression.h"
#include "rarezip_stub_cpp.h" // For D_80007284, D_80007290, inbuf, etc.

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static std::string g_assetDir;

// Define HUFT_POOL_CAPACITY to match rarezip.c
#define HUFT_POOL_CAPACITY 4096

// Global decompression state (from rarezip.h)
extern "C" {
    u8 *inbuf;               // Input buffer (source data)
    u8 *D_80007284;          // Output buffer (decompressed data)
    u32 inptr;               // Current read position in inbuf
    u32 wp;                  // Current write position in D_80007284
    u8 *D_80007290; // Huffman table pool
    u32 bb;                  // Bit buffer
    u32 bk;                  // Bit count
    u32 crc1;                // CRC1
    u32 crc2;                // CRC2
    u32 hufts;               // Huffman table usage tracker
    u32 g_decomp_out_cap;    // Output buffer capacity
}

// Splat segment manifest
struct SegmentRecord {
    uint32_t start = 0; // inclusive ROM start offset
    uint32_t end = 0;   // exclusive ROM end offset
    std::string name;
};

static std::vector<SegmentRecord> g_segments;

// Reference the single authoritative gN64_ROM_Base defined in lowlevel_bridge.cpp.
// Due to --allow-multiple-definition, InitN64Registers may overwrite the pointer
// with an mmap'd buffer after we've already loaded ROM via malloc. To avoid this
// conflict, ResourceMgr_HandleDma now reads directly from rom_base.bin on disk
// rather than relying on the in-memory gN64_ROM_Base pointer.
extern uint8_t* gN64_ROM_Base;
static size_t g_romSize = 0;

extern "C" void BKA_SignalResourcesReady(void);

// Mutex for thread-safe decompression
pthread_mutex_t g_inflateMutex = PTHREAD_MUTEX_INITIALIZER;

// Initialize decompression buffers
static bool InitializeDecompressionBuffers(const char* romPath) {
    if (!romPath) {
        LOGE("InitializeDecompressionBuffers: romPath is NULL!");
        return false;
    }

    // Allocate Huffman pool
    D_80007290 = (u8 *)malloc(HUFT_POOL_CAPACITY * 512);
    if (!D_80007290) {
        LOGE("InitializeDecompressionBuffers: Failed to allocate Huffman pool!");
        return false;
    }

    // Allocate output buffer (16MB for ROM)
    D_80007284 = (u8 *)malloc(16 * 1024 * 1024); // 16MB
    if (!D_80007284) {
        LOGE("InitializeDecompressionBuffers: Failed to allocate decompression buffer!");
        free(D_80007290);
        D_80007290 = nullptr;
        return false;
    }
    g_decomp_out_cap = 16 * 1024 * 1024; // Set capacity to 16MB

    // Load rom_base.bin into inbuf
    FILE *f = fopen(romPath, "rb");
    if (!f) {
        LOGE("InitializeDecompressionBuffers: Failed to open %s!", romPath);
        free(D_80007284);
        free(D_80007290);
        D_80007284 = nullptr;
        D_80007290 = nullptr;
        return false;
    }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (size <= 0) {
        LOGE("InitializeDecompressionBuffers: Invalid ROM size in %s!", romPath);
        fclose(f);
        free(D_80007284);
        free(D_80007290);
        D_80007284 = nullptr;
        D_80007290 = nullptr;
        return false;
    }

    inbuf = (u8 *)malloc(size);
    if (!inbuf) {
        LOGE("InitializeDecompressionBuffers: Failed to allocate input buffer!");
        fclose(f);
        free(D_80007284);
        free(D_80007290);
        D_80007284 = nullptr;
        D_80007290 = nullptr;
        return false;
    }

    size_t bytesRead = fread(inbuf, 1, size, f);
    fclose(f);

    if (bytesRead != static_cast<size_t>(size)) {
        LOGE("InitializeDecompressionBuffers: Failed to read full ROM file!");
        free(inbuf);
        free(D_80007284);
        free(D_80007290);
        inbuf = nullptr;
        D_80007284 = nullptr;
        D_80007290 = nullptr;
        return false;
    }

    // Validate zlib header (0x78 0x9C, 0x78 0x01, or 0x78 0xDA)
    if (size >= 2) {
        if (inbuf[0] != 0x78 || (inbuf[1] != 0x9C && inbuf[1] != 0x01 && inbuf[1] != 0xDA)) {
            LOGW("InitializeDecompressionBuffers: rom_base.bin is not a valid zlib stream! Proceeding anyway (may be raw data).");
        }
    }

    // Reset global state
    inptr = 0;
    wp = 0;
    bb = 0;
    bk = 0;
    crc1 = 0;
    crc2 = -1;
    hufts = 0;

    LOGI("InitializeDecompressionBuffers: Successfully initialized buffers (inbuf=%p, D_80007284=%p, D_80007290=%p, g_decomp_out_cap=%u)",
         inbuf, D_80007284, D_80007290, g_decomp_out_cap);
    return true;
}

// Cleanup decompression buffers
static void CleanupDecompressionBuffers() {
    if (inbuf) {
        free(inbuf);
        inbuf = nullptr;
    }
    if (D_80007284) {
        free(D_80007284);
        D_80007284 = nullptr;
    }
    if (D_80007290) {
        free(D_80007290);
        D_80007290 = nullptr;
    }
    g_decomp_out_cap = 0xFFFFFFFFu; // Reset to unbounded
}

// Parses only the top-level "- name: ..." / "start:" pairs out of a splat YAML config.
static bool parseSplatSegments(const char* path, std::vector<SegmentRecord>& outSegments) {
    FILE* f = fopen(path, "rb");
    if (!f) {
        return false;
    }

    fseek(f, 0, SEEK_END);
    long fileSize = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (fileSize <= 0) {
        fclose(f);
        return false;
    }

    std::string buffer;
    buffer.resize(static_cast<size_t>(fileSize));
    size_t readBytes = fread(&buffer[0], 1, static_cast<size_t>(fileSize), f);
    fclose(f);
    buffer.resize(readBytes);

    outSegments.clear();

    std::string currentName;
    uint32_t currentStart = 0;
    bool haveCurrent = false;

    auto flushCurrent = [&]() {
        if (haveCurrent) {
            SegmentRecord rec;
            rec.start = currentStart;
            rec.end = 0; // filled in below once every start is known
            rec.name = currentName;
            outSegments.push_back(rec);
        }
    };

    size_t pos = 0;
    while (pos <= buffer.size()) {
        size_t lineEnd = buffer.find('\n', pos);
        if (lineEnd == std::string::npos) lineEnd = buffer.size();
        if (pos > buffer.size()) break;

        std::string line = buffer.substr(pos, lineEnd - pos);
        pos = lineEnd + 1;

        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        size_t firstNonSpace = line.find_first_not_of(" \t");
        if (firstNonSpace == std::string::npos || line[firstNonSpace] == '#') {
            if (lineEnd >= buffer.size()) break;
            continue;
        }

        // New top-level segment: zero leading whitespace, "- name..."
        if (firstNonSpace == 0 && line.rfind("- name", 0) == 0) {
            flushCurrent();
            haveCurrent = true;
            currentStart = 0;

            size_t colon = line.find(':', 6);
            if (colon != std::string::npos) {
                std::string nameVal = line.substr(colon + 1);
                size_t hash = nameVal.find('#');
                if (hash != std::string::npos) nameVal = nameVal.substr(0, hash);
                size_t s = nameVal.find_first_not_of(" \t");
                size_t e = nameVal.find_last_not_of(" \t");
                currentName = (s == std::string::npos) ? "" : nameVal.substr(s, e - s + 1);
            } else {
                currentName.clear();
            }

            if (lineEnd >= buffer.size()) break;
            continue;
        }

        if (!haveCurrent) {
            if (lineEnd >= buffer.size()) break;
            continue;
        }

        std::string trimmedLine = line.substr(firstNonSpace);
        if (trimmedLine.rfind("start:", 0) == 0) {
            std::string val = trimmedLine.substr(6);
            size_t hash = val.find('#');
            if (hash != std::string::npos) val = val.substr(0, hash);
            currentStart = static_cast<uint32_t>(strtoul(val.c_str(), nullptr, 0));
        }

        if (lineEnd >= buffer.size()) break;
    }
    flushCurrent();

    std::sort(outSegments.begin(), outSegments.end(),
              [](const SegmentRecord& a, const SegmentRecord& b) { return a.start < b.start; });

    for (size_t i = 0; i + 1 < outSegments.size(); ++i) {
        outSegments[i].end = outSegments[i + 1].start;
    }

    return !outSegments.empty();
}

static const SegmentRecord* findSegmentForOffset(uint32_t offset) {
    for (const auto& seg : g_segments) {
        if (offset >= seg.start && offset < seg.end) {
            return &seg;
        }
    }
    return nullptr;
}

// External implementation of BKA_InflateCodeSegment
extern "C" void BKA_InflateCodeSegment(void* dramAddr, uint32_t romOffset, uint32_t size) {
    if (!gN64_ROM_Base || !dramAddr) {
        LOGE("BKA_InflateCodeSegment: Invalid base pointers for inflation.");
        return;
    }

    uint8_t* srcStream = gN64_ROM_Base + romOffset;

    // Allocate 8MB default expansion workspace bound for code segments
    uint32_t expectedWorkspaceSize = 0x800000;

    // Call the updated pre-embedded offset function to extract directly into the DRAM workspace
    uint32_t decompressedBytes = decompress_rare_to_offset(
        srcStream,                          // src: Compressed payload pointer
        size,                               // src_size: Compressed size from manifest
        static_cast<uint8_t*>(dramAddr),    // out_buffer: Destination DRAM memory buffer
        0,                                  // out_offset: 0 relative to the start of the DRAM allocation
        expectedWorkspaceSize               // out_size: Expected upper bound for the workspace
    );

    if (decompressedBytes == 0) {
        LOGW("BKA_InflateCodeSegment: Decompression returned 0 bytes. Falling back to direct memory copy.");
        memcpy(dramAddr, srcStream, size);
    } else {
        LOGI("BKA_InflateCodeSegment: Successfully inflated %u bytes into DRAM destination %p.", decompressedBytes, dramAddr);
    }
}

extern "C" {

/**
 * Initializes the Resource Manager in Absolute Self-Building Mode and parses decompressed.us.v10.yaml.
 */
void ResourceMgr_Init(const char* assetDir) {
    if (!assetDir) {
        LOGE("ResourceMgr: Received an uninitialized null pointer for assetDir configuration.");
        return;
    }

    g_assetDir = assetDir;
    if (!g_assetDir.empty() && g_assetDir.back() != '/') {
        g_assetDir += "/";
    }

    LOGI("ResourceMgr: Activated in Absolute Self-Building Mode at location %s", g_assetDir.c_str());

    // --- Initialize decompression buffers FIRST ---
    char romPath[512];
    snprintf(romPath, sizeof(romPath), "%srom_base.bin", g_assetDir.c_str());
    if (!InitializeDecompressionBuffers(romPath)) {
        LOGE("ResourceMgr: FATAL ERROR - Failed to initialize decompression buffers!");
        return;
    }

    // --- Determine ROM size for bounds checking in HandleDma ---
    FILE* f = fopen(romPath, "rb");
    if (!f) {
        LOGE("ResourceMgr: FATAL ERROR - System fallback dependency file missing. Path: %s", romPath);
        CleanupDecompressionBuffers();
        return;
    }

    fseek(f, 0, SEEK_END);
    g_romSize = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (g_romSize == 0 || g_romSize > 128 * 1024 * 1024) {
        LOGE("ResourceMgr: FATAL ERROR - Invalid rom_base.bin size detected: %zu bytes", g_romSize);
        fclose(f);
        CleanupDecompressionBuffers();
        g_romSize = 0;
        return;
    }

    // gN64_ROM_Base is owned by lowlevel_bridge.cpp via mmap, but
    // ResourceMgr_Init runs BEFORE InitN64Registers, so it's typically null.
    // We allocate a fallback malloc buffer and load the ROM here so that
    // any code using gN64_ROM_Base directly (e.g., BKA_InflateCodeSegment)
    // has valid data. ResourceMgr_HandleDma now reads directly from
    // rom_base.bin on disk to avoid gN64_ROM_Base sync issues.
    if (gN64_ROM_Base == nullptr) {
        LOGI("ResourceMgr: gN64_ROM_Base not yet allocated by InitN64Registers. Allocating fallback buffer of %zu bytes.", g_romSize);
        gN64_ROM_Base = static_cast<uint8_t*>(malloc(g_romSize));
        if (!gN64_ROM_Base) {
            LOGE("ResourceMgr: FATAL ERROR - Memory pointer verification failed. Cannot parse ROM stream.");
            fclose(f);
            CleanupDecompressionBuffers();
            return;
        }
    } else {
        LOGI("ResourceMgr: Using pre-allocated gN64_ROM_Base at %p (from InitN64Registers).", gN64_ROM_Base);
    }

    LOGI("ResourceMgr: Streaming binary database targets into virtual memory locations...");
    size_t bytesRead = fread(gN64_ROM_Base, 1, g_romSize, f);
    LOGI("ResourceMgr: Verification validation sequence populated %zu bytes into ROM base block.", bytesRead);
    fclose(f);

    // --- Load splat YAML segment boundaries ---
    char manifestPath[512];
    snprintf(manifestPath, sizeof(manifestPath), "%sdecompressed.us.v10.yaml", g_assetDir.c_str());
    if (!parseSplatSegments(manifestPath, g_segments)) {
        snprintf(manifestPath, sizeof(manifestPath), "%smanifest_us.yaml", g_assetDir.c_str());
        if (!parseSplatSegments(manifestPath, g_segments)) {
            LOGW("ResourceMgr: Warning - Could not parse a splat YAML segment config at %s. DMA requests will fall back to whole-ROM bounds only.", manifestPath);
        }
    }

    if (!g_segments.empty()) {
        g_segments.back().end = static_cast<uint32_t>(g_romSize);
        LOGI("ResourceMgr: Parsed %zu top-level segments from %s (ROM size %zu bytes).",
             g_segments.size(), manifestPath, g_romSize);
    }

    // Signal that resources are ready
    BKA_SignalResourcesReady();
}

/**
 * Handles N64 DMA requests.
 *
 * Three paths:
 *   1. Pre-extracted asset files (asset_XXXXXXXX.bin)
 *   2. Host-pointer-to-host-pointer copies (for decompressor internal DMA)
 *   3. ROM reads from rom_base.bin (for PI cartridge DMA)
 *
 * Path 2 is needed because the decompressor (func_80000594 → func_80000618 in
 * src/done/rarezip.c) passes buffer pointers truncated to 32 bits as devAddr
 * for internal buffer-to-buffer copies. We reconstruct the full 64-bit pointer
 * using the upper bits of dramAddr.
 *
 * IMPORTANT: Path 2 only triggers when devAddr > 0x10000000 and is NOT in
 * cartridge space (0x10xxxxxx). This ensures ROM offsets like 0x00001050
 * (core1_rzip_ROM_START) correctly go to Path 3 instead of being incorrectly
 * treated as truncated host pointers.
 */
void ResourceMgr_HandleDma(void* dramAddr, uint32_t devAddr, uint32_t size) {
    if (!dramAddr || size == 0) {
        LOGE("ResourceMgr_HandleDma: Invalid parameters (dramAddr=%p, size=%u)", dramAddr, size);
        return;
    }

    char path[512];
    uint32_t relativeRomOffset = devAddr & 0x0FFFFFFF;

    // --- PATH 1: Try pre-extracted asset file ---
    snprintf(path, sizeof(path), "%sasset_%08X.bin", g_assetDir.c_str(), relativeRomOffset);
    FILE* f = fopen(path, "rb");
    if (!f) {
        snprintf(path, sizeof(path), "%sasset_%08X.bin", g_assetDir.c_str(), devAddr);
        f = fopen(path, "rb");
    }

    if (f) {
        size_t bytesRead = fread(dramAddr, 1, size, f);
        fclose(f);
        if (bytesRead < size) {
            memset(static_cast<uint8_t*>(dramAddr) + bytesRead, 0, size - bytesRead);
        }
        sched_yield();
        return;
    }

    // --- PATH 2: Host pointer → host pointer DMA ---
    // The decompressor (func_80000594 → func_80000618) passes buffer pointers
    // truncated to 32 bits as devAddr. Reconstruct the full 64-bit pointer
    // using the upper bits of dramAddr and do a direct memcpy.
    //
    // FIXED: Only trigger when devAddr looks like a truncated 64-bit host pointer
    // (value > 0x10000000 and NOT in N64 cartridge address space 0x10xxxxxx).
    // ROM offsets like 0x00001050 are < 0x10000000 and will correctly fall
    // through to PATH 3.
    uintptr_t dramVal = reinterpret_cast<uintptr_t>(dramAddr);
    if (dramVal > 0xFFFFFFFFULL && devAddr > 0x10000000 && (devAddr >> 24) != 0x10) {
        // dramAddr is a 64-bit host pointer. Try to interpret devAddr as
        // a truncated 64-bit host pointer by borrowing dramAddr's upper bits.
        uintptr_t srcPtr = (dramVal & 0xFFFFFFFF00000000ULL) | devAddr;

        // Quick sanity check: the reconstructed pointer should be in userspace
        // and reasonably close to dramAddr (same 4GB region).
        if (srcPtr > 0x1000 && srcPtr < 0x7FFFFFFFFFFFULL) {
            int64_t diff = static_cast<int64_t>(srcPtr) - static_cast<int64_t>(dramVal);
            if (diff > -0x100000000LL && diff < 0x100000000LL) {
                // Looks like a valid host pointer. Do a direct memcpy.
                memcpy(dramAddr, reinterpret_cast<void*>(srcPtr), size);
                sched_yield();
                return;
            }
        }
    }

    // --- PATH 3: ROM DMA via direct file read ---
    // Resolve the ROM offset from the N64 device address.
    uint32_t romOffset;
    if ((devAddr >> 24) == 0x10) {
        romOffset = relativeRomOffset;  // Cartridge address space (0x10000000+)
    } else if (devAddr < 0x10000000) {
        romOffset = devAddr;            // Direct ROM offset
    } else {
        // Not a ROM address or recognizable host pointer. Zero and bail.
        LOGW("ResourceMgr_HandleDma: Unrecognized devAddr=0x%08X dramAddr=%p size=%u. Zeroing.",
             devAddr, dramAddr, size);
        memset(dramAddr, 0, size);
        sched_yield();
        return;
    }

    // Open rom_base.bin and read directly from the file
    snprintf(path, sizeof(path), "%srom_base.bin", g_assetDir.c_str());
    f = fopen(path, "rb");
    if (!f) {
        LOGE("ResourceMgr_HandleDma: Cannot open %s! Zeroing %u bytes.", path, size);
        memset(dramAddr, 0, size);
        sched_yield();
        return;
    }

    // Get file size for bounds checking
    fseek(f, 0, SEEK_END);
    long fileSize = ftell(f);

    if (romOffset >= static_cast<uint32_t>(fileSize)) {
        LOGE("ResourceMgr_HandleDma: ROM offset 0x%X exceeds file size %ld. Zeroing.", romOffset, fileSize);
        memset(dramAddr, 0, size);
        fclose(f);
        sched_yield();
        return;
    }

    // Clamp size to available bytes
    uint32_t availableBytes = static_cast<uint32_t>(fileSize) - romOffset;
    if (size > availableBytes) {
        size = availableBytes;
    }

    // Seek and read directly from the ROM file
    fseek(f, romOffset, SEEK_SET);
    size_t bytesRead = fread(dramAddr, 1, size, f);
    fclose(f);

    if (bytesRead < size) {
        memset(static_cast<uint8_t*>(dramAddr) + bytesRead, 0, size - bytesRead);
    }

    sched_yield();
}

} // extern "C"