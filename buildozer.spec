[app]
title = Medicine Scanner
package.name = medicinescanner
package.domain = org.vimleshpatel
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0
requirements = python3,kivy,reportlab,pytesseract,pillow,plyer,pyjnius,android
orientation = portrait
fullscreen = 0

# Custom presplash (replaces the default Kivy "Loading..." screen shown
# while the app starts up) and matching background color.
presplash.filename = %(source.dir)s/data/presplash.png
android.presplash_color = #219574

android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

# Needed for androidx.core.content.FileProvider (used to safely share
# camera photos / PDFs with other apps on Android 7+), and Google ML Kit
# for on-device text recognition (reads medicine name/batch/expiry from
# the photo automatically - bundled model, works offline).
android.gradle_dependencies = androidx.core:core:1.10.1,com.google.mlkit:text-recognition:16.0.0

# Registers file_paths.xml as an Android resource (res/xml/file_paths.xml)
# so the FileProvider <meta-data> in the manifest can actually find it.
android.res_xml = scripts/file_paths.xml

[buildozer]
log_level = 2
warn_on_root = 1
