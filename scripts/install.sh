#!/bin/bash
#
# CineLuck Installation Script for Raspberry Pi OS
# Installs dependencies and sets up the CineLuck video camera application
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    log_info "Checking if running on Raspberry Pi..."
    
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_warning "This script is designed for Raspberry Pi. Some features may not work on other systems."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "Raspberry Pi detected"
        
        # Show Pi model
        PI_MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo "Unknown")
        log_info "Pi Model: $PI_MODEL"
    fi
}

# Check for required system packages
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check for Python 3.9+
    if ! python3 --version | grep -qE "Python 3\.(9|1[0-9])" 2>/dev/null; then
        log_error "Python 3.9+ is required. Please update your system."
        exit 1
    fi
    
    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required. Please install python3-pip."
        exit 1
    fi
    
    log_success "Python and pip requirements met"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install required system packages
    sudo apt install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        libcamera-dev \
        libcamera-apps \
        python3-libcamera \
        python3-picamera2 \
        libasound2-dev \
        portaudio19-dev \
        libavformat-dev \
        libavcodec-dev \
        libavdevice-dev \
        libavutil-dev \
        libswscale-dev \
        libswresample-dev \
        libavfilter-dev \
        v4l-utils \
        ffmpeg \
        git
    
    log_success "System dependencies installed"
}

# Install Qt6 dependencies
install_qt6_deps() {
    log_info "Installing Qt6 dependencies..."
    
    # Install Qt6 development packages
    sudo apt install -y \
        python3-pyqt6 \
        python3-pyqt6.qtcore \
        python3-pyqt6.qtgui \
        python3-pyqt6.qtwidgets \
        qt6-base-dev \
        libqt6core6 \
        libqt6gui6 \
        libqt6widgets6
    
    log_success "Qt6 dependencies installed"
}

# Create Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    VENV_DIR="$HOME/.local/share/cineluck/venv"
    
    # Create directory
    mkdir -p "$(dirname "$VENV_DIR")"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    
    # Activate and upgrade pip
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip setuptools wheel
    
    log_success "Virtual environment created at $VENV_DIR"
}

# Install CineLuck application
install_cineluck() {
    log_info "Installing CineLuck application..."
    
    VENV_DIR="$HOME/.local/share/cineluck/venv"
    source "$VENV_DIR/bin/activate"
    
    # Install from current directory
    pip install -e .
    
    log_success "CineLuck application installed"
}

# Configure camera permissions
setup_camera_permissions() {
    log_info "Setting up camera permissions..."
    
    # Add user to video group
    sudo usermod -a -G video "$USER"
    
    # Enable camera
    if command -v raspi-config &> /dev/null; then
        log_info "Enabling camera interface..."
        sudo raspi-config nonint do_camera 0
    fi
    
    log_success "Camera permissions configured"
}

# Create desktop entry
create_desktop_entry() {
    log_info "Creating desktop entry..."
    
    VENV_DIR="$HOME/.local/share/cineluck/venv"
    DESKTOP_FILE="$HOME/.local/share/applications/cineluck.desktop"
    
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=CineLuck
Comment=Professional Video Camera for Raspberry Pi
Exec=$VENV_DIR/bin/python -m cineluck.main
Icon=camera-video
Terminal=false
Type=Application
Categories=AudioVideo;Recorder;
StartupNotify=true
EOF
    
    # Make executable
    chmod +x "$DESKTOP_FILE"
    
    log_success "Desktop entry created"
}

# Create startup script
create_startup_script() {
    log_info "Creating startup script..."
    
    VENV_DIR="$HOME/.local/share/cineluck/venv"
    SCRIPT_FILE="$HOME/.local/bin/cineluck"
    
    mkdir -p "$(dirname "$SCRIPT_FILE")"
    
    cat > "$SCRIPT_FILE" << EOF
#!/bin/bash
# CineLuck Startup Script

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Set environment variables
export QT_QPA_PLATFORM=wayland
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1

# Run application
cd "$HOME"
python -m cineluck.main "\$@"
EOF
    
    # Make executable
    chmod +x "$SCRIPT_FILE"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi
    
    log_success "Startup script created at $SCRIPT_FILE"
}

# Configure system for optimal performance
optimize_system() {
    log_info "Configuring system for optimal performance..."
    
    # GPU memory split (minimum 128MB for camera)
    if command -v raspi-config &> /dev/null; then
        log_info "Setting GPU memory split to 128MB..."
        sudo raspi-config nonint do_memory_split 128
    fi
    
    # Enable hardware acceleration
    if [ -f /boot/config.txt ]; then
        log_info "Enabling hardware acceleration..."
        
        # Add hardware acceleration settings if not present
        if ! grep -q "gpu_mem=" /boot/config.txt; then
            echo "gpu_mem=128" | sudo tee -a /boot/config.txt
        fi
        
        if ! grep -q "dtoverlay=vc4-kms-v3d" /boot/config.txt; then
            echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
        fi
    fi
    
    log_success "System optimization completed"
}

# Main installation function
main() {
    echo "============================================="
    echo "    CineLuck Installation Script"
    echo "    Professional Video Camera for Pi"
    echo "============================================="
    echo
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this script as root"
        exit 1
    fi
    
    # Check requirements
    check_raspberry_pi
    check_system_requirements
    
    # Install dependencies
    install_system_deps
    install_qt6_deps
    
    # Setup application
    setup_venv
    install_cineluck
    
    # Configure system
    setup_camera_permissions
    create_desktop_entry
    create_startup_script
    optimize_system
    
    echo
    log_success "CineLuck installation completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Reboot your system: sudo reboot"
    echo "2. After reboot, run: cineluck"
    echo "   or launch from the applications menu"
    echo
    echo "For optimal performance on a 5-inch display:"
    echo "- Set display resolution to 800x480"
    echo "- Enable forced composition pipeline in raspi-config"
    echo
}

# Run main installation
main "$@"