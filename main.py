"""
main.py
Medicine Scanner - Android app (Kivy)
By Vimlesh Patel

Screens:
  1. SplashScreen   - app intro
  2. HomeScreen      - list of scanned medicines (edit/delete), bottom nav
  3. AddEditScreen    - add manually / edit an existing entry (with delete)
  4. ScanScreen       - camera capture -> OCR -> auto-fill (with confidence check)
  5. ReportsScreen    - gallery of previously generated PDFs
  6. PDFExportScreen  - header (Received by / Date / Sent by) + merged table + Download/Share

Run on desktop for testing:
    pip install -r requirements.txt
    python main.py

Package for Android:
    buildozer -v android debug   (needs buildozer.spec, included)
"""

import os
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock
from kivy.utils import platform

import database
import names_store
import pdf_export
import ocr_match

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_OUTPUT_DIR = os.path.join(APP_DIR, "reports")
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

SCAN_PHOTO_DIR = os.path.join(APP_DIR, "scans")
os.makedirs(SCAN_PHOTO_DIR, exist_ok=True)


KV = """
#:import dp kivy.metrics.dp

<Card@BoxLayout>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(78)
    padding: dp(10)
    canvas.before:
        Color:
            rgba: 0.95, 0.96, 0.98, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]

ScreenManager:
    id: sm
    SplashScreen:
    HomeScreen:
    AddEditScreen:
    ScanScreen:
    ReportsScreen:
    PDFExportScreen:


<SplashScreen>:
    name: "splash"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 0.85, 0.9, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
        Label:
            text: "[b]Medicine Scanner[/b]"
            markup: True
            font_size: "26sp"
            color: 0.1, 0.1, 0.1, 1
            size_hint_y: None
            height: dp(40)
        Label:
            text: "Scan. Identify. Stay informed."
            color: 0.3, 0.3, 0.3, 1
            size_hint_y: None
            height: dp(24)
        BoxLayout:
        Button:
            text: "Get started"
            size_hint: 0.8, None
            height: dp(48)
            pos_hint: {"center_x": 0.5}
            on_release: app.root.current = "home"
        Label:
            text: "Created by Vimlesh Patel"
            color: 0.2, 0.4, 0.9, 1
            size_hint_y: None
            height: dp(40)


<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(90)
            orientation: "vertical"
            canvas.before:
                Color:
                    rgba: 0.85, 0.9, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "Medicine scans"
                font_size: "20sp"
                bold: True
                color: 0.1, 0.1, 0.1, 1
            Label:
                text: "By Vimlesh Patel"
                font_size: "13sp"
                color: 0.3, 0.3, 0.3, 1

        ScrollView:
            BoxLayout:
                id: medicine_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(12)
                spacing: dp(10)

        BoxLayout:
            size_hint_y: None
            height: dp(78)
            padding: dp(10), dp(10)
            spacing: dp(12)
            canvas.before:
                Color:
                    rgba: 0.97, 0.97, 0.98, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "Reports"
                font_size: "14sp"
                halign: "center"
                background_normal: ""
                background_color: 0.20, 0.45, 0.95, 1
                color: 1, 1, 1, 1
                on_release: app.root.current = "reports"
            Button:
                text: "Scan"
                bold: True
                font_size: "16sp"
                halign: "center"
                size_hint_y: 1.35
                pos_hint: {"center_y": 0.5}
                background_normal: ""
                background_color: 0.15, 0.75, 0.55, 1
                color: 1, 1, 1, 1
                on_release: app.root.current = "scan"
            Button:
                text: "+ Add manually"
                font_size: "14sp"
                halign: "center"
                background_normal: ""
                background_color: 0.55, 0.35, 0.9, 1
                color: 1, 1, 1, 1
                on_release: app.open_add_edit(None)


<AddEditScreen>:
    name: "add_edit"
    name_input: name_input
    batch_input: batch_input
    expiry_input: expiry_input
    strips_input: strips_input
    per_strip_input: per_strip_input
    BoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(10)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            Button:
                text: "< Back"
                size_hint_x: None
                width: dp(80)
                on_release: app.root.current = "home"
            Label:
                text: "Add / edit medicine"
                bold: True
            Button:
                text: "Delete"
                size_hint_x: None
                width: dp(80)
                background_color: 0.9, 0.3, 0.3, 1
                on_release: app.delete_current_item()

        Label:
            text: "Medicine name"
            size_hint_y: None
            height: dp(20)
            halign: "left"
        TextInput:
            id: name_input
            size_hint_y: None
            height: dp(44)
            multiline: False

        Label:
            text: "Batch no."
            size_hint_y: None
            height: dp(20)
        TextInput:
            id: batch_input
            size_hint_y: None
            height: dp(44)
            multiline: False

        Label:
            text: "Expiry date (MM/YYYY)"
            size_hint_y: None
            height: dp(20)
        TextInput:
            id: expiry_input
            size_hint_y: None
            height: dp(44)
            multiline: False

        BoxLayout:
            size_hint_y: None
            height: dp(44)
            spacing: dp(10)
            TextInput:
                id: strips_input
                hint_text: "Strips"
                multiline: False
            TextInput:
                id: per_strip_input
                hint_text: "Qty per strip"
                multiline: False

        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(10)
            Button:
                text: "Cancel"
                on_release: app.root.current = "home"
            Button:
                text: "Save"
                on_release: app.save_medicine()


<ScanScreen>:
    name: "scan"
    result_label: result_label
    BoxLayout:
        orientation: "vertical"
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            canvas.before:
                Color:
                    rgba: 0.85, 0.9, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "X"
                size_hint_x: None
                width: dp(50)
                background_normal: ""
                background_color: 0, 0, 0, 0
                color: 0.1, 0.1, 0.1, 1
                on_release: app.root.current = "home"
            Label:
                text: "Scan medicine"
                bold: True
                color: 0.1, 0.1, 0.1, 1

        Image:
            id: preview_image
            source: ""
            opacity: 0
            allow_stretch: True

        Label:
            text: "Take a photo of the medicine strip / box,\\nor choose one from your gallery"
            color: 0.3, 0.3, 0.3, 1
            halign: "center"

        Label:
            id: result_label
            text: ""
            color: 0.1, 0.5, 0.3, 1
            size_hint_y: None
            height: dp(160)
            halign: "left"
            valign: "top"
            text_size: self.width, None

        BoxLayout:
            size_hint_y: None
            height: dp(90)
            padding: dp(10)
            spacing: dp(10)
            Button:
                text: "Take Photo"
                background_normal: ""
                background_color: 0.15, 0.75, 0.55, 1
                color: 1, 1, 1, 1
                on_release: app.open_camera()
            Button:
                text: "Choose from Gallery"
                background_normal: ""
                background_color: 0.55, 0.35, 0.9, 1
                color: 1, 1, 1, 1
                on_release: app.open_gallery()


<ReportsScreen>:
    name: "reports"
    report_list: report_list
    BoxLayout:
        orientation: "vertical"
        padding: dp(12)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            Button:
                text: "< Back"
                size_hint_x: None
                width: dp(80)
                on_release: app.root.current = "home"
            Label:
                text: "Reports (last 30 days)"
                bold: True
        ScrollView:
            BoxLayout:
                id: report_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
        Button:
            text: "+ Create new PDF from current list"
            size_hint_y: None
            height: dp(48)
            on_release: app.root.current = "pdf_export"


<PDFExportScreen>:
    name: "pdf_export"
    received_by_input: received_by_input
    sent_by_label: sent_by_label
    table_preview: table_preview
    BoxLayout:
        orientation: "vertical"
        padding: dp(14)
        spacing: dp(8)
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            Button:
                text: "< Back"
                size_hint_x: None
                width: dp(80)
                on_release: app.root.current = "home"
            Label:
                text: "Export as PDF"
                bold: True

        Label:
            text: "Received by"
            size_hint_y: None
            height: dp(18)
        TextInput:
            id: received_by_input
            size_hint_y: None
            height: dp(42)
            multiline: False

        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(10)
            Label:
                text: "Date: " + root.today_str
            Spinner:
                id: sent_by_label
                text: app.sent_by_names[0] if app.sent_by_names else "Add name"
                values: app.sent_by_names + ["+ Add new name"]
                on_text: app.on_sent_by_selected(self.text)

        ScrollView:
            BoxLayout:
                id: table_preview
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(4)

        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(10)
            Button:
                text: "Share"
                on_release: app.share_pdf()
            Button:
                text: "Download"
                on_release: app.download_pdf()
"""


class SplashScreen(Screen):
    pass


class HomeScreen(Screen):
    def on_pre_enter(self):
        self.refresh_list()

    def refresh_list(self):
        app = App.get_running_app()
        container = self.ids.medicine_list
        container.clear_widgets()
        for item in database.get_all_medicines(days=30):
            container.add_widget(app.build_medicine_card(item))


class AddEditScreen(Screen):
    current_item_id = None

    def load_item(self, item_id=None):
        self.current_item_id = item_id
        if item_id:
            item = database.get_medicine(item_id)
            self.name_input.text = item["name"]
            self.batch_input.text = item["batch_no"]
            self.expiry_input.text = item["expiry"] or ""
            self.strips_input.text = str(item["strips"])
            self.per_strip_input.text = str(item["per_strip"])
        else:
            self.name_input.text = ""
            self.batch_input.text = ""
            self.expiry_input.text = ""
            self.strips_input.text = "1"
            self.per_strip_input.text = "1"


class ScanScreen(Screen):
    def on_pre_enter(self):
        self.result_label.text = ""
        if "preview_image" in self.ids:
            self.ids.preview_image.source = ""
            self.ids.preview_image.opacity = 0


class ReportsScreen(Screen):
    def on_pre_enter(self):
        self.refresh_reports()

    def refresh_reports(self):
        from kivy.uix.button import Button
        app = App.get_running_app()
        container = self.ids.report_list
        container.clear_widgets()
        if not os.path.isdir(PDF_OUTPUT_DIR):
            return
        for fname in sorted(os.listdir(PDF_OUTPUT_DIR), reverse=True):
            if fname.lower().endswith(".pdf"):
                full_path = os.path.join(PDF_OUTPUT_DIR, fname)
                btn = Button(text=fname, size_hint_y=None, height=44)
                btn.bind(on_release=lambda *_, p=full_path: app.open_pdf(p))
                container.add_widget(btn)


class PDFExportScreen(Screen):
    today_str = StringProperty(datetime.now().strftime("%d %b %Y"))

    def on_pre_enter(self):
        self.refresh_table()

    def refresh_table(self):
        from kivy.uix.label import Label
        app = App.get_running_app()
        container = self.ids.table_preview
        container.clear_widgets()

        header = Label(
            text="S.No | Medicine name | Batch | Exp | Qty",
            size_hint_y=None, height=28, bold=True,
        )
        container.add_widget(header)

        rows = database.get_all_medicines(days=30)
        merged = pdf_export.merge_medicines(rows) if rows else []
        for i, r in enumerate(merged, start=1):
            line = f"{i}. {r['name']} | {r['batch_no']} | {r['expiry']} | {r['qty']}"
            container.add_widget(Label(text=line, size_hint_y=None, height=26))


class MedicineScannerApp(App):
    sent_by_names = ListProperty([])

    def build(self):
        database.init_db()
        self.sent_by_names = names_store.load_names()
        if platform == "android":
            self.request_android_permissions()
        return Builder.load_string(KV)

    def request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission
            perms = [
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
            ]
            # Android 13+ (API 33) replaced READ_EXTERNAL_STORAGE with a
            # media-specific permission for picking images from the gallery.
            # Older plyer versions may not define this constant, so fall
            # back to the raw permission string.
            read_media_images = getattr(Permission, "READ_MEDIA_IMAGES", "android.permission.READ_MEDIA_IMAGES")
            perms.append(read_media_images)
            request_permissions(perms)
        except Exception as e:
            print("Permission request failed:", e)

    # ---------- Home screen: medicine card widget ----------
    def _make_icon_button(self, kind, on_release):
        """Build a small square button with a hand-drawn pencil/trash icon.
        We draw with canvas lines instead of a Unicode/emoji glyph because
        the font bundled with the app doesn't include emoji characters
        (they were showing up as empty boxes)."""
        from kivy.uix.button import Button
        from kivy.graphics import Color, Line, Rectangle

        btn = Button(size_hint_x=None, width=40, background_normal="", background_color=(0.9, 0.9, 0.9, 1))
        btn.bind(on_release=on_release)

        def redraw(*_):
            btn.canvas.after.clear()
            x, y, w, h = btn.x, btn.y, btn.width, btn.height
            cx, cy = x + w / 2, y + h / 2
            with btn.canvas.after:
                Color(0.15, 0.15, 0.15, 1)
                if kind == "edit":
                    # simple pencil: diagonal line + nib triangle
                    Line(points=[cx - 8, cy - 8, cx + 8, cy + 8], width=1.8)
                    Line(points=[cx + 6, cy + 10, cx + 10, cy + 6], width=1.8)
                else:
                    # simple trash can: lid + body outline
                    Line(points=[cx - 8, cy + 8, cx + 8, cy + 8], width=1.8)
                    Line(points=[cx - 4, cy + 8, cx - 4, cy + 10], width=1.5)
                    Line(points=[cx + 4, cy + 8, cx + 4, cy + 10], width=1.5)
                    Line(
                        points=[
                            cx - 6, cy + 8, cx - 5, cy - 8,
                            cx + 5, cy - 8, cx + 6, cy + 8,
                        ],
                        width=1.8,
                    )

        btn.bind(pos=redraw, size=redraw)
        return btn

    def build_medicine_card(self, item):
        card = BoxLayout(orientation="vertical", size_hint_y=None, height=90, padding=8, spacing=2)

        from kivy.uix.label import Label
        from kivy.uix.button import Button

        top_row = BoxLayout(size_hint_y=None, height=32, spacing=4)

        name_label = Label(
            text=f"[b]{item['name']}[/b]", markup=True,
            halign="left", valign="middle", shorten=True, shorten_from="right",
            color=(0.1, 0.1, 0.1, 1),
        )
        name_label.bind(size=lambda w, s: setattr(w, "text_size", (w.width, w.height)))
        top_row.add_widget(name_label)

        edit_btn = self._make_icon_button("edit", lambda *_: self.open_add_edit(item["id"]))
        delete_btn = self._make_icon_button("delete", lambda *_: self.delete_item(item["id"]))
        top_row.add_widget(edit_btn)
        top_row.add_widget(delete_btn)

        qty = item["strips"] * item["per_strip"]
        details = Label(
            text=f"Batch: {item['batch_no']}   Qty: {qty}   Expiry: {item['expiry']}",
            size_hint_y=None, height=24, font_size="12sp",
            color=(0.35, 0.35, 0.35, 1),
        )

        # NOTE: Kivy's BoxLayout renders the most-recently-added child at the
        # top, so "details" must be added BEFORE "top_row" for the medicine
        # name to actually appear above the batch/expiry line.
        card.add_widget(details)
        card.add_widget(top_row)
        return card

    def open_add_edit(self, item_id):
        screen = self.root.get_screen("add_edit")
        screen.load_item(item_id)
        self.root.current = "add_edit"

    def save_medicine(self):
        screen = self.root.get_screen("add_edit")
        name = screen.name_input.text.strip()
        batch = screen.batch_input.text.strip()
        expiry = screen.expiry_input.text.strip()
        try:
            strips = int(screen.strips_input.text or 1)
            per_strip = int(screen.per_strip_input.text or 1)
        except ValueError:
            strips, per_strip = 1, 1

        if not name or not batch:
            return  # medicine name & batch no. are required

        if screen.current_item_id:
            database.update_medicine(screen.current_item_id, name, batch, expiry, strips, per_strip)
        else:
            database.add_medicine(name, batch, expiry, strips, per_strip, source="manual")

        self.root.current = "home"

    def delete_current_item(self):
        screen = self.root.get_screen("add_edit")
        if screen.current_item_id:
            database.delete_medicine(screen.current_item_id)
        self.root.current = "home"

    def delete_item(self, item_id):
        database.delete_medicine(item_id)
        self.root.get_screen("home").refresh_list()

    # ---------- Scan screen ----------
    def _new_photo_path(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(SCAN_PHOTO_DIR, f"scan_{stamp}.jpg")

    def _file_provider_uri(self, path):
        """Turn a local file path into a content:// Uri other apps can use."""
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        FileProviderCls = autoclass("androidx.core.content.FileProvider")
        JavaFile = autoclass("java.io.File")
        act = PythonActivity.mActivity
        authority = act.getPackageName() + ".fileprovider"
        return FileProviderCls.getUriForFile(act, authority, JavaFile(path))

    def open_camera(self):
        """Open the device's native camera app and capture a photo.

        We talk to Android directly (instead of plyer.camera) so we can use
        a proper FileProvider content:// Uri - modern Android refuses to
        hand a raw file:// path to another app (FileUriExposedException).
        """
        screen = self.root.get_screen("scan")
        if platform != "android":
            screen.result_label.text = "Camera not available on this device/platform."
            return
        photo_path = self._new_photo_path()
        self._last_photo_path = photo_path
        try:
            from jnius import autoclass
            from android import activity

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            MediaStore = autoclass("android.provider.MediaStore")

            act = PythonActivity.mActivity
            photo_uri = self._file_provider_uri(photo_path)

            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, photo_uri)
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)

            self._camera_request_code = 9001
            activity.bind(on_activity_result=self._on_activity_result)
            act.startActivityForResult(intent, self._camera_request_code)
        except Exception as e:
            screen.result_label.text = f"Could not open camera: {e}"

    def open_gallery(self):
        """Let the user pick an existing photo from the gallery."""
        screen = self.root.get_screen("scan")
        if platform != "android":
            screen.result_label.text = "Gallery not available on this device/platform."
            return
        try:
            from jnius import autoclass
            from android import activity

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")

            act = PythonActivity.mActivity
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.setType("image/*")

            self._gallery_request_code = 9002
            activity.bind(on_activity_result=self._on_activity_result)
            act.startActivityForResult(intent, self._gallery_request_code)
        except Exception as e:
            screen.result_label.text = f"Could not open gallery: {e}"

    def _on_activity_result(self, requestCode, resultCode, data):
        from android import activity
        activity.unbind(on_activity_result=self._on_activity_result)
        RESULT_OK = -1

        if requestCode == getattr(self, "_camera_request_code", None):
            Clock.schedule_once(lambda dt: self._handle_camera_result(resultCode == RESULT_OK), 0)
        elif requestCode == getattr(self, "_gallery_request_code", None):
            if resultCode == RESULT_OK and data is not None:
                uri = data.getData()
                Clock.schedule_once(lambda dt: self._handle_gallery_uri(uri), 0)
            else:
                Clock.schedule_once(lambda dt: self._set_scan_message("No photo selected."), 0)

    def _set_scan_message(self, text):
        self.root.get_screen("scan").result_label.text = text

    def _handle_camera_result(self, success):
        if not success:
            self._set_scan_message("No photo was taken.")
            return
        path = getattr(self, "_last_photo_path", None)
        self._process_scanned_image(path)

    def _handle_gallery_uri(self, uri):
        """Copy the picked gallery image (content:// Uri) into our app folder."""
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            BitmapFactory = autoclass("android.graphics.BitmapFactory")
            CompressFormat = autoclass("android.graphics.Bitmap$CompressFormat")
            FileOutputStream = autoclass("java.io.FileOutputStream")

            act = PythonActivity.mActivity
            resolver = act.getContentResolver()
            input_stream = resolver.openInputStream(uri)
            bitmap = BitmapFactory.decodeStream(input_stream)
            input_stream.close()

            dest_path = self._new_photo_path()
            out_stream = FileOutputStream(dest_path)
            bitmap.compress(CompressFormat.JPEG, 90, out_stream)
            out_stream.flush()
            out_stream.close()

            self._process_scanned_image(dest_path)
        except Exception as e:
            self._set_scan_message(f"Could not load photo: {e}")

    def _process_scanned_image(self, image_path):
        """Run OCR on the given photo, show the preview + result, and save it."""
        screen = self.root.get_screen("scan")

        if image_path and os.path.exists(image_path) and "preview_image" in screen.ids:
            screen.ids.preview_image.source = image_path
            screen.ids.preview_image.opacity = 1
            screen.ids.preview_image.reload()

        if image_path and os.path.exists(image_path) and ocr_match.OCR_AVAILABLE:
            result = ocr_match.analyze_scan(image_path)
        else:
            # Fallback demo result if OCR isn't available or no photo was captured
            result = {
                "name": "Paracetamol 500mg", "name_confidence": 0.96, "name_needs_review": False,
                "batch_no": "B4021", "batch_needs_review": False,
                "expiry": "08/2027", "expiry_needs_review": False,
                "strips": 25, "per_strip": 15, "qty_needs_review": False,
            }

        review_flags = []
        if result["name_needs_review"]:
            review_flags.append("name")
        if result["batch_needs_review"]:
            review_flags.append("batch no.")
        if result["expiry_needs_review"]:
            review_flags.append("expiry")
        if result["qty_needs_review"]:
            review_flags.append("quantity")

        review_text = f"\\nPlease verify: {', '.join(review_flags)}" if review_flags else "\\nAll fields high confidence."
        screen.result_label.text = (
            f"Name: {result['name']}\\nBatch: {result['batch_no']}\\n"
            f"Expiry: {result['expiry']}\\nQty: {result['strips']} x {result['per_strip']}"
            f"{review_text}"
        )

        database.add_medicine(
            result["name"], result["batch_no"], result["expiry"],
            result["strips"], result["per_strip"], source="scan",
        )

    # ---------- PDF export screen ----------
    def on_sent_by_selected(self, value):
        if value == "+ Add new name":
            self.show_add_name_popup()

    def show_add_name_popup(self):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button

        text_input = TextInput(hint_text="Enter name", multiline=False, size_hint_y=None, height=44)
        save_btn = Button(text="Save name", size_hint_y=None, height=44)

        box.add_widget(text_input)
        box.add_widget(save_btn)

        popup = Popup(title="Add new sender name", content=box, size_hint=(0.8, 0.35))

        def on_save(*_):
            name = text_input.text.strip()
            if name:
                self.sent_by_names = names_store.add_name(name)
            popup.dismiss()

        save_btn.bind(on_release=on_save)
        popup.open()

    def _current_output_path(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(PDF_OUTPUT_DIR, f"medicine_report_{stamp}.pdf")

    def _build_pdf(self):
        screen = self.root.get_screen("pdf_export")
        rows = database.get_all_medicines(days=30)
        received_by = screen.received_by_input.text.strip()
        sent_by = screen.sent_by_label.text
        if sent_by == "+ Add new name":
            sent_by = ""
        output_path = self._current_output_path()
        return pdf_export.generate_pdf(rows, received_by=received_by, sent_by=sent_by,
                                        output_path=output_path)

    def download_pdf(self):
        path = self._build_pdf()
        if platform == "android":
            try:
                self._save_pdf_to_downloads(path)
                self._toast("Saved to Downloads: " + os.path.basename(path))
            except Exception as e:
                self._toast(f"Could not save to Downloads: {e}")
        else:
            print(f"PDF saved to: {path}")

    def _save_pdf_to_downloads(self, local_path):
        """Copy a PDF from our private storage into the public Downloads
        folder, so the user can actually find/open it (scoped-storage safe)."""
        from jnius import autoclass
        Build = autoclass("android.os.Build")
        fname = os.path.basename(local_path)

        with open(local_path, "rb") as f:
            data = f.read()

        if Build.VERSION.SDK_INT >= 29:
            MediaStoreDownloads = autoclass("android.provider.MediaStore$Downloads")
            ContentValues = autoclass("android.content.ContentValues")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            act = PythonActivity.mActivity
            resolver = act.getContentResolver()

            values = ContentValues()
            values.put("_display_name", fname)
            values.put("mime_type", "application/pdf")

            item_uri = resolver.insert(MediaStoreDownloads.EXTERNAL_CONTENT_URI, values)
            out_stream = resolver.openOutputStream(item_uri)
            out_stream.write(bytearray(data))
            out_stream.flush()
            out_stream.close()
        else:
            Environment = autoclass("android.os.Environment")
            downloads_dir = str(Environment.getExternalStoragePublicDirectory(
                Environment.DIRECTORY_DOWNLOADS).getAbsolutePath())
            dest_path = os.path.join(downloads_dir, fname)
            with open(dest_path, "wb") as out:
                out.write(data)

    def _toast(self, message):
        print(message)
        if platform != "android":
            return
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Toast = autoclass("android.widget.Toast")

            @run_on_ui_thread
            def _show():
                Toast.makeText(PythonActivity.mActivity, message, Toast.LENGTH_LONG).show()

            _show()
        except Exception as e:
            print("Toast failed:", e)

    def share_pdf(self):
        path = self._build_pdf()
        if platform == "android":
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")

                act = PythonActivity.mActivity
                file_uri = self._file_provider_uri(path)

                intent = Intent(Intent.ACTION_SEND)
                intent.setType("application/pdf")
                intent.putExtra(Intent.EXTRA_STREAM, file_uri)
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

                chooser = Intent.createChooser(intent, "Share medicine report")
                act.startActivity(chooser)
            except Exception as e:
                self._toast(f"Could not share PDF: {e}")
        else:
            print(f"(Desktop demo) Would share file: {path}")

    def open_pdf(self, path):
        """Open a previously generated PDF (used by the Reports screen list)."""
        if platform == "android":
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")

                act = PythonActivity.mActivity
                file_uri = self._file_provider_uri(path)

                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(file_uri, "application/pdf")
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                act.startActivity(intent)
            except Exception as e:
                self._toast(f"Could not open PDF: {e}")
        else:
            print(f"(Desktop demo) Would open: {path}")


if __name__ == "__main__":
    MedicineScannerApp().run()
