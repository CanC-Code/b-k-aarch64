// Android/app/src/main/cpp/ultra/otr_builder.cpp
#include "assets_manifest.h"
#include "rare_decompression.h"
#include <vector>
#include <fcntl.h>
#include <unistd.h>

void run_otr_generation(int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    for (uint32_t i = 0; i < header->entryCount; i++) {
        AssetEntry& asset = entries[i];
        if (asset.type == ASSET_TYPE_SKIP) continue;

        [span_10](start_span)[span_11](start_span)// Logic from splat_inputs.py: Seek to ROM position[span_10](end_span)[span_11](end_span)
        lseek(romFd, asset.romOffset, SEEK_SET);
        std::vector<uint8_t> compBuffer(asset.compSize);
        read(romFd, compBuffer.data(), asset.compSize);

        [span_12](start_span)// Logic from rareunzip.py: Decompress asset[span_12](end_span)
        uint32_t actualSize = 0;
        uint8_t* decompData = decompress_rare_asset(compBuffer.data(), &actualSize);

        if (decompData) {
            char fullPath[256];
            snprintf(fullPath, sizeof(fullPath), "%s/%s", outDirPath, asset.name);
            int outFd = open(fullPath, O_WRONLY | O_CREAT | O_TRUNC, 0666);
            write(outFd, decompData, actualSize);
            close(outFd);
            free(decompData);
        }
    }
}
