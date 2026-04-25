"""UI components for the YouTube Downloader application."""

import json
import os
import shutil
import sys
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QComboBox, QTextEdit, QProgressBar,
                             QMessageBox, QDialog, QRadioButton, QButtonGroup, QFrame,
                             QFileDialog, QCheckBox)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon


DARK_THEME_STYLESHEET = """
    QMainWindow, QDialog, QMessageBox {
        background: #0f172a;
    }
    QLabel {
        color: #e2e8f0;
        font-size: 13px;
    }
    QFrame#card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
    }
    QLineEdit, QComboBox, QTextEdit {
        background: #0b1220;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 10px;
        selection-background-color: #2563eb;
    }
    QComboBox QAbstractItemView {
        background: #0b1220;
        color: #f8fafc;
        border: 1px solid #334155;
        selection-background-color: #2563eb;
        selection-color: #ffffff;
        outline: 0;
    }
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
        border: 1px solid #3b82f6;
    }
    QPushButton {
        background: #1f2937;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px 12px;
        font-weight: 600;
    }
    QPushButton:hover {
        background: #273449;
    }
    QPushButton:disabled {
        color: #94a3b8;
        background: #1e293b;
    }
    QPushButton#primaryButton {
        background: #2563eb;
        border: 1px solid #2563eb;
    }
    QPushButton#primaryButton:hover {
        background: #1d4ed8;
    }
    QProgressBar {
        background: #0b1220;
        border: 1px solid #334155;
        border-radius: 8px;
        text-align: center;
        color: #e2e8f0;
        min-height: 18px;
    }
    QProgressBar::chunk {
        background-color: #22c55e;
        border-radius: 6px;
    }
    QRadioButton {
        color: #e2e8f0;
        spacing: 6px;
    }
    QCheckBox {
        color: #e2e8f0;
        spacing: 6px;
    }
"""


class DownloadWorker(QObject):
    """Background worker to download media without freezing the UI."""

    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url: str, quality: str, audio_only: bool, save_dir: str, ffmpeg_location: str = ""):
        super().__init__()
        self.url = url
        self.quality = quality
        self.audio_only = audio_only
        self.save_dir = save_dir
        self.ffmpeg_location = ffmpeg_location

    def _build_format(self) -> str:
        """Return yt-dlp format selector based on mode and quality."""
        if self.audio_only:
            if self.quality == "320kbps":
                return "bestaudio[abr<=320]/bestaudio/best"
            if self.quality == "192kbps":
                return "bestaudio[abr<=192]/bestaudio/best"
            if self.quality == "128kbps":
                return "bestaudio[abr<=128]/bestaudio/best"
            return "bestaudio/best"

        if self.quality == "1080p":
            return "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        if self.quality == "720p":
            return "bestvideo[height<=720]+bestaudio/best[height<=720]"
        if self.quality == "360p":
            return "bestvideo[height<=360]+bestaudio/best[height<=360]"
        return "bestvideo+bestaudio/best"

    def _progress_hook(self, data: dict):
        """Emit progress updates from yt-dlp hook callbacks."""
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes", 0)
            speed = data.get("speed")
            percent = int((downloaded / total) * 100) if total else 0
            speed_text = f" @ {speed / 1024 / 1024:.2f} MB/s" if speed else ""
            self.progress.emit(min(max(percent, 0), 99), f"Downloading... {percent}%{speed_text}")
        elif status == "finished":
            self.progress.emit(100, "Post-processing...")
            self.log.emit("Download finished. Finalizing file...")

    def run(self):
        """Run yt-dlp download in background thread."""
        try:
            try:
                import yt_dlp
            except ImportError:
                self.finished.emit(False, "yt-dlp is not installed. Run: pip install yt-dlp")
                return

            os.makedirs(self.save_dir, exist_ok=True)
            output_template = os.path.join(self.save_dir, "%(title)s.%(ext)s")
            ydl_opts = {
                "format": self._build_format(),
                "outtmpl": output_template,
                "progress_hooks": [self._progress_hook],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }
            if self.ffmpeg_location:
                ydl_opts["ffmpeg_location"] = self.ffmpeg_location

            if self.audio_only:
                ydl_opts["writethumbnail"] = True
                ydl_opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    },
                    {
                        "key": "FFmpegMetadata",
                    },
                    {
                        "key": "EmbedThumbnail",
                        "already_have_thumbnail": False,
                    },
                ]

            self.log.emit(f"Saving to: {self.save_dir}")
            if self.ffmpeg_location:
                self.log.emit(f"Using FFmpeg: {self.ffmpeg_location}")
            if self.audio_only:
                self.log.emit("MP3 tags and cover art embedding enabled.")
            self.log.emit("Connecting to download source...")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                title = info.get("title", "Unknown title")
                self.log.emit(f"Title: {title}")
                ydl.download([self.url])

            self.finished.emit(True, "Download completed successfully.")
        except Exception as exc:
            details = traceback.format_exc(limit=2)
            self.log.emit(details)
            self.finished.emit(False, f"Download failed: {exc}")


class LogViewerDialog(QDialog):
    """Dialog for viewing error logs."""
    
    def __init__(self, content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error Log")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Text editor for log content
        text_edit = QTextEdit()
        text_edit.setPlainText(content)
        text_edit.setFontFamily("Consolas")
        text_edit.setFontPointSize(10)
        text_edit.setReadOnly(True)
        
        layout.addWidget(text_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        copy_btn = QPushButton("Copy to Clipboard")
        
        close_btn.clicked.connect(self.accept)
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(content))
        
        button_layout.addWidget(copy_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def copy_to_clipboard(self, content: str):
        """Copy log content to clipboard."""
        QApplication.clipboard().setText(content)


class AboutDialog(QDialog):
    """Dialog for displaying app credits and GitHub link."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setMinimumSize(400, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        info_label = QLabel(
            "<b>YouTube Downloader</b><br><br>"
            "Created by LVEL5 &amp; LINUXFY<br><br>"
            "<a href=\"https://github.com/LVEL5/yt-downloader\">"
            "Visit GitHub Repository</a>"
        )
        info_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        info_label.setOpenExternalLinks(True)
        info_label.setAlignment(Qt.AlignCenter)

        close_button = QPushButton("Close")
        close_button.setMinimumHeight(36)
        close_button.clicked.connect(self.accept)

        layout.addWidget(info_label)
        layout.addWidget(close_button, 0, Qt.AlignCenter)


class YTDLP_Qt(QMainWindow):
    """Main application window for YouTube Downloader."""
    
    def __init__(self):
        super().__init__()
        self.video_quality_items = [
            "Best Quality",
            "1080p",
            "720p",
            "360p",
            "Best Available",
        ]
        self.audio_quality_items = [
            "Best Quality",
            "320kbps",
            "192kbps",
            "128kbps",
        ]
        self.settings = {}
        self.init_ui()
        self.load_settings()
        self.download_thread = None
        self.download_worker = None
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("YouTube Downloader")
        self.setMinimumSize(860, 620)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_candidates = [
            os.path.join(base_dir, "icon.ico"),
            os.path.join(base_dir, "icon.png"),
        ]
        for icon_path in icon_candidates:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break

        # Global style for a modern dark look
        # Stylesheet is now set globally in app.py

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header card
        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(2)

        title_label = QLabel("YouTube Downloader")
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #f8fafc;")

        header_top_layout = QHBoxLayout()
        header_top_layout.addWidget(title_label)
        header_top_layout.addStretch(1)

        self.about_btn = QPushButton("About")
        self.about_btn.setMinimumHeight(34)
        self.about_btn.setStyleSheet("color: #f87171;")
        self.about_btn.clicked.connect(self.show_about_dialog)
        header_top_layout.addWidget(self.about_btn, 0, Qt.AlignRight)
        header_top_layout.addSpacing(10)

        self.github_btn = QPushButton("GitHub")
        self.github_btn.setMinimumHeight(34)
        self.github_btn.clicked.connect(self.open_github)
        header_top_layout.addWidget(self.github_btn, 0, Qt.AlignRight)

        subtitle_label = QLabel("Fast video/audio downloads with metadata and cover art")
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        header_layout.addLayout(header_top_layout)
        header_layout.addWidget(subtitle_label)
        main_layout.addWidget(header_card)
        
        # URL card
        url_card = QFrame()
        url_card.setObjectName("card")
        url_layout = QVBoxLayout(url_card)
        url_layout.setContentsMargins(14, 14, 14, 14)
        url_layout.setSpacing(10)

        url_title = QLabel("Video URL")
        url_title.setStyleSheet("font-weight: 600;")
        url_layout.addWidget(url_title)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        self.url_input.setMinimumHeight(42)
        self.url_input.returnPressed.connect(self.start_download)
        self.url_input.textChanged.connect(self.on_url_changed)
        
        self.download_btn = QPushButton("Download")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setMinimumWidth(120)
        self.download_btn.setMinimumHeight(42)
        self.download_btn.clicked.connect(self.start_download)
        
        self.paste_btn = QPushButton("Paste")
        self.paste_btn.setMinimumHeight(42)
        self.paste_btn.clicked.connect(self.paste_url)

        self.inspect_btn = QPushButton("Inspect")
        self.inspect_btn.setMinimumHeight(42)
        self.inspect_btn.clicked.connect(self.inspect_url)

        input_layout.addWidget(self.url_input, 1)
        input_layout.addWidget(self.paste_btn)
        input_layout.addWidget(self.inspect_btn)
        input_layout.addWidget(self.download_btn)
        url_layout.addLayout(input_layout)

        save_layout = QHBoxLayout()
        save_layout.setSpacing(10)
        save_label = QLabel("Save Folder")
        save_label.setStyleSheet("font-weight: 600;")
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setPlaceholderText("Download folder path")
        self.save_dir_input.setMinimumHeight(38)
        self.save_dir_input.textChanged.connect(self.on_save_directory_changed)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setMinimumHeight(38)
        self.browse_btn.clicked.connect(self.browse_save_directory)
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setMinimumHeight(38)
        self.open_folder_btn.clicked.connect(self.open_save_directory)
        save_layout.addWidget(save_label, 0)
        save_layout.addWidget(self.save_dir_input, 1)
        save_layout.addWidget(self.browse_btn)
        save_layout.addWidget(self.open_folder_btn)
        url_layout.addLayout(save_layout)
        main_layout.addWidget(url_card)
        
        # Options + actions row
        options_layout = QHBoxLayout()
        options_layout.setSpacing(10)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(self.video_quality_items)
        self.quality_combo.setMinimumHeight(38)
        
        quality_label = QLabel("Quality")
        quality_label.setStyleSheet("font-weight: 600;")
        options_layout.addWidget(quality_label, 0)
        options_layout.addWidget(self.quality_combo, 1)
        
        self.video_radio = QRadioButton("Video")
        self.audio_radio = QRadioButton("Audio (MP3)")
        self.video_radio.setChecked(True)
        
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.video_radio)
        self.mode_group.addButton(self.audio_radio)
        
        self.video_radio.toggled.connect(self.toggle_mode)
        self.audio_radio.toggled.connect(self.toggle_mode)
        
        options_layout.addWidget(self.video_radio, 0, Qt.AlignVCenter)
        options_layout.addWidget(self.audio_radio, 0, Qt.AlignVCenter)
        options_layout.addStretch(1)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.clicked.connect(self.clear_form)
        self.save_settings_btn = QPushButton("Save Preferences")
        self.save_settings_btn.setMinimumHeight(36)
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.auto_paste_checkbox = QCheckBox("Auto-paste clipboard")
        self.open_folder_checkbox = QCheckBox("Open folder when done")
        self.auto_paste_checkbox.setChecked(False)
        self.open_folder_checkbox.setChecked(False)
        self.auto_paste_checkbox.stateChanged.connect(lambda _: self.save_settings())
        self.open_folder_checkbox.stateChanged.connect(lambda _: self.save_settings())
        options_layout.addWidget(self.auto_paste_checkbox, 0, Qt.AlignVCenter)
        options_layout.addWidget(self.open_folder_checkbox, 0, Qt.AlignVCenter)
        options_layout.addWidget(self.clear_btn)
        options_layout.addWidget(self.save_settings_btn)
        main_layout.addLayout(options_layout)
        
        # Progress card
        progress_card = QFrame()
        progress_card.setObjectName("card")
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(14, 12, 14, 12)
        progress_layout.setSpacing(8)
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addWidget(progress_card)
        
        # Logs card
        logs_card = QFrame()
        logs_card.setObjectName("card")
        logs_layout = QVBoxLayout(logs_card)
        logs_layout.setContentsMargins(14, 12, 14, 14)
        logs_layout.setSpacing(8)
        log_label = QLabel("Activity Log")
        log_label.setStyleSheet("font-weight: 600;")
        logs_layout.addWidget(log_label)
        log_tools_layout = QHBoxLayout()
        log_tools_layout.addStretch(1)
        self.copy_logs_btn = QPushButton("Copy Logs")
        self.copy_logs_btn.clicked.connect(self.copy_logs)
        self.clear_logs_btn = QPushButton("Clear Logs")
        self.clear_logs_btn.clicked.connect(lambda: self.log_text.clear())
        self.export_logs_btn = QPushButton("Export Logs")
        self.export_logs_btn.clicked.connect(self.export_logs)
        log_tools_layout.addWidget(self.copy_logs_btn)
        log_tools_layout.addWidget(self.clear_logs_btn)
        log_tools_layout.addWidget(self.export_logs_btn)
        logs_layout.addLayout(log_tools_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(180)
        self.log_text.setFontFamily("Consolas")
        self.log_text.setFontPointSize(9)
        logs_layout.addWidget(self.log_text, 1)
        main_layout.addWidget(logs_card, 1)
        self.log_text.append("Application ready.")
        
        credit_label = QLabel("Created by LVEL5 & LINUXFY")
        credit_label.setAlignment(Qt.AlignCenter)
        credit_label.setStyleSheet("color: #94a3b8; font-size: 11px; margin-top: 8px;")
        main_layout.addWidget(credit_label)
        
        self.setCentralWidget(central_widget)
    
    def load_settings(self):
        """Load saved settings from config file."""
        config_file = "settings.json"
        defaults = {
            "quality": self.quality_combo.currentText(),
            "mode": "video",
            "save_directory": self.get_save_directory(),
            "auto_paste_clipboard": False,
            "open_folder_on_finish": False,
        }
        settings = dict(defaults)

        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        settings.update(loaded)
            except Exception as e:
                print(f"Error loading settings: {e}")

        self.settings = settings
        self.save_dir_input.setText(settings.get("save_directory", defaults["save_directory"]))

        # Load quality preference
        if settings.get("quality"):
            index = self.quality_combo.findText(settings["quality"])
            if index >= 0:
                self.quality_combo.setCurrentIndex(index)

        mode = settings.get("mode", "video")
        if mode == "audio":
            self.audio_radio.setChecked(True)
        else:
            self.video_radio.setChecked(True)
        self.auto_paste_checkbox.setChecked(bool(settings.get("auto_paste_clipboard", False)))
        self.open_folder_checkbox.setChecked(bool(settings.get("open_folder_on_finish", False)))
        self.toggle_mode()
        self.try_auto_paste_url()
    
    def save_settings(self):
        """Save current settings to config file."""
        config_file = "settings.json"
        
        try:
            # Get current quality selection
            quality = self.quality_combo.currentText()
            mode = 'audio' if self.audio_radio.isChecked() else 'video'
            
            settings = {
                "quality": quality,
                "mode": mode,
                "save_directory": self.save_dir_input.text().strip() or self.get_save_directory(),
                "auto_paste_clipboard": self.auto_paste_checkbox.isChecked(),
                "open_folder_on_finish": self.open_folder_checkbox.isChecked(),
            }

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            self.settings = settings
            self.log_text.append("Preferences saved.")
                
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def start_download(self):
        """Start the download process."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "No URL", "Please enter a YouTube URL first.")
            return
        
        # Validate URL
        from utils import is_valid_url
        if not is_valid_url(url):
            QMessageBox.critical(self, "Invalid URL", 
                               "Please enter a valid YouTube URL.\n\n"
                               "Supported: youtube.com, youtu.be")
            return
        
        mode_text = "Audio" if self.audio_radio.isChecked() else "Video"
        quality_text = self.quality_combo.currentText()

        save_dir = self.get_save_directory()
        if not save_dir:
            QMessageBox.critical(self, "Invalid Save Directory", "Could not resolve a valid download directory.")
            return
        ffmpeg_location = self.get_ffmpeg_location()

        self.set_downloading_state(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Status: Preparing {mode_text.lower()} download")
        self.log_text.append(f"Starting {mode_text.lower()} download")
        self.log_text.append(f"URL: {url}")
        self.log_text.append(f"Quality: {quality_text}")
        self.log_text.append(f"Save directory: {save_dir}")

        self.download_thread = QThread(self)
        self.download_worker = DownloadWorker(
            url=url,
            quality=quality_text,
            audio_only=self.audio_radio.isChecked(),
            save_dir=save_dir,
            ffmpeg_location=ffmpeg_location,
        )
        self.download_worker.moveToThread(self.download_thread)

        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.log.connect(self.log_text.append)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)

        self.download_thread.start()
    
    def toggle_mode(self):
        """Toggle between video and audio mode."""
        current_selection = self.quality_combo.currentText()
        self.quality_combo.clear()
        
        if self.audio_radio.isChecked():
            self.quality_combo.addItems(self.audio_quality_items)
            if current_selection in self.audio_quality_items:
                self.quality_combo.setCurrentText(current_selection)
            self.status_label.setText("Status: Audio mode selected")
            self.log_text.append("Switched to audio mode.")
        else:
            self.quality_combo.addItems(self.video_quality_items)
            if current_selection in self.video_quality_items:
                self.quality_combo.setCurrentText(current_selection)
            self.status_label.setText("Status: Video mode selected")
            self.log_text.append("Switched to video mode.")
    
    def clear_form(self):
        """Clear URL input and reset progress display."""
        self.url_input.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Status: Ready")
        self.log_text.append("Form cleared.")

    def paste_url(self):
        """Paste URL from clipboard into the URL field."""
        clip_text = QApplication.clipboard().text().strip()
        if clip_text:
            self.url_input.setText(clip_text)
            self.log_text.append("URL pasted from clipboard.")

    def show_about_dialog(self):
        """Show the about dialog with credits and GitHub link."""
        dialog = AboutDialog(self)
        dialog.exec_()

    def open_github(self):
        """Open the GitHub repository in the default browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/LVEL5/yt-downloader"))

    def try_auto_paste_url(self):
        """Auto-fill URL from clipboard if enabled and input is empty."""
        if not self.auto_paste_checkbox.isChecked() or self.url_input.text().strip():
            return
        clip_text = QApplication.clipboard().text().strip()
        if clip_text and ("youtube.com" in clip_text or "youtu.be" in clip_text):
            self.url_input.setText(clip_text)
            self.log_text.append("Auto-pasted YouTube URL from clipboard.")

    def inspect_url(self):
        """Inspect URL and log basic metadata before download."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.information(self, "Inspect URL", "Paste a YouTube URL first.")
            return
        from utils import extract_video_id, is_valid_url
        if not is_valid_url(url):
            QMessageBox.warning(self, "Inspect URL", "Please enter a valid YouTube URL.")
            return
        video_id = extract_video_id(url)
        self.log_text.append(f"Inspect: video id = {video_id or 'unknown'}")
        self.log_text.append("Inspect complete.")

    def browse_save_directory(self):
        """Open folder picker for save directory."""
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self.save_dir_input.text().strip() or self.get_save_directory(),
        )
        if selected:
            self.save_dir_input.setText(selected)
            self.log_text.append(f"Save folder set: {selected}")
            self.save_settings()

    def open_save_directory(self):
        """Open current save directory in file explorer."""
        folder = self.get_save_directory()
        os.makedirs(folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def copy_logs(self):
        """Copy log content to clipboard."""
        QApplication.clipboard().setText(self.log_text.toPlainText())
        self.log_text.append("Logs copied to clipboard.")

    def export_logs(self):
        """Export logs to a text file."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            os.path.join(self.get_save_directory(), "yt_downloader_logs.txt"),
            "Text Files (*.txt)",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(self.log_text.toPlainText())
        self.log_text.append(f"Logs exported: {path}")

    def on_url_changed(self):
        """Minimal URL validation feedback."""
        value = self.url_input.text().strip()
        if not value:
            self.status_label.setText("Status: Ready")
            return
        from utils import is_valid_url
        self.status_label.setText("Status: URL looks valid" if is_valid_url(value) else "Status: URL not recognized")

    def on_save_directory_changed(self):
        """Reflect current save directory in status."""
        value = self.save_dir_input.text().strip()
        if value:
            self.status_label.setText("Status: Save folder updated")

    def get_save_directory(self) -> str:
        """Resolve save directory from config, fallback to Downloads folder."""
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube Downloads")
        configured = self.save_dir_input.text().strip() if hasattr(self, "save_dir_input") else ""
        if configured:
            return os.path.abspath(os.path.expanduser(configured))
        if isinstance(self.settings, dict) and self.settings.get("save_directory"):
            return os.path.abspath(os.path.expanduser(self.settings["save_directory"]))

        # Compatibility fallback from existing config.json
        config_path = "config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as fp:
                    config = json.load(fp)
                configured = str(config.get("save_directory", "")).strip()
                if configured:
                    return os.path.abspath(os.path.expanduser(configured))
        except Exception:
            pass
        return default_dir

    def get_ffmpeg_location(self) -> str:
        """Resolve ffmpeg location for yt-dlp (--ffmpeg-location equivalent)."""
        config_path = "config.json"

        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as fp:
                    config = json.load(fp)
                configured_path = str(config.get("ffmpeg_path", "")).strip()
                if configured_path:
                    expanded = os.path.abspath(os.path.expanduser(configured_path))
                    if os.path.isdir(expanded):
                        return expanded
                    if os.path.isfile(expanded):
                        return os.path.dirname(expanded)
        except Exception:
            pass

        ffmpeg_exe = shutil.which("ffmpeg")
        if ffmpeg_exe:
            return os.path.dirname(ffmpeg_exe)

        from utils import find_ffmpeg

        detected = find_ffmpeg()
        if detected and os.path.isfile(detected):
            return os.path.dirname(detected)

        return ""

    def set_downloading_state(self, is_downloading: bool):
        """Enable/disable controls while downloads are in progress."""
        self.download_btn.setEnabled(not is_downloading)
        self.inspect_btn.setEnabled(not is_downloading)
        self.paste_btn.setEnabled(not is_downloading)
        self.clear_btn.setEnabled(not is_downloading)
        self.save_settings_btn.setEnabled(not is_downloading)
        self.copy_logs_btn.setEnabled(not is_downloading)
        self.clear_logs_btn.setEnabled(not is_downloading)
        self.export_logs_btn.setEnabled(not is_downloading)
        self.browse_btn.setEnabled(not is_downloading)
        self.open_folder_btn.setEnabled(not is_downloading)
        self.url_input.setEnabled(not is_downloading)
        self.save_dir_input.setEnabled(not is_downloading)
        self.video_radio.setEnabled(not is_downloading)
        self.audio_radio.setEnabled(not is_downloading)
        self.auto_paste_checkbox.setEnabled(not is_downloading)
        self.open_folder_checkbox.setEnabled(not is_downloading)
        self.quality_combo.setEnabled(not is_downloading)

    def on_download_progress(self, value: int, status_text: str):
        """Update UI progress from worker callback."""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Status: {status_text}")

    def on_download_finished(self, success: bool, message: str):
        """Handle worker completion and restore UI state."""
        self.set_downloading_state(False)
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText("Status: Ready")
        self.log_text.append(message)

        if success:
            if self.open_folder_checkbox.isChecked():
                self.open_save_directory()
            QMessageBox.information(self, "Download Complete", message)
        else:
            QMessageBox.critical(self, "Download Failed", message)


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    
    window = YTDLP_Qt()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
