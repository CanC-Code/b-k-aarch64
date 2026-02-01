2026-02-01T17:41:34.0759209Z ##[group]Run GRADLEW_PATH=$(find . -name gradlew)
GRADLEW_PATH=$(find . -name gradlew)
chmod +x "$GRADLEW_PATH"
cd $(dirname "$GRADLEW_PATH")
# CLEAN is vital here to re-link your new icons
./gradlew clean assembleDebug --no-daemon --stacktrace
shell: /usr/bin/bash -e {0}
env:
  JAVA_HOME: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
  JAVA_HOME_17_X64: /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17.0.18-8/x64
  pythonLocation: /opt/hostedtoolcache/Python/3.12.12/x64
  PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.12/x64/lib/pkgconfig
  Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
  Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
  Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.12/x64
  LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.12/x64/lib

Welcome to Gradle 8.4!

Here are the highlights of this release:
 - Compiling and testing with Java 21
 - Faster Java compilation on Windows
 - Role focused dependency configurations creation

For more details see https://docs.gradle.org/8.4/release-notes.html

To honour the JVM settings for this build a single-use Daemon process will be forked. For more on this, please refer to https://docs.gradle.org/8.4/userguide/gradle_daemon.html#sec:disabling_the_daemon in the Gradle documentation.
Daemon will be stopped at the end of the build 

> Configure project :Android:app
Checking the license for package NDK (Side by side) 25.1.8937393 in /usr/local/lib/android/sdk/licenses
License for package NDK (Side by side) 25.1.8937393 accepted.
Preparing "Install NDK (Side by side) 25.1.8937393 v.25.1.8937393".
"Install NDK (Side by side) 25.1.8937393 v.25.1.8937393" ready.
Installing NDK (Side by side) 25.1.8937393 in /usr/local/lib/android/sdk/ndk/25.1.8937393
"Install NDK (Side by side) 25.1.8937393 v.25.1.8937393" complete.
"Install NDK (Side by side) 25.1.8937393 v.25.1.8937393" finished.

> Task :Android:app:externalNativeBuildCleanDebug
> Task :Android:app:externalNativeBuildCleanRelease
> Task :Android:app:clean UP-TO-DATE
> Task :Android:app:preBuild UP-TO-DATE
> Task :Android:app:preDebugBuild UP-TO-DATE
> Task :Android:app:mergeDebugNativeDebugMetadata NO-SOURCE
> Task :Android:app:javaPreCompileDebug
> Task :Android:app:generateDebugResValues
> Task :Android:app:checkDebugAarMetadata
> Task :Android:app:mapDebugSourceSetPaths
> Task :Android:app:generateDebugResources
> Task :Android:app:packageDebugResources
> Task :Android:app:createDebugCompatibleScreenManifests
> Task :Android:app:extractDeepLinksDebug
> Task :Android:app:parseDebugLocalResources
> Task :Android:app:processDebugMainManifest
> Task :Android:app:mergeDebugResources
> Task :Android:app:processDebugManifest
> Task :Android:app:mergeDebugShaders
> Task :Android:app:compileDebugShaders NO-SOURCE
> Task :Android:app:generateDebugAssets UP-TO-DATE
> Task :Android:app:mergeDebugAssets
> Task :Android:app:desugarDebugFileDependencies
> Task :Android:app:compressDebugAssets
> Task :Android:app:processDebugJavaRes NO-SOURCE
> Task :Android:app:processDebugManifestForPackage
> Task :Android:app:checkDebugDuplicateClasses
> Task :Android:app:mergeDebugJavaResource
> Task :Android:app:mergeLibDexDebug
> Task :Android:app:processDebugResources

> Task :Android:app:configureCMakeDebug[arm64-v8a]
Checking the license for package CMake 3.22.1 in /usr/local/lib/android/sdk/licenses
License for package CMake 3.22.1 accepted.
Preparing "Install CMake 3.22.1 v.3.22.1".
"Install CMake 3.22.1 v.3.22.1" ready.
Installing CMake 3.22.1 in /usr/local/lib/android/sdk/cmake/3.22.1
"Install CMake 3.22.1 v.3.22.1" complete.
"Install CMake 3.22.1 v.3.22.1" finished.

> Task :Android:app:mergeExtDexDebug

> Task :Android:app:compileDebugJavaWithJavac
Note: Some input files use or override a deprecated API.
Note: Recompile with -Xlint:deprecation for details.

> Task :Android:app:dexBuilderDebug
> Task :Android:app:mergeDebugGlobalSynthetics
> Task :Android:app:mergeProjectDexDebug

> Task :Android:app:buildCMakeDebug[arm64-v8a] FAILED
C/C++: ninja: Entering directory `/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a'
C/C++: /usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/bin/clang --target=aarch64-none-linux-android26 --sysroot=/usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/sysroot -D_LANGUAGE_C -Dbkawrapper_EXPORTS -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/ultra -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L/PR -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core1 -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core2 -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -D_FORTIFY_SOURCE=2 -Wformat -Werror=format-security  -fno-limit-debug-info  -fPIC -w -fcommon -O3 -MD -MT CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -MF CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o.d -o CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -c /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected parameter declarator
C/C++:     mapSpecificFlags_set(0x10, 0);
C/C++:                          ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected ')'
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:25: note: to match this '('
C/C++:     mapSpecificFlags_set(0x10, 0);
C/C++:                         ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:5: error: conflicting types for 'mapSpecificFlags_set'
C/C++:     mapSpecificFlags_set(0x10, 0);

C/C++:     ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/functions.h:458:6: note: previous declaration is here
C/C++: void mapSpecificFlags_set(s32, s32);
C/C++:      ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:30:5: error: expected identifier or '('
C/C++:     if(actPtr->state == 4){
C/C++:     ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:33:5: error: expected identifier or '('
C/C++:     else{
C/C++:     ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:36:1: error: extraneous closing brace ('}')
C/C++: }
C/C++: ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:58:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
C/C++:             gcdialog_showDialog(ASSET_C81_DIALOG_YELLOW_FLIBBITS_MEET, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
C/C++:                                                                                                           ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:61:113: error: use of undeclared identifier '__chFrogMinigame_textCallback'
C/C++:                 gcdialog_showDialog(ASSET_C83_DIALOG_YELLOW_FLIBBITS_RETURN, 0x4, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
C/C++:                                                                                                                 ^
C/C++: /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:95:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
C/C++:         gcdialog_showDialog(ASSET_C82_DIALOG_YELLOW_FLIBBITS_COMPLETE, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
C/C++:                                                                                                           ^
FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':Android:app:buildCMakeDebug[arm64-v8a]'.
> com.android.ide.common.process.ProcessException: ninja: Entering directory `/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a'
  [1/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/bss_pad.c.o
  [2/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/bigalligator.c.o
  [3/866] Building C object CMakeFiles/bkawrapper.dir/src/GV/ch/histup.c.o
  [4/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/code_2270.c.o
  [5/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o
  FAILED: CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o 
  /usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/bin/clang --target=aarch64-none-linux-android26 --sysroot=/usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/sysroot -D_LANGUAGE_C -Dbkawrapper_EXPORTS -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/ultra -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L/PR -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core1 -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core2 -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -D_FORTIFY_SOURCE=2 -Wformat -Werror=format-security  -fno-limit-debug-info  -fPIC -w -fcommon -O3 -MD -MT CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -MF CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o.d -o CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -c /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected parameter declarator
      mapSpecificFlags_set(0x10, 0);
                           ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected ')'
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:25: note: to match this '('
      mapSpecificFlags_set(0x10, 0);
                          ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:5: error: conflicting types for 'mapSpecificFlags_set'
      mapSpecificFlags_set(0x10, 0);
      ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/functions.h:458:6: note: previous declaration is here
C/C++: 9 errors generated.
  void mapSpecificFlags_set(s32, s32);
       ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:30:5: error: expected identifier or '('
      if(actPtr->state == 4){
      ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:33:5: error: expected identifier or '('
      else{
      ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:36:1: error: extraneous closing brace ('}')
  }
  ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:58:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
              gcdialog_showDialog(ASSET_C81_DIALOG_YELLOW_FLIBBITS_MEET, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                            ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:61:113: error: use of undeclared identifier '__chFrogMinigame_textCallback'
                  gcdialog_showDialog(ASSET_C83_DIALOG_YELLOW_FLIBBITS_RETURN, 0x4, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                                  ^
  /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:95:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
          gcdialog_showDialog(ASSET_C82_DIALOG_YELLOW_FLIBBITS_COMPLETE, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                            ^
  9 errors generated.
  [6/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/croctus.c.o
  [7/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/leafboat.c.o
  [8/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/flibbit.c.o
  [9/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/mudhut.c.o
  [10/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/mrvile.c.o
  ninja: build stopped: subcommand failed.
  
  C++ build system [build] failed while executing:
      /usr/local/lib/android/sdk/cmake/3.22.1/bin/ninja \
        -C \
        /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a \
        bkawrapper
    from /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app

* Try:
> Run with --info or --debug option to get more log output.
> Run with --scan to get full insights.
> Get more help at https://help.gradle.org.

* Exception is:
org.gradle.api.tasks.TaskExecutionException: Execution failed for task ':Android:app:buildCMakeDebug[arm64-v8a]'.
	at org.gradle.api.internal.tasks.execution.ExecuteActionsTaskExecuter.lambda$executeIfValid$1(ExecuteActionsTaskExecuter.java:148)
	at org.gradle.internal.Try$Failure.ifSuccessfulOrElse(Try.java:282)
	at org.gradle.api.internal.tasks.execution.ExecuteActionsTaskExecuter.executeIfValid(ExecuteActionsTaskExecuter.java:146)
	at org.gradle.api.internal.tasks.execution.ExecuteActionsTaskExecuter.execute(ExecuteActionsTaskExecuter.java:134)
	at org.gradle.api.internal.tasks.execution.FinalizePropertiesTaskExecuter.execute(FinalizePropertiesTaskExecuter.java:46)
	at org.gradle.api.internal.tasks.execution.ResolveTaskExecutionModeExecuter.execute(ResolveTaskExecutionModeExecuter.java:51)
	at org.gradle.api.internal.tasks.execution.SkipTaskWithNoActionsExecuter.execute(SkipTaskWithNoActionsExecuter.java:57)
	at org.gradle.api.internal.tasks.execution.SkipOnlyIfTaskExecuter.execute(SkipOnlyIfTaskExecuter.java:74)
	at org.gradle.api.internal.tasks.execution.CatchExceptionTaskExecuter.execute(CatchExceptionTaskExecuter.java:36)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter$1.executeTask(EventFiringTaskExecuter.java:77)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter$1.call(EventFiringTaskExecuter.java:55)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter$1.call(EventFiringTaskExecuter.java:52)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:204)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:199)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:66)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:157)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:53)
	at org.gradle.internal.operations.DefaultBuildOperationExecutor.call(DefaultBuildOperationExecutor.java:78)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter.execute(EventFiringTaskExecuter.java:52)
	at org.gradle.execution.plan.LocalTaskNodeExecutor.execute(LocalTaskNodeExecutor.java:42)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$InvokeNodeExecutorsAction.execute(DefaultTaskExecutionGraph.java:331)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$InvokeNodeExecutorsAction.execute(DefaultTaskExecutionGraph.java:318)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$BuildOperationAwareExecutionAction.lambda$execute$0(DefaultTaskExecutionGraph.java:314)
	at org.gradle.internal.operations.CurrentBuildOperationRef.with(CurrentBuildOperationRef.java:80)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$BuildOperationAwareExecutionAction.execute(DefaultTaskExecutionGraph.java:314)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$BuildOperationAwareExecutionAction.execute(DefaultTaskExecutionGraph.java:303)
	at org.gradle.execution.plan.DefaultPlanExecutor$ExecutorWorker.execute(DefaultPlanExecutor.java:463)
	at org.gradle.execution.plan.DefaultPlanExecutor$ExecutorWorker.run(DefaultPlanExecutor.java:380)
	at org.gradle.execution.plan.DefaultPlanExecutor.process(DefaultPlanExecutor.java:116)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph.executeWithServices(DefaultTaskExecutionGraph.java:138)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph.execute(DefaultTaskExecutionGraph.java:123)
	at org.gradle.execution.SelectedTaskExecutionAction.execute(SelectedTaskExecutionAction.java:35)
	at org.gradle.execution.DryRunBuildExecutionAction.execute(DryRunBuildExecutionAction.java:51)
	at org.gradle.execution.BuildOperationFiringBuildWorkerExecutor$ExecuteTasks.call(BuildOperationFiringBuildWorkerExecutor.java:54)
	at org.gradle.execution.BuildOperationFiringBuildWorkerExecutor$ExecuteTasks.call(BuildOperationFiringBuildWorkerExecutor.java:43)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:204)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:199)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:66)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:157)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:53)
	at org.gradle.internal.operations.DefaultBuildOperationExecutor.call(DefaultBuildOperationExecutor.java:78)
	at org.gradle.execution.BuildOperationFiringBuildWorkerExecutor.execute(BuildOperationFiringBuildWorkerExecutor.java:40)
	at org.gradle.internal.build.DefaultBuildLifecycleController.lambda$executeTasks$10(DefaultBuildLifecycleController.java:313)
	at org.gradle.internal.model.StateTransitionController.doTransition(StateTransitionController.java:266)
	at org.gradle.internal.model.StateTransitionController.lambda$tryTransition$8(StateTransitionController.java:177)
	at org.gradle.internal.work.DefaultSynchronizer.withLock(DefaultSynchronizer.java:44)
	at org.gradle.internal.model.StateTransitionController.tryTransition(StateTransitionController.java:177)
	at org.gradle.internal.build.DefaultBuildLifecycleController.executeTasks(DefaultBuildLifecycleController.java:304)
	at org.gradle.internal.build.DefaultBuildWorkGraphController$DefaultBuildWorkGraph.runWork(DefaultBuildWorkGraphController.java:220)
	at org.gradle.internal.work.DefaultWorkerLeaseService.withLocks(DefaultWorkerLeaseService.java:264)
	at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:128)
	at org.gradle.composite.internal.DefaultBuildController.doRun(DefaultBuildController.java:181)
	at org.gradle.composite.internal.DefaultBuildController.access$000(DefaultBuildController.java:50)
	at org.gradle.composite.internal.DefaultBuildController$BuildOpRunnable.lambda$run$0(DefaultBuildController.java:198)
	at org.gradle.internal.operations.CurrentBuildOperationRef.with(CurrentBuildOperationRef.java:80)
	at org.gradle.composite.internal.DefaultBuildController$BuildOpRunnable.run(DefaultBuildController.java:198)
	at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:64)
	at org.gradle.internal.concurrent.AbstractManagedExecutor$1.run(AbstractManagedExecutor.java:47)
Caused by: org.gradle.internal.UncheckedException: com.android.ide.common.process.ProcessException: ninja: Entering directory `/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a'
[1/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/bss_pad.c.o
[2/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/bigalligator.c.o
[3/866] Building C object CMakeFiles/bkawrapper.dir/src/GV/ch/histup.c.o
[4/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/code_2270.c.o
[5/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o
FAILED: CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o 
/usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/bin/clang --target=aarch64-none-linux-android26 --sysroot=/usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/sysroot -D_LANGUAGE_C -Dbkawrapper_EXPORTS -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/ultra -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L/PR -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core1 -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core2 -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -D_FORTIFY_SOURCE=2 -Wformat -Werror=format-security  -fno-limit-debug-info  -fPIC -w -fcommon -O3 -MD -MT CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -MF CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o.d -o CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -c /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected parameter declarator
    mapSpecificFlags_set(0x10, 0);
                         ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected ')'
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:25: note: to match this '('
    mapSpecificFlags_set(0x10, 0);
                        ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:5: error: conflicting types for 'mapSpecificFlags_set'
    mapSpecificFlags_set(0x10, 0);
    ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/functions.h:458:6: note: previous declaration is here
void mapSpecificFlags_set(s32, s32);
     ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:30:5: error: expected identifier or '('
    if(actPtr->state == 4){
    ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:33:5: error: expected identifier or '('
    else{
    ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:36:1: error: extraneous closing brace ('}')
}
^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:58:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
            gcdialog_showDialog(ASSET_C81_DIALOG_YELLOW_FLIBBITS_MEET, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                          ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:61:113: error: use of undeclared identifier '__chFrogMinigame_textCallback'
                gcdialog_showDialog(ASSET_C83_DIALOG_YELLOW_FLIBBITS_RETURN, 0x4, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                                ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:95:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
        gcdialog_showDialog(ASSET_C82_DIALOG_YELLOW_FLIBBITS_COMPLETE, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                          ^
9 errors generated.
[6/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/croctus.c.o
[7/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/leafboat.c.o
[8/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/flibbit.c.o
[9/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/mudhut.c.o
[10/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/mrvile.c.o
ninja: build stopped: subcommand failed.

C++ build system [build] failed while executing:
    /usr/local/lib/android/sdk/cmake/3.22.1/bin/ninja \
      -C \
      /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a \
      bkawrapper
  from /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app
	at org.gradle.internal.UncheckedException.throwAsUncheckedException(UncheckedException.java:68)
	at org.gradle.internal.UncheckedException.throwAsUncheckedException(UncheckedException.java:41)
	at org.gradle.internal.reflect.JavaMethod.invoke(JavaMethod.java:128)
	at org.gradle.api.internal.project.taskfactory.StandardTaskAction.doExecute(StandardTaskAction.java:58)
	at org.gradle.api.internal.project.taskfactory.StandardTaskAction.execute(StandardTaskAction.java:51)
	at org.gradle.api.internal.project.taskfactory.StandardTaskAction.execute(StandardTaskAction.java:29)
	at org.gradle.api.internal.tasks.execution.TaskExecution$3.run(TaskExecution.java:248)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$1.execute(DefaultBuildOperationRunner.java:29)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$1.execute(DefaultBuildOperationRunner.java:26)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:66)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:157)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.run(DefaultBuildOperationRunner.java:47)
	at org.gradle.internal.operations.DefaultBuildOperationExecutor.run(DefaultBuildOperationExecutor.java:73)
	at org.gradle.api.internal.tasks.execution.TaskExecution.executeAction(TaskExecution.java:233)
	at org.gradle.api.internal.tasks.execution.TaskExecution.executeActions(TaskExecution.java:216)
	at org.gradle.api.internal.tasks.execution.TaskExecution.executeWithPreviousOutputFiles(TaskExecution.java:199)
	at org.gradle.api.internal.tasks.execution.TaskExecution.execute(TaskExecution.java:166)
	at org.gradle.internal.execution.steps.ExecuteStep.executeInternal(ExecuteStep.java:105)
	at org.gradle.internal.execution.steps.ExecuteStep.access$000(ExecuteStep.java:44)
	at org.gradle.internal.execution.steps.ExecuteStep$1.call(ExecuteStep.java:59)
	at org.gradle.internal.execution.steps.ExecuteStep$1.call(ExecuteStep.java:56)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:204)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:199)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:66)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:157)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:53)
	at org.gradle.internal.operations.DefaultBuildOperationExecutor.call(DefaultBuildOperationExecutor.java:78)
	at org.gradle.internal.execution.steps.ExecuteStep.execute(ExecuteStep.java:56)
	at org.gradle.internal.execution.steps.ExecuteStep.execute(ExecuteStep.java:44)
	at org.gradle.internal.execution.steps.RemovePreviousOutputsStep.execute(RemovePreviousOutputsStep.java:67)
	at org.gradle.internal.execution.steps.RemovePreviousOutputsStep.execute(RemovePreviousOutputsStep.java:37)
	at org.gradle.internal.execution.steps.CancelExecutionStep.execute(CancelExecutionStep.java:41)
	at org.gradle.internal.execution.steps.TimeoutStep.executeWithoutTimeout(TimeoutStep.java:74)
	at org.gradle.internal.execution.steps.TimeoutStep.execute(TimeoutStep.java:55)
	at org.gradle.internal.execution.steps.CreateOutputsStep.execute(CreateOutputsStep.java:50)
	at org.gradle.internal.execution.steps.CreateOutputsStep.execute(CreateOutputsStep.java:28)
	at org.gradle.internal.execution.steps.CaptureStateAfterExecutionStep.executeDelegateBroadcastingChanges(CaptureStateAfterExecutionStep.java:100)
	at org.gradle.internal.execution.steps.CaptureStateAfterExecutionStep.execute(CaptureStateAfterExecutionStep.java:72)
	at org.gradle.internal.execution.steps.CaptureStateAfterExecutionStep.execute(CaptureStateAfterExecutionStep.java:50)
	at org.gradle.internal.execution.steps.ResolveInputChangesStep.execute(ResolveInputChangesStep.java:40)
	at org.gradle.internal.execution.steps.ResolveInputChangesStep.execute(ResolveInputChangesStep.java:29)
	at org.gradle.internal.execution.steps.BuildCacheStep.executeWithoutCache(BuildCacheStep.java:179)
	at org.gradle.internal.execution.steps.BuildCacheStep.lambda$execute$1(BuildCacheStep.java:70)
	at org.gradle.internal.Either$Right.fold(Either.java:175)
	at org.gradle.internal.execution.caching.CachingState.fold(CachingState.java:59)
	at org.gradle.internal.execution.steps.BuildCacheStep.execute(BuildCacheStep.java:68)
	at org.gradle.internal.execution.steps.BuildCacheStep.execute(BuildCacheStep.java:46)
	at org.gradle.internal.execution.steps.StoreExecutionStateStep.execute(StoreExecutionStateStep.java:36)
	at org.gradle.internal.execution.steps.StoreExecutionStateStep.execute(StoreExecutionStateStep.java:25)
	at org.gradle.internal.execution.steps.RecordOutputsStep.execute(RecordOutputsStep.java:36)
	at org.gradle.internal.execution.steps.RecordOutputsStep.execute(RecordOutputsStep.java:22)
	at org.gradle.internal.execution.steps.SkipUpToDateStep.executeBecause(SkipUpToDateStep.java:91)
	at org.gradle.internal.execution.steps.SkipUpToDateStep.lambda$execute$2(SkipUpToDateStep.java:55)
	at org.gradle.internal.execution.steps.SkipUpToDateStep.execute(SkipUpToDateStep.java:55)
	at org.gradle.internal.execution.steps.SkipUpToDateStep.execute(SkipUpToDateStep.java:37)
	at org.gradle.internal.execution.steps.ResolveChangesStep.execute(ResolveChangesStep.java:65)
	at org.gradle.internal.execution.steps.ResolveChangesStep.execute(ResolveChangesStep.java:36)
	at org.gradle.internal.execution.steps.legacy.MarkSnapshottingInputsFinishedStep.execute(MarkSnapshottingInputsFinishedStep.java:37)
	at org.gradle.internal.execution.steps.legacy.MarkSnapshottingInputsFinishedStep.execute(MarkSnapshottingInputsFinishedStep.java:27)
	at org.gradle.internal.execution.steps.ResolveCachingStateStep.execute(ResolveCachingStateStep.java:77)
	at org.gradle.internal.execution.steps.ResolveCachingStateStep.execute(ResolveCachingStateStep.java:38)
	at org.gradle.internal.execution.steps.ValidateStep.execute(ValidateStep.java:108)
	at org.gradle.internal.execution.steps.ValidateStep.execute(ValidateStep.java:55)
	at org.gradle.internal.execution.steps.CaptureStateBeforeExecutionStep.execute(CaptureStateBeforeExecutionStep.java:71)
	at org.gradle.internal.execution.steps.CaptureStateBeforeExecutionStep.execute(CaptureStateBeforeExecutionStep.java:45)
	at org.gradle.internal.execution.steps.SkipEmptyWorkStep.executeWithNonEmptySources(SkipEmptyWorkStep.java:177)
	at org.gradle.internal.execution.steps.SkipEmptyWorkStep.execute(SkipEmptyWorkStep.java:81)
	at org.gradle.internal.execution.steps.SkipEmptyWorkStep.execute(SkipEmptyWorkStep.java:53)
	at org.gradle.internal.execution.steps.RemoveUntrackedExecutionStateStep.execute(RemoveUntrackedExecutionStateStep.java:32)
	at org.gradle.internal.execution.steps.RemoveUntrackedExecutionStateStep.execute(RemoveUntrackedExecutionStateStep.java:21)
	at org.gradle.internal.execution.steps.legacy.MarkSnapshottingInputsStartedStep.execute(MarkSnapshottingInputsStartedStep.java:38)
	at org.gradle.internal.execution.steps.LoadPreviousExecutionStateStep.execute(LoadPreviousExecutionStateStep.java:36)
	at org.gradle.internal.execution.steps.LoadPreviousExecutionStateStep.execute(LoadPreviousExecutionStateStep.java:23)
	at org.gradle.internal.execution.steps.CleanupStaleOutputsStep.execute(CleanupStaleOutputsStep.java:75)
	at org.gradle.internal.execution.steps.CleanupStaleOutputsStep.execute(CleanupStaleOutputsStep.java:41)
	at org.gradle.internal.execution.steps.ExecuteWorkBuildOperationFiringStep.lambda$execute$2(ExecuteWorkBuildOperationFiringStep.java:66)
	at org.gradle.internal.execution.steps.ExecuteWorkBuildOperationFiringStep.execute(ExecuteWorkBuildOperationFiringStep.java:66)
	at org.gradle.internal.execution.steps.ExecuteWorkBuildOperationFiringStep.execute(ExecuteWorkBuildOperationFiringStep.java:38)
	at org.gradle.internal.execution.steps.AssignWorkspaceStep.lambda$execute$0(AssignWorkspaceStep.java:32)
	at org.gradle.api.internal.tasks.execution.TaskExecution$4.withWorkspace(TaskExecution.java:293)
	at org.gradle.internal.execution.steps.AssignWorkspaceStep.execute(AssignWorkspaceStep.java:30)
	at org.gradle.internal.execution.steps.AssignWorkspaceStep.execute(AssignWorkspaceStep.java:21)
	at org.gradle.internal.execution.steps.IdentityCacheStep.execute(IdentityCacheStep.java:37)
	at org.gradle.internal.execution.steps.IdentityCacheStep.execute(IdentityCacheStep.java:27)
	at org.gradle.internal.execution.steps.IdentifyStep.execute(IdentifyStep.java:47)
	at org.gradle.internal.execution.steps.IdentifyStep.execute(IdentifyStep.java:34)
	at org.gradle.internal.execution.impl.DefaultExecutionEngine$1.execute(DefaultExecutionEngine.java:64)
	at org.gradle.api.internal.tasks.execution.ExecuteActionsTaskExecuter.executeIfValid(ExecuteActionsTaskExecuter.java:145)
	at org.gradle.api.internal.tasks.execution.ExecuteActionsTaskExecuter.execute(ExecuteActionsTaskExecuter.java:134)
	at org.gradle.api.internal.tasks.execution.FinalizePropertiesTaskExecuter.execute(FinalizePropertiesTaskExecuter.java:46)
	at org.gradle.api.internal.tasks.execution.ResolveTaskExecutionModeExecuter.execute(ResolveTaskExecutionModeExecuter.java:51)
	at org.gradle.api.internal.tasks.execution.SkipTaskWithNoActionsExecuter.execute(SkipTaskWithNoActionsExecuter.java:57)
	at org.gradle.api.internal.tasks.execution.SkipOnlyIfTaskExecuter.execute(SkipOnlyIfTaskExecuter.java:74)
	at org.gradle.api.internal.tasks.execution.CatchExceptionTaskExecuter.execute(CatchExceptionTaskExecuter.java:36)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter$1.executeTask(EventFiringTaskExecuter.java:77)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter$1.call(EventFiringTaskExecuter.java:55)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter$1.call(EventFiringTaskExecuter.java:52)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:204)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:199)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:66)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:157)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:53)
	at org.gradle.internal.operations.DefaultBuildOperationExecutor.call(DefaultBuildOperationExecutor.java:78)
	at org.gradle.api.internal.tasks.execution.EventFiringTaskExecuter.execute(EventFiringTaskExecuter.java:52)
	at org.gradle.execution.plan.LocalTaskNodeExecutor.execute(LocalTaskNodeExecutor.java:42)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$InvokeNodeExecutorsAction.execute(DefaultTaskExecutionGraph.java:331)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$InvokeNodeExecutorsAction.execute(DefaultTaskExecutionGraph.java:318)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$BuildOperationAwareExecutionAction.lambda$execute$0(DefaultTaskExecutionGraph.java:314)
	at org.gradle.internal.operations.CurrentBuildOperationRef.with(CurrentBuildOperationRef.java:80)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$BuildOperationAwareExecutionAction.execute(DefaultTaskExecutionGraph.java:314)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph$BuildOperationAwareExecutionAction.execute(DefaultTaskExecutionGraph.java:303)
	at org.gradle.execution.plan.DefaultPlanExecutor$ExecutorWorker.execute(DefaultPlanExecutor.java:463)
	at org.gradle.execution.plan.DefaultPlanExecutor$ExecutorWorker.run(DefaultPlanExecutor.java:380)
	at org.gradle.execution.plan.DefaultPlanExecutor.process(DefaultPlanExecutor.java:116)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph.executeWithServices(DefaultTaskExecutionGraph.java:138)
	at org.gradle.execution.taskgraph.DefaultTaskExecutionGraph.execute(DefaultTaskExecutionGraph.java:123)
	at org.gradle.execution.SelectedTaskExecutionAction.execute(SelectedTaskExecutionAction.java:35)
	at org.gradle.execution.DryRunBuildExecutionAction.execute(DryRunBuildExecutionAction.java:51)
	at org.gradle.execution.BuildOperationFiringBuildWorkerExecutor$ExecuteTasks.call(BuildOperationFiringBuildWorkerExecutor.java:54)
	at org.gradle.execution.BuildOperationFiringBuildWorkerExecutor$ExecuteTasks.call(BuildOperationFiringBuildWorkerExecutor.java:43)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:204)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:199)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:66)
	at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:157)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:59)
	at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:53)
	at org.gradle.internal.operations.DefaultBuildOperationExecutor.call(DefaultBuildOperationExecutor.java:78)
	at org.gradle.execution.BuildOperationFiringBuildWorkerExecutor.execute(BuildOperationFiringBuildWorkerExecutor.java:40)
	at org.gradle.internal.build.DefaultBuildLifecycleController.lambda$executeTasks$10(DefaultBuildLifecycleController.java:313)
	at org.gradle.internal.model.StateTransitionController.doTransition(StateTransitionController.java:266)
	at org.gradle.internal.model.StateTransitionController.lambda$tryTransition$8(StateTransitionController.java:177)
	at org.gradle.internal.work.DefaultSynchronizer.withLock(DefaultSynchronizer.java:44)
	at org.gradle.internal.model.StateTransitionController.tryTransition(StateTransitionController.java:177)
	at org.gradle.internal.build.DefaultBuildLifecycleController.executeTasks(DefaultBuildLifecycleController.java:304)
	at org.gradle.internal.build.DefaultBuildWorkGraphController$DefaultBuildWorkGraph.runWork(DefaultBuildWorkGraphController.java:220)
	at org.gradle.internal.work.DefaultWorkerLeaseService.withLocks(DefaultWorkerLeaseService.java:264)
	at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:128)
	at org.gradle.composite.internal.DefaultBuildController.doRun(DefaultBuildController.java:181)
	at org.gradle.composite.internal.DefaultBuildController.access$000(DefaultBuildController.java:50)
	at org.gradle.composite.internal.DefaultBuildController$BuildOpRunnable.lambda$run$0(DefaultBuildController.java:198)
	at org.gradle.internal.operations.CurrentBuildOperationRef.with(CurrentBuildOperationRef.java:80)
	at org.gradle.composite.internal.DefaultBuildController$BuildOpRunnable.run(DefaultBuildController.java:198)
	at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:64)
	at org.gradle.internal.concurrent.AbstractManagedExecutor$1.run(AbstractManagedExecutor.java:47)
Caused by: com.android.ide.common.process.ProcessException: ninja: Entering directory `/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a'
[1/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/bss_pad.c.o
[2/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/bigalligator.c.o
[3/866] Building C object CMakeFiles/bkawrapper.dir/src/GV/ch/histup.c.o
[4/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/code_2270.c.o
[5/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o
FAILED: CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o 
/usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/bin/clang --target=aarch64-none-linux-android26 --sysroot=/usr/local/lib/android/sdk/ndk/25.1.8937393/toolchains/llvm/prebuilt/linux-x86_64/sysroot -D_LANGUAGE_C -Dbkawrapper_EXPORTS -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/ultra -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/2.0L/PR -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core1 -I/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/core2 -g -DANDROID -fdata-sections -ffunction-sections -funwind-tables -fstack-protector-strong -no-canonical-prefixes -D_FORTIFY_SOURCE=2 -Wformat -Werror=format-security  -fno-limit-debug-info  -fPIC -w -fcommon -O3 -MD -MT CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -MF CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o.d -o CMakeFiles/bkawrapper.dir/src/BGS/ch/frogminigame.c.o -c /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected parameter declarator
    mapSpecificFlags_set(0x10, 0);
                         ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:26: error: expected ')'
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:25: note: to match this '('
    mapSpecificFlags_set(0x10, 0);
                        ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:29:5: error: conflicting types for 'mapSpecificFlags_set'
    mapSpecificFlags_set(0x10, 0);
    ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/include/functions.h:458:6: note: previous declaration is here
void mapSpecificFlags_set(s32, s32);
     ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:30:5: error: expected identifier or '('
    if(actPtr->state == 4){
    ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:33:5: error: expected identifier or '('
    else{
    ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:36:1: error: extraneous closing brace ('}')
}
^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:58:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
            gcdialog_showDialog(ASSET_C81_DIALOG_YELLOW_FLIBBITS_MEET, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                          ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:61:113: error: use of undeclared identifier '__chFrogMinigame_textCallback'
                gcdialog_showDialog(ASSET_C83_DIALOG_YELLOW_FLIBBITS_RETURN, 0x4, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                                ^
/home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/src/main/cpp/src/BGS/ch/frogminigame.c:95:107: error: use of undeclared identifier '__chFrogMinigame_textCallback'
        gcdialog_showDialog(ASSET_C82_DIALOG_YELLOW_FLIBBITS_COMPLETE, 0xf, arg0->position, arg0->marker, __chFrogMinigame_textCallback, 0);
                                                                                                          ^
9 errors generated.
[6/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/croctus.c.o
[7/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/leafboat.c.o
[8/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/flibbit.c.o
[9/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/mudhut.c.o
[10/866] Building C object CMakeFiles/bkawrapper.dir/src/BGS/ch/mrvile.c.o
ninja: build stopped: subcommand failed.

C++ build system [build] failed while executing:
    /usr/local/lib/android/sdk/cmake/3.22.1/bin/ninja \
      -C \
      /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a \
      bkawrapper
  from /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app
	at com.android.build.gradle.internal.cxx.process.ExecuteProcessKt.execute(ExecuteProcess.kt:288)
	at com.android.build.gradle.internal.cxx.process.ExecuteProcessKt$executeProcess$1.invoke(ExecuteProcess.kt:108)
	at com.android.build.gradle.internal.cxx.process.ExecuteProcessKt$executeProcess$1.invoke(ExecuteProcess.kt:106)
	at com.android.build.gradle.internal.cxx.timing.TimingEnvironmentKt.time(TimingEnvironment.kt:32)
	at com.android.build.gradle.internal.cxx.process.ExecuteProcessKt.executeProcess(ExecuteProcess.kt:106)
	at com.android.build.gradle.internal.cxx.process.ExecuteProcessKt.executeProcess$default(ExecuteProcess.kt:85)
	at com.android.build.gradle.internal.cxx.build.CxxRegularBuilder.executeProcessBatch(CxxRegularBuilder.kt:332)
	at com.android.build.gradle.internal.cxx.build.CxxRegularBuilder.build(CxxRegularBuilder.kt:129)
	at com.android.build.gradle.tasks.ExternalNativeBuildTask$doTaskAction$$inlined$recordTaskAction$1.invoke(BaseTask.kt:70)
	at com.android.build.gradle.internal.tasks.Blocks.recordSpan(Blocks.java:51)
	at com.android.build.gradle.tasks.ExternalNativeBuildTask.doTaskAction(ExternalNativeBuildTask.kt:145)
	at com.android.build.gradle.internal.tasks.UnsafeOutputsTask$taskAction$$inlined$recordTaskAction$1.invoke(BaseTask.kt:65)
	at com.android.build.gradle.internal.tasks.Blocks.recordSpan(Blocks.java:51)
	at com.android.build.gradle.internal.tasks.UnsafeOutputsTask.taskAction(UnsafeOutputsTask.kt:63)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at org.gradle.internal.reflect.JavaMethod.invoke(JavaMethod.java:125)
	... 148 more
Caused by: com.android.ide.common.process.ProcessException: Error while executing process /usr/local/lib/android/sdk/cmake/3.22.1/bin/ninja with arguments {-C /home/runner/work/b-k-aarch64/b-k-aarch64/Android/app/.cxx/Debug/uq183170/arm64-v8a bkawrapper}
	at com.android.build.gradle.internal.process.GradleProcessResult.buildProcessException(GradleProcessResult.java:73)
	at com.android.build.gradle.internal.process.GradleProcessResult.assertNormalExitValue(GradleProcessResult.java:48)
	at com.android.build.gradle.internal.cxx.process.ExecuteProcessKt.execute(ExecuteProcess.kt:277)
	... 165 more
Caused by: org.gradle.process.internal.ExecException: Process 'command '/usr/local/lib/android/sdk/cmake/3.22.1/bin/ninja'' finished with non-zero exit value 1
	at org.gradle.process.internal.DefaultExecHandle$ExecResultImpl.assertNormalExitValue(DefaultExecHandle.java:431)
	at com.android.build.gradle.internal.process.GradleProcessResult.assertNormalExitValue(GradleProcessResult.java:46)
	... 166 more


BUILD FAILED in 32s
30 actionable tasks: 29 executed, 1 up-to-date
Process completed with exit code 1.