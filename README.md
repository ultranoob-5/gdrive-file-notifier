# Google Drive Discord Notifier

A lightweight Google Apps Script that monitors Google Drive folders and sends
real-time notifications to a Discord channel via webhook. No servers, no GitHub
Actions, no API keys — runs entirely within Google's ecosystem for free.

## Features
- Monitors one or more Google Drive folders for new files and subfolders
- Sends Discord notifications with view and download links
- Runs every minute via a time-based trigger
- Persists state via Apps Script Properties — no external storage needed

## Prerequisites
- A Google account with access to [Google Apps Script](https://script.google.com)
- A Discord webhook URL ([how to create one](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))
- The Google Drive folder ID(s) you want to monitor

> **How to find your folder ID**: Open the folder in Google Drive. The ID is
> the part of the URL after `/folders/`.
> Example: `https://drive.google.com/drive/folders/1TzjJpTs...` → ID is `1TzjJpTs...`

## Setup

### 1. Create a new Apps Script project
- Go to [script.google.com](https://script.google.com)
- Click **New Project**
- Name it something like `G-Drive Discord Notifier`

### 2. Add the code
- Delete the default `myFunction()` placeholder
- Copy and paste the contents of `Code.gs` into the editor

### 3. Configure your settings
At the top of the script, update these two values:
```javascript
const DISCORD_WEBHOOK_URL = "your_discord_webhook_url_here";
const FOLDER_IDS = [
  "your_google_drive_folder_id_here"
];
```
To monitor multiple folders, add more IDs to the array:
```javascript
const FOLDER_IDS = [
  "folder_id_one",
  "folder_id_two"
];
```

### 4. Run the initial setup
- In the editor, select `checkNewFiles` from the function dropdown and click **Run**
- This marks all existing files as already notified so you don't get spammed
- Grant the requested permissions when prompted

### 5. Create the trigger
- Select `createTrigger` from the function dropdown and click **Run**
- This sets up a 1-minute time-based trigger for `checkNewFiles`
- Verify it was created under the **Triggers** tab (clock icon on the left)

## How It Works
1. Every minute, `checkNewFiles()` scans each configured folder
2. File IDs are checked against previously notified IDs stored in Script Properties
3. Any new file or subfolder triggers a Discord notification with view and download links
4. The updated list of notified IDs is saved back to Script Properties

## Limitations
- Minimum trigger interval is 1 minute (Google Apps Script limitation)
- Apps Script has a daily execution quota of 90 minutes/day on free accounts —
  at ~2s per run, 1-minute triggers use roughly 48 minutes/day, well within limits
- Does not monitor nested subfolders recursively (only direct children)

## License
MIT