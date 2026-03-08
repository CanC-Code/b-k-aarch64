name: Android Build

on:
  workflow_dispatch:
  push:
    branches: [ main, master ]

jobs:
  build-android:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17
          cache: gradle

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y imagemagick
          pip install PyYAML

      - name: Generate Binary Asset Manifests
        run: python3 runtime/generate_assets_header.py

      - name: Generate App Icons
        run: |
          if [ -f "master_icon.png" ]; then
            python3 runtime/generate_icons.py master_icon.png
          else
            echo "master_icon.png not found, building with dummy icon"
            mkdir -p Android/app/src/main/res/mipmap-mdpi
            convert -size 48x48 xc:gray Android/app/src/main/res/mipmap-mdpi/ic_launcher.png
            cp Android/app/src/main/res/mipmap-mdpi/ic_launcher.png Android/app/src/main/res/mipmap-mdpi/ic_launcher_round.png
          fi

      - name: Prepare C++ Source (harmonizer)
        run: |
          set -x  # echo commands for debug
          python3 runtime/prepare_source.py || { echo "Harmonizer failed!"; exit 1; }

      # Critical: Verify changes landed BEFORE build
      - name: Verify BOOL macro / preamble in source
        run: |
          FILE="decomp-files/src/core2/code_5BEB0.c"
          if [ -f "$FILE" ]; then
            echo "First 50 lines of failing file:"
            head -n 50 "$FILE"
            echo ""
            echo "Grep for BOOL define:"
            grep -A 5 -B 5 "BOOL" "$FILE" || echo "No BOOL macro found — harmonizer didn't apply!"
            echo ""
            echo "Grep for pragma diagnostic:"
            grep -i "SourceHarmonizer" "$FILE" || echo "No pragma — preamble missing!"
          else
            echo "File $FILE not found — source dir issue?"
          fi

      # Nuclear clean for CMake/NDK
      - name: Force full clean of Gradle + CMake artifacts
        run: |
          GRADLEW_PATH=$(find . -name gradlew | head -1)
          chmod +x "$GRADLEW_PATH"
          cd $(dirname "$GRADLEW_PATH")
          ./gradlew clean --no-daemon --stacktrace --info || true
          cd -  # back to root
          echo "Nuking CMake build dirs..."
          rm -rf Android/app/.cxx || true
          rm -rf Android/app/build || true
          rm -rf Android/app/.externalNativeBuild || true
          find Android -name "*.o" -delete || true
          find Android -name "CMakeCache.txt" -delete || true
          find Android -name "build.ninja" -delete || true
          find Android -name "CMakeFiles" -type d -exec rm -rf {} + || true

      # Second clean after nuke
      - name: Final Gradle clean
        run: |
          GRADLEW_PATH=$(find . -name gradlew | head -1)
          chmod +x "$GRADLEW_PATH"
          cd $(dirname "$GRADLEW_PATH")
          ./gradlew clean --no-daemon --stacktrace --info

      - name: Build with Gradle (force rerun)
        run: |
          GRADLEW_PATH=$(find . -name gradlew | head -1)
          chmod +x "$GRADLEW_PATH"
          cd $(dirname "$GRADLEW_PATH")
          ./gradlew assembleDebug --rerun-tasks --no-daemon --stacktrace --info

      - name: Upload Debug APK
        if: success()  # only if build succeeds
        uses: actions/upload-artifact@v4
        with:
          name: BKA-debug-apk
          path: "Android/app/build/outputs/apk/debug/*.apk"