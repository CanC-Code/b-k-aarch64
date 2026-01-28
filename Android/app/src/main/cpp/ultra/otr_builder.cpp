#include "otr_builder.h"
#include <unistd.h> // Required for pread
#include <android/log.h>

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {
    
    // Example logic:
    // 1. Cast manifestPtr to your Entry struct
    // 2. Loop until total bytes processed == manifestSize
    // 3. For each entry:
    //    pread(romFd, buffer, entry.size, entry.romOffset);
    
    // IMPORTANT: If you use read() or fread(), the file pointer moves. 
    // Since extraction is multi-threaded or non-linear, pread() is mandatory.
    
    __android_log_print(ANDROID_LOG_INFO, "OTR", "Builder started with FD: %d", romFd);
    
    // Dummy progress to verify the bridge is working:
    for(int i = 0; i <= 100; i += 10) {
        jstring name = env->NewStringUTF("Checking ROM...");
        env->CallVoidMethod(activity, progressMid, i, name);
        env->DeleteLocalRef(name);
        usleep(100000); // 100ms
    }
}
