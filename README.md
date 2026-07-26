🎬 Trail Film Renderer

A Python-based cinematic trail film renderer that generates a 4K (3840×2160), 30 FPS H.264 MP4 video using Pillow, NumPy, and FFmpeg.

📥 Installation Guide
Step 1: Download the Project

Download the ZIP file of this repository.

Step 2: Extract the Files

Unzip the downloaded folder to your preferred location.

Example:

C:\
 └── Trail-Film/
Step 3: Install Python

Make sure you have Python 3.8 or later installed.

Check your version:

python --version

or

python3 --version
📦 Install Required Packages

Install all required Python packages.

pip install Pillow numpy

or

pip install -r requirements.txt
⚙️ Requirements
Python 3.8+
Pillow
NumPy
FFmpeg installed and available in your system PATH

Verify FFmpeg installation:

ffmpeg -version

If FFmpeg prints its version information, it is installed correctly.

📁 Project Structure
Trail-Film/
│
├── trail_film.py                  # Main rendering script
│
├── bg/
│   ├── cabin.png                  # Background image
│   ├── logo.png                   # Logo
│   ├── map.png                    # Explore Nearby map artwork
│   ├── thumb-pine.png             # Trail thumbnail
│   ├── thumb-waterfall.png        # Trail thumbnail
│   └── thumb-beaver.png           # Trail thumbnail
│
├── fonts/
│   ├── Inter.ttf                  # UI font
│   └── Lora.ttf                   # Chat / Title font
│
├── output/                        # Generated videos (optional)
│
├── test_frames/                   # Preview frames
│
├── requirements.txt               # Python dependencies
│
└── README.md
🚀 Usage
Render the Full 4K Film
python trail_film.py trail_film_4k.mp4

This generates

Resolution: 3840 × 2160
Frame Rate: 30 FPS
Codec: H.264
MP4 with faststart enabled
🎞 Render in Chunks

Rendering in chunks is useful on slower computers or for long videos.

Command:

python trail_film.py chunk <start_frame> <end_frame> output.mp4

Example:

python trail_film.py chunk 0 90 part0.mp4

Render additional chunks:

python trail_film.py chunk 91 180 part1.mp4

python trail_film.py chunk 181 270 part2.mp4

After rendering all chunks, merge them using FFmpeg's concat demuxer.

🖼 Preview Test Frames

Generate preview frames without rendering the full video.

python trail_film.py test

This renders several representative frames as JPEG images into the

test_frames/

folder.

Preview resolution:

1280 × 720

Useful for quick visual quality checks before encoding the complete film.

📂 Output

After rendering, your project directory may look like:

Trail-Film/
│
├── trail_film_4k.mp4
├── test_frames/
│   ├── frame001.jpg
│   ├── frame002.jpg
│   ├── frame003.jpg
│   └── ...
│
└── output/
💻 Example Commands

Render full film

python trail_film.py trail_film_4k.mp4

Render frames 0–300

python trail_film.py chunk 0 300 part0.mp4

Render frames 301–600

python trail_film.py chunk 301 600 part1.mp4

Generate preview images

python trail_film.py test
📋 Dependencies
Package	Version
Python	3.8+
Pillow	Latest
NumPy	Latest
FFmpeg	Installed & added to PATH
🛠 Troubleshooting
ModuleNotFoundError

Install missing packages:

pip install Pillow numpy
ffmpeg not found

Ensure FFmpeg is installed and added to your system PATH.

Verify:

ffmpeg -version
Python not recognized

Install Python and enable "Add Python to PATH" during installation.

Verify:

python --version
