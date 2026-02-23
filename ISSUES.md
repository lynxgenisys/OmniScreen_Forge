# 🚨 Project Issues & Alerts Tracker 🚨

*I will use this file to document any sudden pipeline breaks, missing files, or critical architecture issues I encounter while building. If I point you to this file, it means something requires your explicit attention or a manual asset drop.*

## Resolved Issues

**[2026-02-22] Missing Gradient Morals Logo Incident**
- **Status**: FIXED
- **Details**: The application encountered a fatal missing-file exception because the master `GradMorls-Logo.png` asset was abruptly missing from the directory prior to compilation.
- **Action Taken**: I temporally hot-swapped the UI mapping to a backup `.jpg` file found in the directory just to keep the application from hard-crashing on boot so you could see the Advanced UI. You have since restored the correct `.png` and the code has been permanently reverted to the master path.
