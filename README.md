# YouTube Downloader

A fast and user-friendly YouTube video and audio downloader with a modern dark-themed GUI. Download videos in various qualities or extract audio as MP3 files with embedded metadata and cover art.

![YouTube Downloader](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-orange.svg)

## Features

- **Video Downloads**: Download videos in multiple qualities (1080p, 720p, 360p, Best Available)
- **Audio Downloads**: Extract audio as MP3 with metadata and cover art embedding
- **Modern GUI**: Clean, dark-themed interface built with PyQt5
- **Batch Processing**: Download multiple videos (playlist support coming soon)
- **Settings Persistence**: Remembers your preferences and save directory
- **Progress Tracking**: Real-time download progress with speed indicators
- **Error Handling**: Comprehensive error logging and user-friendly messages
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Screenshots

*Add screenshots here*

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (included in releases)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Download FFmpeg

The application requires FFmpeg for audio processing. Download the latest FFmpeg binaries for your platform:

- **Windows**: FFmpeg executables are included in the release
- **macOS/Linux**: Install via package manager or download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

### Running the Application

```bash
python main.py
```

### Basic Usage

1. **Enter URL**: Paste a YouTube video URL in the input field
2. **Select Quality**: Choose video quality or audio format
3. **Set Save Directory**: Browse to your preferred download folder
4. **Download**: Click the "Download" button to start

### Features

- **Auto-paste**: Automatically paste clipboard content when the app starts
- **Open Folder**: Automatically open the download folder when complete
- **Inspect URL**: Preview video information before downloading
- **Activity Log**: View detailed download logs and error messages

### Keyboard Shortcuts

- `Enter`: Start download when URL is entered
- `Ctrl+V`: Paste URL from clipboard

## Configuration

Settings are automatically saved to `settings.json`:

```json
{
    "quality": "Best Quality",
    "mode": "video",
    "save_directory": "/path/to/downloads",
    "auto_paste_clipboard": false,
    "open_folder_on_finish": false
}
```

## Building from Source

### Prerequisites

- Python 3.8+
- PyInstaller

### Build Steps

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. Build the executable:

   ```bash
   pyinstaller YTDownloader.spec
   ```
3. The executable will be created in the `dist/` folder

### Development

To run in development mode:

```bash
python main.py
```

## Dependencies

- **PyQt5**: GUI framework
- **yt-dlp**: YouTube downloading library
- **requests**: HTTP library for metadata
- **FFmpeg**: Audio/video processing

## Project Structure

```
├── main.py              # Application entry point
├── app.py               # Main application logic
├── ui.py                # GUI components and styling
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── settings.json        # User settings
├── config.json          # Application configuration
├── YTDownloader.spec    # PyInstaller build configuration
├── icon.ico             # Application icon
├── ffmpeg.exe           # FFmpeg binary (Windows)
├── yt-dlp.exe           # yt-dlp binary (Windows)
└── build/               # Build artifacts
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

**"yt-dlp is not installed"**

- Ensure yt-dlp is installed: `pip install yt-dlp`

**"FFmpeg not found"**

- Download FFmpeg and place it in the application directory or PATH

**Download fails**

- Check your internet connection
- Verify the YouTube URL is valid
- Some videos may be region-restricted or private

**GUI doesn't start**

- Ensure PyQt5 is installed correctly
- Try running with `python -c "import PyQt5; print('PyQt5 OK')"`

### Logs

Check the activity log in the application for detailed error messages. You can also export logs for debugging.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Created by **LVEL5 & LINUXFY**

- GitHub: [LVEL5/yt-downloader](https://github.com/LVEL5/yt-downloader)
- Inspired by various open-source YouTube downloaders

## Disclaimer

This application is for educational purposes only. Please respect YouTube's Terms of Service and copyright laws. Only download content you have permission to access.`</content>`
`<parameter name="filePath">`c:\Apps\YT Downloader\Source\readme.md
