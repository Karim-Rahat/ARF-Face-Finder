# ARF Face Finder

ARF Face Finder is a private, fully offline Windows application that finds one person's face across hundreds or thousands of local photos. Choose a clear reference face, scan a folder, review similarity-ranked results, then copy selected photos or move them safely to the Windows Recycle Bin.

![ARF Face Finder logo](facefinder_static/arf-logo.png)

## Main use cases

- Find one guest across wedding, graduation, conference, school, or family-event photos.
- Separate one person's photos from a large photographer delivery.
- Review likely duplicates or unwanted photos before removing them.
- Collect every matching photo into a new delivery folder.
- Search nested folders without uploading private images to a cloud service.
- Repeat searches quickly using the local face-embedding cache.

## Features

- Fully offline from the first launch.
- Local OpenCV YuNet face detection and SFace recognition.
- Recursive scanning of folders and subfolders.
- Adjustable match strictness from broad to highly certain.
- Live scan progress and similarity-ranked results.
- Matched-face outline when hovering over a result.
- Individual, Select All, and Shift-click range selection.
- Copy selected photos without overwriting files with the same name.
- Recoverable deletion through the Windows Recycle Bin.
- Cached embeddings make later searches of unchanged photos faster.
- ARF-branded Windows executable, installer, shortcuts, and web interface.

## Privacy and offline behavior

Photos, face embeddings, and search results stay on the computer. No face API, analytics service, account, or internet connection is required. The official OpenCV YuNet and SFace ONNX models are bundled under `assets/models/` and copied to the user's local application-data directory on first launch.

Application data is stored at:

```text
%LOCALAPPDATA%\ARF Face Finder
```

This includes the models, uploaded reference images, and the SQLite embedding cache.

## How to use

1. Launch **ARF Face Finder**.
2. Choose a clear, front-facing reference photo. If several faces are visible, the largest face is used.
3. Enter the complete path to the folder containing the photo collection.
4. Choose match strictness. **Balanced (42%)** is a useful starting point.
5. Click **Find matching photos**.
6. Review the results and select photos individually, use **Select all**, or click one result and Shift-click another to select the full range.
7. Choose **Copy selected** to copy files into another folder, or **Move to Recycle Bin** for recoverable deletion.

Always review matches before deleting photos. Face similarity search can produce false positives or miss faces affected by blur, occlusion, extreme angles, or poor lighting.

## Supported images

- JPG and JPEG
- PNG
- WebP
- BMP
- TIFF

## Run from source on Windows

Requirements:

- Windows 10 or Windows 11, 64-bit
- Python 3.10 or newer

Create an environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r facefinder-requirements.txt
.\.venv\Scripts\python.exe facefinder_windows_offline_v103.py
```

The interface opens at `http://127.0.0.1:5173/` and is accessible only from the local computer.

## Build the offline Windows installer

The build requires PyInstaller, Pillow, and Inno Setup 6. From PowerShell in the project directory:

```powershell
.\build-offline.ps1
```

The generated installer is written to `release/`. Executables and build output are intentionally excluded from Git; build them locally or attach the installer to a GitHub Release.

## Project structure

```text
facefinder.py                         Core scanning server and file operations
facefinder_windows_offline.py         Offline model installation and ARF branding
facefinder_windows_offline_v103.py    Current Windows entry point and selection fixes
facefinder_templates/                 Application HTML
facefinder_static/                    Styles, browser code, and ARF logo
assets/models/                        Bundled YuNet and SFace ONNX models
assets/arf-face-finder.ico            Multi-resolution Windows icon
installer/ARFFaceFinderOffline103.iss Inno Setup configuration
build-offline.ps1                     Reproducible Windows build script
```

## Recognition notes

The similarity percentage is a ranking aid, not a verified identity probability. Results depend on face size, pose, lighting, blur, age differences, and image quality. Lower thresholds return more possible matches; higher thresholds return fewer, more certain candidates.

## Technology

- Python and Flask
- OpenCV YuNet face detector
- OpenCV SFace face recognizer
- NumPy and SQLite
- Send2Trash for recoverable deletion
- PyInstaller and Inno Setup for Windows packaging

## License

No project license has been selected yet. Add a license before redistributing or accepting external contributions.
