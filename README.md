# Google Drive Notification Bot

A Python-based tool to monitor Google Drive and send notifications to Discord using Google APIs and a Discord webhook.

## Features

- Monitor Google Drive for changes like new files or updates.
- Notify a Discord channel via webhook with detailed information.
- Easily deployable through GitHub Actions.

## Installation

### Prerequisites

1. **Google Service Account**:
   - Create a Google Service Account via the [Google Cloud Console](https://console.cloud.google.com/).
   - Share access to the monitored Google Drive folder with the service account email.
   - Download the service account JSON file.

2. **Enable Google Drive API**:
   - Visit the [Google Drive API page](https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com).
   - Enable the API for your project.

3. **Discord Webhook**:
   - Create a webhook in your desired Discord channel. Learn more [here](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

### Environment Variables

1. **Required Variables**:
   - `DISCORD_WEBHOOK_URL`: Discord webhook URL.
   - `SERVICE_ACCOUNT_JSON_BASE64`: Base64-encoded string of your service account JSON.

   To encode your service account JSON:
   - Visit [Base64 Encode](https://www.base64encode.org/).
   - Upload or paste your JSON file's content.
   - Copy the encoded string and use it as the value for the `SERVICE_ACCOUNT_JSON_BASE64` variable.

2. **Add Environment Variables to GitHub Secrets**:
   - Navigate to your forked repository on GitHub.
   - Go to **Settings > Secrets and variables > Actions > New repository secret**.
   - Add the following secrets:
     - `DISCORD_WEBHOOK_URL`: Paste your Discord webhook URL.
     - `SERVICE_ACCOUNT_JSON_BASE64`: Paste the Base64-encoded JSON string.

### Steps

1. Fork the repository:
   - Click the "Fork" button at the top right corner of this GitHub repository.

2. Enable GitHub Actions:
   - Go to the "Actions" tab in your forked repository.
   - Enable workflows to automatically run the script.

3. Adjust the folder ID in the configuration file:
   - Open `config.json`.
   - Update the `"folder_id"` field with the Google Drive folder ID you want to monitor.

   Example:
   ```json
   {
       "folder_id": "your_google_drive_folder_id"
   }
