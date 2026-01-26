#include <jni.h>
#include <android/log.h>
#include <stdio.h>
#include <vector>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" {

void core1_loadOTR(int fd) {
    LOGI("Received ROM File Descriptor: %d", fd);
    
    // Use "rb" for read-binary. 
    // We must NOT close the FD here if Java's ParcelFileDescriptor is managing it,
    // but fdopen creates a stream that owns it.
    FILE* romFile = fdopen(fd, "rb");
    if (!romFile) {
        LOGE("Failed to open ROM from File Descriptor: %d", fd);
        return;
    }

    // Basic validation: Check file size
    fseek(romFile, 0, SEEK_END);
    long size = ftell(romFile);
    fseek(romFile, 0, SEEK_SET);

    LOGI("ROM File Size: %ld bytes", size);

    if (size < 1024 * 1024) { // Typical Z64 is 32MB+
        LOGE("File too small to be a valid ROM.");
        fclose(romFile);
        return;
    }

    // Dummy extraction loop: read first 4 bytes (The N64 Header)
    unsigned char header[4];
    if (fread(header, 1, 4, romFile) == 4) {
        LOGI("ROM Header: %02X %02X %02X %02X", header[0], header[1], header[2], header[3]);
    }

    LOGI("OTR generation stub complete.");
    
    // Note: In a production scenario, we'd pass this stream to the actual extraction engine.
    fclose(romFile);
}

}
