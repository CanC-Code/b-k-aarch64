#include <jni.h>
#include <vector>
#include <cstdint>
#include <string>
#include "otr_builder.h"

extern "C" {

void extract_assets_to_otr(JNIEnv* env, jobject activity, const uint8_t* romData, size_t size) {
    // 1. Get the Java class and the method ID for the callback
    jclass clazz = env->GetObjectClass(activity);
    jmethodID updateMethod = env->GetMethodID(clazz, "updateOtrProgress", "(ILjava/lang/String;)V");

    int version = detect_rom_version(romData, size);
    if (version == -1) return;

    // 2. Simulated extraction loop
    // In your real code, this would loop through your manifest entries
    int totalFiles = 500; 
    for (int i = 0; i <= totalFiles; i++) {
        
        // --- REAL EXTRACTION LOGIC GOES HERE ---
        // Example: decompress_rare_asset(input, output);
        
        // 3. Update the UI every 5 files
        if (i % 5 == 0 || i == totalFiles) {
            int percentage = (i * 100) / totalFiles;
            jstring fileName = env->NewStringUTF("Asset_Chunk.bin");
            
            env->CallVoidMethod(activity, updateMethod, percentage, fileName);
            
            env->DeleteLocalRef(fileName); // Clean up local JNI references
        }
    }
}

int detect_rom_version(const uint8_t* romData, size_t size) {
    if (size < 0x40) return -1;
    if (romData[0x3B] == 'E') return 0; // US
    if (romData[0x3B] == 'P') return 1; // PAL
    return -1;
}

} // extern "C"
