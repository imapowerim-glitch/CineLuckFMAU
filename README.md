Project name and scope
CineLuck — Raspberry Pi 5 video camera using Picamera2 on the latest Raspberry Pi OS Desktop, designed for a 5-inch 800×640 touch display, single fixed 2K recording mode, clean pro UI, safe start/stop, predictable manual control.

Imaging and recording
Sensor windowing to DCI 2K 2048×1080, selectable frame rates 24, 25, 30, 50, 60 fps. Hardware encoding H.264 High (24–60 fps) and optional H.265 Main (24–60 fps). MKV container by default for crash-safe stops, MP4 as an option. Constant bitrates tuned for SSD. On-screen timecode, clip timer, dropped-frame indicator, storage speed test before enabling 50/60 fps.

Preview and monitoring
Real-time preview from lores stream to reduce CPU, letterboxed to 800×640, exposure tools zebras with threshold, RGB/luma histogram, waveform, false color, focus peaking, 2× punch-in magnifier, clean preview mode for framing.

Exposure and color controls
Manual and auto modes with clear priority. Shutter in µs mapped to frame rate limits. Gain as ISO-style steps. Metering modes: average, center, spot. Anti-flicker 50/60 Hz with shutter multiples and fixed FPS. White balance auto indoor/daylight and manual CCT 2000–8000 K + tint. Native camera controls for contrast, saturation, sharpness, gamma, safe color matrix presets — all immediate and reversible.

Audio
USB mic or USB sound card via ALSA, 48 kHz, AAC at 128–256 kbps, muxed to MKV/MP4. Input gain and peak meter on screen. Device selector with auto-reconnect.

User interface and UX
Touch-first layout. Top bar with FPS, shutter, gain/ISO, WB, free space, temp. Center preview. Bottom bar with big record toggle, quick exposure/WB. Slide-in panels: left exposure, right WB/color. Safe Stop modal. Onscreen keyboard only when needed. Touch debounce during critical ops.

File management
Auto folder structure: Movies/CineLuck/YYYY-MM-DD. Filenames: YYYY-MM-DD_HH-MM-SS_2Kfps_codec.mkv or .mp4. Rolling take counter. Sidecar .json with camera settings. Free-space monitor with warning and auto stop. Default target SSD, fallback SD with FPS guard.

Stability and state machine
Finite state machine: Idle, Preview, Recording, Stopping, Error. Safe Stop = drain encoder, finalize container, wait on camera request, then Preview. Heavy ops off UI thread. Retry logic on camera open. Watchdog restarts preview if stalled.

Performance and thermals
Hardware encoder V4L2, single YUV→RGB reused, capped preview FPS at high bitrates. Active cooling mandatory, temp readout, soft throttling (lower preview FPS or bitrate). SSD via USB3 for 2K50/60. SD usable only for moderate bitrates.

Display and rendering
Vsync to avoid tearing, integer scaling + letterbox, configurable UI scale, persistent layout.

Configuration and persistence
Settings in ~/.config/CineLuck, JSON profiles, startup self-check, auto directory creation, config export/import.

Safety and recovery
MKV default to avoid broken clips, MP4 with periodic moov updates optional. Graceful SIGINT handling. Last 100 lines of log saved at ~/.config/CineLuck/run.log.
