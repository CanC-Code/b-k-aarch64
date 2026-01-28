#include "otr_builder.h"
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <string>

static JavaVM* g_vm = nullptr;

void otr_builder_set_jvm(JavaVM* vm) {
    g_vm = vm;
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {
    
    __android_log_print(ANDROID_LOG_INFO, "OTR", "Builder started. Manifest size: %u bytes", manifestSize);

    // This is where your actual extraction loop goes. 
    // For now, we simulate progress to ensure the UI unfreezes.
    
    const int total_steps = 20;
    for (int i = 0; i <= total_steps; i++) {
        int percent = (i * 100) / total_steps;
        
        // Update the UI via the callback
        std::string status = "Extracting asset " + std::to_string(i) + "...";
        jstring jStatus = env->NewStringUTF(status.c_str());
        
        env->CallVoidMethod(activity, progressMid, percent, jStatus);
        
        env->DeleteLocalRef(jStatus);
        
        // Use usleep for a small delay so the UI can actually show progress
        usleep(50000); 
    }

    __android_log_print(ANDROID_LOG_INFO, "OTR", "Generation Complete");
}
