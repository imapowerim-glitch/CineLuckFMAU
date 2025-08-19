# CineLuck - Professional Raspberry Pi Video Camera

CineLuck is a professional video camera application designed for Raspberry Pi 5 using Picamera2, optimized for a 5-inch 800×640 touch display with DCI 2K recording capabilities.

## Features

### Core Capabilities
- **DCI 2K Recording**: 2048×1080 sensor windowing with selectable frame rates (24, 25, 30, 50, 60 fps)
- **Hardware Encoding**: H.264 High and H.265 Main profiles with V4L2 acceleration
- **Crash-Safe Recording**: MKV container by default, MP4 optional with proper finalization
- **Professional Audio**: USB audio support via ALSA with 48kHz AAC encoding

### Touch-First Interface
- **Optimized Layout**: 800×640 touch-friendly interface design
- **Real-Time Preview**: Low-latency preview with monitoring tools
- **Slide-In Panels**: Left panel for exposure, right panel for color/WB controls
- **Status Bar**: Live display of FPS, shutter, ISO, temperature, and storage

### Monitoring Tools
- **Exposure Tools**: Zebras, histogram, waveform, false color
- **Focus Assistance**: Focus peaking and 2× punch-in magnifier
- **Audio Monitoring**: Input level meter and device selection

### Professional Controls
- **Exposure**: Manual and auto modes with precise shutter/ISO control
- **White Balance**: Auto modes and manual CCT 2000-8000K with tint
- **Image Processing**: Contrast, saturation, sharpness adjustments
- **Anti-Flicker**: 50/60 Hz flicker reduction

### File Management
- **Organized Structure**: Auto-created folders by date (Movies/CineLuck/YYYY-MM-DD)
- **Smart Naming**: YYYY-MM-DD_HH-MM-SS_2Kfps_codec.mkv format
- **Metadata**: JSON sidecar files with camera settings
- **Storage Monitoring**: Free space tracking with automatic warnings

### System Integration
- **State Machine**: Robust recording workflow with safe stop functionality
- **Thermal Management**: CPU temperature monitoring with throttling
- **Hardware Optimization**: GPU memory management and V4L2 encoder support
- **Configuration**: Persistent settings with profile support

## Installation

### Prerequisites
- Raspberry Pi 5 (recommended) or Pi 4
- Raspberry Pi OS Desktop (latest)
- Camera module (v2, v3, or HQ Camera)
- 5-inch 800×640 touch display (optional)
- USB audio device (optional)
- High-speed storage (USB 3.0 SSD recommended for 50/60fps)

### Quick Install
```bash
git clone https://github.com/imapowerim-glitch/CineLuckFMAU.git
cd CineLuckFMAU
chmod +x scripts/install.sh
./scripts/install.sh
```

The installation script will:
1. Install system dependencies (libcamera, PyQt6, audio libraries)
2. Set up Python virtual environment
3. Install CineLuck application
4. Configure camera permissions
5. Create desktop entry and startup script
6. Optimize system settings

### Manual Installation
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-dev python3-pip libcamera-dev python3-picamera2 \
    python3-pyqt6 libasound2-dev portaudio19-dev v4l-utils ffmpeg

# Clone and install
git clone https://github.com/imapowerim-glitch/CineLuckFMAU.git
cd CineLuckFMAU
pip3 install -e .

# Add user to video group
sudo usermod -a -G video $USER

# Enable camera (if using raspi-config)
sudo raspi-config nonint do_camera 0
```

## Usage

### Starting the Application
```bash
# From command line
cineluck

# Or launch from desktop applications menu
```

### Basic Operation
1. **Power On**: Camera initializes and enters Preview mode
2. **Recording**: Press red REC button or spacebar to start recording
3. **Monitoring**: Use preview tools (zebras, focus peaking) as needed
4. **Settings**: Access exposure (left panel) or color (right panel) controls
5. **Safe Stop**: Press STOP button for proper recording finalization

### Keyboard Shortcuts
- `Space`: Start/stop recording
- `F1`: Toggle exposure panel
- `F2`: Toggle color panel
- `F11`: Toggle fullscreen
- `Esc`: Hide panels or exit fullscreen

### File Output
- **Location**: `~/Movies/CineLuck/YYYY-MM-DD/`
- **Format**: `YYYY-MM-DD_HH-MM-SS_2K{fps}_{codec}.mkv`
- **Metadata**: Corresponding `.json` sidecar files
- **Audio**: Embedded AAC audio if USB device connected

## Configuration

Settings are stored in `~/.config/CineLuck/settings.json` and include:
- Camera parameters (exposure, white balance, image processing)
- Recording settings (codec, bitrate, frame rate)
- UI preferences (scale, panel visibility)
- Audio configuration (device, gain)
- Storage preferences (directory, container format)

### Configuration Profiles
Save and load different settings profiles for various shooting scenarios:
```python
# Example: Create profile for outdoor shooting
config_manager.save_profile("outdoor_daylight")
config_manager.load_profile("outdoor_daylight")
```

## Hardware Recommendations

### Display Setup
- **5-inch DSI Touch**: 800×640 resolution preferred
- **HDMI Alternative**: Any display, will letterbox to fit
- **Touch Calibration**: Use `xinput_calibrator` if needed

### Storage Performance
- **High Frame Rates (50/60fps)**: USB 3.0 SSD required
- **Standard Rates (24-30fps)**: Class 10 SD card acceptable
- **Storage Test**: Built-in speed test validates storage capability

### Audio Setup
- **USB Audio Interface**: Professional quality recommended
- **USB Microphone**: Simple setup for basic audio
- **Sample Rate**: Fixed at 48kHz for best compatibility

## Development

### Project Structure
```
cineluck/
├── __init__.py           # Package initialization
├── main.py              # Application entry point
├── app.py               # Main application class
├── camera/              # Camera management
│   ├── manager.py       # Picamera2 interface
│   └── encoder.py       # Video encoding
├── ui/                  # User interface
│   ├── main_window.py   # Main window layout
│   ├── widgets/         # UI components
│   ├── panels/          # Side panels
│   └── dialogs/         # Modal dialogs
├── audio/               # Audio management
├── config/              # Configuration system
├── state/               # State machine
└── utils/               # Utilities and helpers
```

### Testing
```bash
# Basic functionality test
python3 test_basic.py

# Full test with dependencies installed
python3 -m pytest tests/
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## Troubleshooting

### Camera Issues
- **No Preview**: Check camera cable and enable in raspi-config
- **Permission Denied**: Ensure user is in video group
- **Poor Performance**: Increase GPU memory split to 128MB+

### Audio Issues
- **No Audio Device**: Check USB connection and `arecord -l`
- **Low Levels**: Adjust input gain in color panel
- **Sync Issues**: USB audio may have slight latency

### Recording Issues
- **Dropped Frames**: Use faster storage or lower frame rate
- **Corrupted Files**: Ensure proper safe stop procedure
- **Large Files**: Check bitrate settings and storage space

### Performance Optimization
- **Thermal Throttling**: Ensure adequate cooling (fan recommended)
- **Storage Speed**: Use USB 3.0 SSD for high frame rates
- **Memory Usage**: Close other applications during recording

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Picamera2](https://github.com/raspberrypi/picamera2) library
- UI framework: [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Raspberry Pi Foundation for hardware platform
- Community contributors and testers
