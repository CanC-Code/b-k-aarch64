// File: otr_builder.cpp
// Purpose: Deterministic ROM → OTR builder

#include "ultra/otr_builder.h"

#include <vector>
#include <cstdint>
#include <string>
#include <cstring>
#include <memory>

#include "ultra/rom_detector.h"
#include "ultra/otr_archive.h"
#include "ultra/asset_builder.h"

bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR
) {
    if (!romData || romSize == 0) {
        return false;
    }

    // --- Detect ROM ---
    RomInfo info{};
    if (!detectRom(romData, romSize, info)) {
        return false;
    }

    // --- Create OTR archive ---
    OTRArchive archive;
    archive.setGameId(info.gameId);
    archive.setRegion(info.region);

    // --- Build assets ---
    if (!buildAssetsFromRom(
            romData,
            romSize,
            info,
            archive
        )) {
        return false;
    }

    // --- Serialize OTR ---
    return archive.serialize(outOTR);
}