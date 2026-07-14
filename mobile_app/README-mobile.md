# Pattern Picnic Mobile Build Guide

This folder contains a **mobile starter port** of your desktop app using Kivy.

## Build without Windows (recommended)

If you do not want to build on Windows, use cloud builds:

- Android APK: run the GitHub Actions workflow in [.github/workflows/android-apk.yml](../.github/workflows/android-apk.yml)
- Guide: [mobile_app/CLOUD-BUILD.md](CLOUD-BUILD.md)

## 1) Run locally (desktop test)

```powershell
cd mobile_app
pip install -r requirements-mobile.txt
python main.py
```

## 2) Build Android APK (Windows via WSL/Ubuntu recommended)

Buildozer works best on Linux.

```bash
cd mobile_app
pip install buildozer cython==0.29.36
buildozer android debug
```

APK output is under:

- `mobile_app/bin/`

## 3) Build iPad app (IPA)

iPad build **requires macOS + Xcode** (Apple toolchain requirement).

### On macOS:

```bash
python3 -m pip install kivy-ios
cd mobile_app
toolchain build python3 kivy
toolchain create patternpicnicmobile .
```

Then open the generated Xcode project, set:

- Team / Signing
- Bundle ID
- Target device: iPad

Finally archive and export `.ipa` from Xcode.

## Notes

- Your current `algorithm_game_gui_v2.py` uses `tkinter`, which is desktop-only.
- The mobile UI in this folder is a clean starter and should be expanded feature-by-feature from the desktop version.
