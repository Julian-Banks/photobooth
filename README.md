# Photobooth AR System
A Python-based photobooth with real-time pose detection and motion tracking overlays.

## Features
- Camera streaming with OpenCV
- Overlay positioning based on pose landmarks
- Web interface for remote control (Flask-based)

## Installation
```bash
# Clone repository
git clone https://github.com/Julian-Banks/photobooth/
cd photobooth

#check that your Python version is >3.9 and <3.13 as mediapipe only supports this range
python --version #or python3 --version if this give an error

#create a virtual environment
python -m venv venv

# Install with pip (Python 3.9+ required)
pip install .
```

**Note:** MediaPipe requires [system dependencies](https://google.github.io/mediapipe/getting_started/install.html)

## Basic Usage

```bash
#activate venv
source venv/bin/activate

# Start development server
python -m src.main

```

Access web interface at `http://localhost:5000`
