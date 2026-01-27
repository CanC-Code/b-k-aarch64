#include <jni.h>
#include <android/log.h>
#include <string>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

void run_otr_extraction(JNIEnv* env, jobject activity, int romFd) {
    LOGI("Starting OTR Extraction from ROM FD: %d", romFd);

    // Get reference to the Java progress update method
    jclass activityClass = env->GetObjectClass(activity);
    jmethodID updateMethod = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");

    // --- PSEUDO EXTRACTION LOOP ---
    // You will replace this with your actual manifest-based extraction logic.
    // This loop demonstrates how the UI updates work.
    const int totalAssets = 100;
    for (int i = 1; i <= totalAssets; i++) {
        std::string fileName = "asset_" + std::to_string(i) + ".bin";
        jstring jFileName = env->NewStringUTF(fileName.c_str());

        // Update the Progress Bar in Java
        env->CallVoidMethod(activity, updateMethod, i, jFileName);
        
        env->DeleteLocalRef(jFileName);

        // Simulate work (Replace with actual decompression/writing)
        usleep(50000); // 50ms per asset
    }

    LOGI("OTR Extraction Complete");
}

}
