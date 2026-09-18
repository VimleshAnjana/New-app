"""
Inserts a FileProvider <provider> declaration into python-for-android's
AndroidManifest.tmpl.xml, so the app can hand out content:// Uris instead
of raw file:// paths (required on Android 7+ to avoid
FileUriExposedException when opening the camera, sharing, or viewing a
generated PDF in another app).

Usage: python3 patch_p4a_fileprovider.py /path/to/AndroidManifest.tmpl.xml
"""

import sys

PROVIDER_BLOCK = """
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="org.vimleshpatel.medicinescanner.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
"""


def main():
    manifest_path = sys.argv[1]
    with open(manifest_path) as f:
        content = f.read()

    if "fileprovider" in content:
        print("FileProvider already present, skipping")
        return

    content = content.replace("</application>", PROVIDER_BLOCK + "    </application>")
    with open(manifest_path, "w") as f:
        f.write(content)
    print(f"FileProvider added to {manifest_path}")


if __name__ == "__main__":
    main()
