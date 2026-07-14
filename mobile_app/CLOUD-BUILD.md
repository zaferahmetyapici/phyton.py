# Build Without Windows (APK / IPA)

You can generate install files in the cloud and download them to your phone or iPad.

## Android APK (GitHub Actions)

1. Push this project to GitHub.
2. Open Actions tab in your repo.
3. Run workflow: **Build Android APK**.
4. After build finishes, download artifact:
   - `pattern-picnic-android-apk`
5. Copy APK to your Android phone and install.

### Android install note

- On phone: allow install from unknown sources for your file manager/browser.

## iPad IPA (Codemagic, no local Windows build)

Apple requires iOS signing for installable IPA files.

1. Create account at Codemagic.
2. Connect your GitHub repository.
3. Choose iOS workflow for Python/Kivy project.
4. Add Apple Developer signing (certificate + provisioning profile).
5. Build and export IPA.
6. Install via TestFlight or Apple Configurator.

## What you already have

- Mobile app source: [mobile_app/main.py](mobile_app/main.py)
- Android build config: [mobile_app/buildozer.spec](mobile_app/buildozer.spec)
- Android cloud workflow: [.github/workflows/android-apk.yml](.github/workflows/android-apk.yml)

## Important

- iPad app cannot be produced as installable IPA without Apple signing.
- If you want, I can add a ready `codemagic.yaml` next so your iPad pipeline is one-click.
