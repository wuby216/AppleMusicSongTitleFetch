# Apple Music Japanese Song Title Retrieval

A robust Python automation tool for macOS that scans your Apple Music playlists and retrieves the original Japanese title, artist, album names. Built to be lightweight, fail-safe, and run silently in the background.

## 🚀 Features

- **Real-time Sync:** Polls your library every 60 seconds to track new additions and removals.
- **Background Persistence:** Uses macOS `launchd` for reliable scheduling without manual intervention.
- **Smart Coalescing:** Automatically handles system sleep and prevents process overlapping.
- **Zero Focus Theft:** Uses the `launch` command to keep the Music app in the background while syncing.

## 🛠️ Requirements

- **Operating System:** macOS Monterey (12.0) or newer.
- **Python:** Version 3.10 or higher.
- **Permissions:** Automation access must be granted for the script to communicate with the Music app.

## 📂 Project Structure

- `main.py`: The primary Python script containing the sync logic and AppleScript bridges.
- `processed_songs.json`: The local database storing your library state (automatically generated).
- `com.user.music_sync.plist`: The macOS launch agent configuration.
- `music_sync.lock`: A temporary file created during execution to prevent duplicate processes.

## 📦 Installation & Setup

## 1. Clone the Repository
```bash
git clone https://github.com/wuby216/AppleMusicSongTitleFetch.git
cd AppleMusicSongTitleFetch
```

## 2. Manual Test Run
Run the script manually once to initialize the `processed_songs.json` file and trigger the macOS "Automation" permission prompt.

```bash
python3 main.py
```

---

## 3. Configure the Launch Agent
Open the `.plist` file and update the `ProgramArguments` with the **absolute path** to your Python executable and `main.py` script. 

> **Note:** Ensure the path points to your specific user directory (e.g., `/Users/yourname/...`).

---

## 4. Deploy the Service
Move the configuration to your `LaunchAgents` folder and load it to begin the 1-minute interval sync:

```bash
cp com.user.music_sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.music_sync.plist
```

---

## 📝 License
This project is licensed under the **MIT License**. Feel free to use and modify for personal use.