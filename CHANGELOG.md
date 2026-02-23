# OmniScreen Forge Changelog

## [1.1.0] - GUI Style Update

### Added
- **Help Menu**: Added a top navigation menu bar containing `Changelog` and `About` popup dialogues.
- **Asynchronous Rendering**: Integrated a threading model to process FFmpeg actions in the background, keeping the GUI perfectly responsive during long renders.
- **Progress Monitoring**: Added a dedicated progress bar and scrolling log console directly underneath the rendering tools so users can see exactly what FFmpeg is doing in real-time.
- **State Persistence**: The software now automatically creates a `bezel_settings.json` file. It permanently remembers the last `initial_dir` locations you used when opening or saving media/presets, drastically speeding up repetitive workflows.
- **"Buy Me A Coffee" & QR Integration**: Added top-right header buttons. The text button opens a browser link, and the QR button opens a perfectly scaled, borderless image popup for easy scanning.

### Changed (Design & UI Improvements)
- **Rebranding**: Changed core application name from `BezelCorrect` to **OmniScreen Forge**.
- **Dark Theme Upgrade**: Completely migrated from standard Tkinter visuals to the custom `sv_ttk` dark theme framework.
    - Title Text: Replaced standard label with a custom Cyan (`#00FFFF`) to Magenta (`#FF00FF`) mathematical color-stepped gradient font rendering.
    - Canvas: Deepened the core 2D canvas background to matching `#050505`.
    - Title Bar: Implemented native Windows `ctypes` OS-level calls to force the application windows and popups strictly into Dark Mode.
    - Buttons: Engineered a custom `RoundedButton` Canvas class to bypass sharp Windows defaults. Replaced flat native buttons with custom rounded buttons that dynamically shift glow colors.
- **Contextual Rendering**: The "Render Media!" button background now matches the gradient "S" in the title text. It is now fully dynamic. It checks the source file extension and generates standard static image outputs for things like `.jpg`/`.png` using Pillow, but builds full video composites for `.mp4`/`.gif` using FFmpeg.

### Fixed (Bugs)
- **FFmpeg Subprocess Audio Crash**: Fixed a massive bug where attempting to render source video with audio would instantly crash. By migrating the map arguments out of generic dictionary kwargs and back to strict command line `subprocess.Popen` execution, audio streams are now handled flawlessly without breaking the filter mappings.
- **Infinite Space Padding Loop**: Resolved an issue where compositing a video onto a black padding background would cause FFmpeg to render infinitely into empty black frames. Fixed by applying the `:shortest=1` overlay modifier, ensuring the final clip terminates exactly when the source frames end.
- **Negative OS Space Coordinate Glitch**: Rewrote the 2D bounding box logic to mathematically anchor the minimum X/Y values to Zero. Previously, monitors existing to the left or above the main Windows display (resulting in negative `os_x` or `os_y` integers) would clip out of bounds when rendering.
- **Drag-and-Drop Whitespace Parsing**: Fixed an issue where the `tkinterdnd2` module crashed on Windows filepaths containing spaces (which injects encapsulating `{}` brackets). The application now utilizes `splitlist` for native filepath decoding. It also universally accepts 15+ variations of Image and Video media natively.
