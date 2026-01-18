// File: otr_builder.cpp
// Purpose: Deterministic ROM → OTR builder (self-contained)

#include "ultra/otr_builder.h"

#include <vector>
#include <cstdint>
#include <string>
#include <cstring>

// Core OTR pipeline
#include "ultra/otr_archive.h"
#include "ultra/asset_builder.h"

// ------------------------------------------------------------
// Inline ROM detection (no external headers)
// ------------------------------------------------------------

enum class BKRegion {
    NTSC,
    PAL,
    UNKNOWN
};

struct RomInfo {
    std::string gameId;
    BKRegion region;
    size_t romSize;
};

// N64 ROMs are usually byte-swapped or big-endian.
// BK retail ROM size is exactly 16 MB.
static bool detectBKRom(
    const uint8_t* romData,
    size_t romSize,
    RomInfo& outInfo
) {
    if (!romData || romSize == 0) {
        return false;
    }

    // Banjo-Kazooie retail ROM is exactly 16MB
    constexpr size_t BK_ROM_SIZE = 16 * 1024 * 1024;
    if (romSize != BK_ROM_SIZE) {
        return false;
    }

    // N64 header magic (big-endian)
    // 0x80371240 = standard big-endian N64 ROM
    uint32_t magic =
        (romData[0] << 24) |
        (romData[1] << 16) |
        (romData[2] << 8)  |
        (romData[3]);

    if (magic != 0x80371240 &&
        magic != 0x37804012 && // byte-swapped
        magic != 0x40123780) { // little-endian
        return false;
    }

    // Game ID is stored at 0x3B–0x3E in ASCII
    // Example: "NBKE" (NTSC), "NBKP" (PAL)
    char gameId[5] = {};
    gameId[0] = static_cast<char>(romData[0x3B]);
    gameId[1] = static_cast<char>(romData[0x3C]);
    gameId[2] = static_cast<char>(romData[0x3D]);
    gameId[3] = static_cast<char>(romData[0x3E]);
    gameId[4] = '\0';

    BKRegion region = BKRegion::UNKNOWN;

    if (gameId[3] == 'E') {
        region = BKRegion::NTSC;
    } else if (gameId[3] == 'P') {
        region = BKRegion::PAL;
    }

    if (region == BKRegion::UNKNOWN) {
        return false;
    }

    outInfo.gameId  = gameId;
    outInfo.region  = region;
    outInfo.romSize = romSize;

    return true;
}

// ------------------------------------------------------------
// Public OTR builder entry point
// ------------------------------------------------------------

bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR
) {
    outOTR.clear();

    if (!romData || romSize == 0) {
        return false;
    }

    // --- Detect ROM (inline, deterministic) ---
    RomInfo info{};
    if (!detectBKRom(romData, romSize, info)) {
        return false;
    }

    // --- Create OTR archive ---
    OTRArchive archive;
    archive.setGameId(info.gameId);

    switch (info.region) {
        case BKRegion::NTSC:
            archive.setRegion("NTSC");
            break;
        case BKRegion::PAL:
            archive.setRegion("PAL");
            break;
        default:
            return false;
    }

    // --- Build assets ---
    if (!buildAssetsFromRom(
            romData,
            romSize,
            info.gameId,
            archive
        )) {
        return false;
    }

    // --- Serialize OTR ---
    return archive.serialize(outOTR);
}