#include <ultra64.h>
#include <PRinternal/macros.h>
#include "core1/core1.h"
#include "functions.h"

static OSMesgQueue sDefragThreadResumeSyncQueue;
static OSMesg      sDefragThreadResumeSyncMesg;
static OSMesgQueue sDefragThreadPauseSyncQueue;
static OSMesg      sDefragThreadPauseSyncMesg;
static OSThread    sDefragThread;
STACK(sDefragThreadStack, 2048);

void defragthread_init(void) {
    osCreateMesgQueue(&sDefragThreadResumeSyncQueue, &sDefragThreadResumeSyncMesg, 1);
    osCreateMesgQueue(&sDefragThreadPauseSyncQueue, &sDefragThreadPauseSyncMesg, 1);
    osCreateThread(&sDefragThread, DEFRAGMANAGER_THREAD_ID, defragthread_entry, NULL, STACK_START(sDefragThreadStack), DEFRAGMANAGER_THREAD_PRI);
    osStartThread(&sDefragThread);
}

void defragthread_free(void) {
    osStopThread(&sDefragThread);
    osDestroyThread(&sDefragThread);
}

void defragthread_resume(void) {
    if (func_8023E000() == 3) {
        osSendMesg(&sDefragThreadResumeSyncQueue, NULL, OS_MESG_BLOCK);
    }
}

void defragthread_pause(void) {
    if (func_8023E000() == 3) {
        osSendMesg(&sDefragThreadPauseSyncQueue, NULL, OS_MESG_BLOCK);
    }
}

void defragthread_setPriority(OSPri pri) {
    if (func_8023E000() == 3) {
        osSetThreadPri(&sDefragThread, pri);
    }
}

void defragthread_entry(void *arg) {
    s32 defrag_flag;

    do {
        osRecvMesg(&sDefragThreadResumeSyncQueue, NULL, OS_MESG_BLOCK);
        if (sDefragThreadPauseSyncQueue.validCount == 0) {
            do {
                defrag_flag = game_defrag();
            } while ((sDefragThreadPauseSyncQueue.validCount == 0) && defrag_flag);
        }
        osRecvMesg(&sDefragThreadPauseSyncQueue, NULL, OS_MESG_BLOCK);
    } while(TRUE);
}
