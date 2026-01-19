#include <jni.h>
#include "otr_generator.hpp"
#include "otr_assets.hpp"
#include <vector>
#include <cstdint>
#include <sys/stat.h> // for mkdir

extern std::vector<uint8_t> g_romData; // loaded ROM in memory
extern float g_progress;

extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_generateOTR(JNIEnv* env, jclass, jbyteArray rom) {
    // Copy ROM data from Java
    jsize romSize = env->GetArrayLength(rom);
    g_romData.resize(romSize);
    env->GetByteArrayRegion(rom, 0, romSize, reinterpret_cast<jbyte*>(g_romData.data()));

    // Create output directory if needed
    mkdir("/data/data/com.bkawrapper/files", 0755);

    OTRGenerator otrGen;

    // Load embedded YAML
    otrGen.loadEmbeddedYAML("decompressed.pal.yaml", embedded_pal_yaml, embedded_pal_yaml_size);
    otrGen.loadEmbeddedYAML("decompressed.us.v10.yaml", embedded_us_yaml, embedded_us_yaml_size);

    // Generate OTR from ROM
    bool success = otrGen.generate(
        g_romData.data(),
        g_romData.size(),
        [](float progress) { g_progress = progress; }
    );

    return success ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getProgress(JNIEnv*, jclass) {
    return g_progress;
}