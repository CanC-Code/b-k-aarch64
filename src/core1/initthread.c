#include <ultra64.h>
#include <PRinternal/macros.h>
#include "core1/core1.h"
#include "functions.h"
#include "variables.h"

STACK(sInitThreadStack, 512); // Size based on the previous symbol's address
OSThread sInitThread;

void initThread_create(void) {
    osCreateThread(&sInitThread, INITTHREAD_ID, initThread_entry, NULL, STACK_START(sInitThreadStack), OS_PRIORITY_IDLE);
    osStartThread(&sInitThread);
}

void initThread_entry(void *arg) {
    parallel_init();
    mainThread_create();
    osStartThread(mainThread_get());
    while (1);
}
