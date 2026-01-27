#include <jni.h>
#include <android/log.h>
#include <unistd.h>  // Added this to fix the 'usleep' error
#include <string>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

void run_otr_extraction(JNIEnv* env, jobject activity, int romFd) {
    LOGI("Starting OTR Extraction from ROM FD: %d", romFd);

    // Get reference to the Java progress update method
    jclass activityClass = env->GetObjectClass(activity);
    jmethodID updateMethod = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");

    if (updateMethod == nullptr) {
        LOGI("Error: Could not find updateOtrProgress method in MainActivity");
        return;
    }

    // --- PSEUDO EXTRACTION LOOP ---
    // This loop updates the UI for testing. 
    // Replace the internal logic with your actual manifest extraction code later.
    const int totalAssets = 100;
    for (int i = 1; i <= totalAssets; i++) {
        std::string fileName = "asset_" + std::to_string(i) + ".bin";
        jstring jFileName = env->NewStringUTF(fileName.c_str());

        // Call back to Java to update the ProgressBar and TextView
        env->CallVoidMethod(activity, updateMethod, i, jFileName);
        
        env->DeleteLocalRef(jFileName);

        // Simulate work (Replace with actual decompression/writing)
        usleep(50000); // 50ms per asset = 5 seconds total for 100 assets
    }

    LOGI("OTR Extraction Complete");
}

}
