# OmniScreen Forge
**Version:** 1.1.0  

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
- **Automated Parameter Extraction**: It automatically pulls the structural native resolution and X/Y OS coordinates directly from `screeninfo` without user intervention.
- **State Persistence**: Remembers your designated input/output media locations and interface presets entirely via standard JSON loading.
- **Asynchronous Rendering**: An integrated processing queue ensures UI responsiveness even while massive 4K video streams are re-transcoded in the background.

## Video Tutorial
Before and after video- showcasing the before and after of various backgrounds, on my personal setup... the whole reason I created this in the first place!

https://youtu.be/CO36Bm-emIM

## Basic Usage Guide
1. **Load Media**: Select an MP4, GIF, JPEG, or PNG file utilizing the "Browse Media..." field.
2. **Define Screens**: Click "Auto-Detect Monitors" to instantly pull the screen profiles provided by Windows.
3. **Calibrate Dimensions**: For each screen row, determine the exact physical diagonal screen size (in inches, such as 31.5, 27.0, etc.)
4. **Arrange Layout**: Look at the "2D Layout Canvas" on the right side. Drag the monitor blocks to match exactly how they are arranged on your desk. Ensure their relative sizes intuitively look correct based on your physical inputs.
5. **Render Engine**: Click the purple "Render Media!" button. The log window will display progress, and a prompt will notify you when the asset is finalized. Right click your desktop and set the resulting image/video to "Span".
