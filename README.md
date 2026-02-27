# OmniScreen Forge
**Version:** 2.1

## Installation & Requirements
1. **Python 3**: Ensure [Python 3.9+](https://www.python.org/downloads/) is installed and added to your System PATH.
2. **FFmpeg**: For video processing, you *must* have [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) installed and added to your System PATH. *If you only need to process static images, you can skip this.*
3. **Launch**: Simply double-click **`Run_OmniScreenForge.bat`**. 
   - This script will automatically verify your Python and FFmpeg installations, download all required Python dependencies (`pip install -r requirements.txt`), and launch the application interface.
## Overview
OmniScreen Forge is a specialized, lightweight, universal multi-monitor rescaling tool. It was built specifically to solve the problem of displaying a single continuous desktop image or video across multiple monitors that have drastically different physical sizes and resolutions.

When you have a 32-inch 4K monitor next to a 24-inch 1080p monitor, simply telling your OS to "Span" an image will result in a visual disjoint. The image on the 4K monitor will shrink to fit the pixels, while the 1080p side looks drastically zoomed in. OmniScreen Forge acts as a "physical compositor." It mathematically maps the exact screen resolutions against their physical diagonal screen sizes in inches to render a perfect, real-world continuous image.

## Key Features
- **Visual Desktop Layout Matrix**: A 2D canvas where you can freely drag around representations of your monitors to match their physical real-world positions. You can also drag their corners to adjust their physical sizes.
- **Dynamic PPI Calculation Engine**: The program calculates the exact Pixels Per Inch (PPI) for every assigned screen, establishing a master scaling baseline to equalize the video/image.
- **FFmpeg & PIL Subsystems**: It seamlessly maps videos using an asynchronous `subprocess` FFmpeg routine ensuring flawless frame-rates, and processes static images natively using Python's Pillow imaging library.
- **Visual Colorimeter & Advanced Grading**: Generate mathematical gradient calibrators or cyberpunk grids to visually match RGB profiles across mismatched monitors. Sync their output via FFmpeg `colorchannelmixer` matrices and `ImageEnhance` operations. Includes advanced control over Gamma curve bending, Brightness offsets, and Saturation.
- **Live Interactive Previews**: An integrated system that spawns native, perfectly scaled windows on every monitor to dynamically preview color grading and brightness adjustments in real-time, eliminating the need to render test images.
- **Automated Parameter Extraction**: It automatically pulls the structural native resolution and X/Y OS coordinates directly from `screeninfo` without user intervention.
- **Smart Wallpaper Detection**: Booting the application automatically queries the Windows OS via `ctypes` to instantly detect and load your active Desktop Wallpaper into the preview engine for fast, in-context color calibration.
- **State Persistence**: Remembers your designated input/output media locations and interface presets entirely via standard JSON loading.
- **Asynchronous Rendering**: An integrated processing queue ensures UI responsiveness even while massive 4K video streams are re-transcoded in the background.

## Video Tutorial
Before and after video- showcasing the before and after of various backgrounds, on my personal setup... the whole reason I created this in the first place!

[![OmniScreen Forge Video Tutorial](https://img.youtube.com/vi/CO36Bm-emIM/maxresdefault.jpg)](https://youtu.be/CO36Bm-emIM "Click to Watch!")

## Comprehensive Usage Guide

### 1. Initial Setup & Layout Configuration
1. **Load Media**: Select an MP4, GIF, JPEG, or PNG file utilizing the "Browse Media..." button. **Pro-Tip**: OmniScreen Forge automatically detects your active Windows Desktop Wallpaper on boot and pre-fills this path to save you time!
2. **Define Screens**: Click "Auto-Detect Monitors" to instantly pull the screen profiles (Resolution & OS Coordinates) directly from Windows. Alternatively, you can use "+ Add Monitor" to manually input custom screens.
3. **Calibrate Dimensions**: For each monitor listed on the left, you MUST input the exact physical diagonal screen size in inches (e.g., 27.0, 31.5). This is the core variable the engine uses to calculate physical pixel density (PPI) disparities.
4. **Arrange Layout (The 2D Canvas)**: Look at the "2D Layout Canvas" on the right. 
    - **Click & Drag** the monitor blocks to match exactly how they are grouped on your physical desk.
    - **Drag the bottom-right corner** of a block to visually resize its physical diagonal, which instantly updates the math on the left panel.
    - **Bezel Gap**: Use the slider to inject empty physical inches between screens, ensuring the image perfectly bridges monitors without "eating" parts of the picture behind the plastic frames.

### 2. Visual Colorimeter & Monitor Calibration
Mismatched monitors often display colors drastically differently. Use the "Color Calibration" suite to align them:
1. **Generate a Reference Image**: Click *2. Generate Rich Color Gradient*. This automatically paints a mathematically perfect 0-255 RGB & Luma sweeping reference image and saves it to your folder.
2. **Launch Live Interactive Previews**: Clicking this button will ask for a reference image (select the gradient you just generated, or your wallpaper). The app will spawn a perfectly scaled, individual replica of that image floating exactly in the center of every physical monitor you own.
3. **Adjust & Interpolate**: 
    - Adjust the Jog-Wheels for Gray (Luma), Red, Green, and Blue for any monitors that look "off" compared to your best screen.
    - Expand the `Advanced` section to tweak the core Gamut (midtones), Brightness offset (black floors), and Saturation.
    - **Real-Time Magic**: As you drag *any* slider or type *any* number into the boxes, the Live Preview on that specific monitor pushes updates instantly using Numpy array math, allowing you to perfectly color-match your displays by eye in real-time.
4. **Save Your Preset**: Once your layout and colors are perfect, hit "Save JSON Preset" on the main GUI. You will never have to calibrate this specific layout again!

### 3. Rendering & Output
1. **Include Source Audio**: Ensure this is checked if you are processing a video file and want the output to retain the original soundtrack.
2. **Select Output Format**: Use the dropdown next to the render button to select your desired output container (`.mp4`, `.gif`, `.png`, etc.). The app dynamically updates available formats based on your input media type.
3. **Render Media!**: Click the purple render button. 
    - FFmpeg instances are completely multithreaded. You can monitor the direct FFmpeg output in the scrolling log console natively within the app.
    - Once finished, right-click your Windows Desktop -> Personalize -> Background, select your new image/video, and set the "Choose a fit" option to **Span**. Your media is now perfectly mapping your physical reality!
