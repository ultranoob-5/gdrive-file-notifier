# Google Drive Notification Bot
A Python-based tool to monitor Google Drive and send notifications to Discord using Google APIs and a Discord webhook.

## Features
- Monitor Google Drive for changes like new files or updates.
- Notify a Discord channel via webhook with detailed information.
- Easily deployable through GitHub Actions.
- Keyless authentication via Google Workload Identity Federation — no service account JSON keys required.

## Installation

### Prerequisites

1. **Google Cloud Project**:
   - Create or use an existing project in the [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Google Drive API**:
```bash
     gcloud services enable drive.googleapis.com
```

2. **Google Cloud Setup (Workload Identity Federation)**:

   Run the following commands in [Google Cloud Shell](https://shell.cloud.google.com/):

   a. Create a service account:
```bash
   gcloud iam service-accounts create "gdrive-notify-sa" \
     --display-name="GDrive Notify Service Account"
```

   b. Create a Workload Identity Pool:
```bash
   gcloud iam workload-identity-pools create "github-pool" \
     --location="global" \
     --display-name="GitHub Actions Pool"
```

   c. Create an OIDC provider (replace `YOUR_GITHUB_USERNAME/YOUR_REPO`):
```bash
   gcloud iam workload-identity-pools providers create-oidc "github-provider" \
     --location="global" \
     --workload-identity-pool="github-pool" \
     --display-name="GitHub Provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
     --attribute-condition="assertion.repository=='YOUR_GITHUB_USERNAME/YOUR_REPO'" \
     --issuer-uri="https://token.actions.githubusercontent.com"
```

   d. Bind the service account to the pool (replace `YOUR_PROJECT_NUMBER` and `YOUR_GITHUB_USERNAME/YOUR_REPO`):
```bash
   gcloud iam service-accounts add-iam-policy-binding "gdrive-notify-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_USERNAME/YOUR_REPO"
```

   e. Share the Google Drive folder with the service account:
   - Open the folder in [Google Drive](https://drive.google.com).
   - Click **Share** and add `gdrive-notify-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com` as a **Viewer**.

3. **Discord Webhook**:
   - Create a webhook in your desired Discord channel. Learn more [here](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

---

### GitHub Setup

1. Fork the repository:
   - Click the **Fork** button at the top right corner of this repository.

2. Add GitHub Secret:
   - Navigate to **Settings > Secrets and variables > Actions > New repository secret**.
   - Add the following secret:
     - `DISCORD_WEBHOOK_URL`: Your Discord webhook URL.

3. Update the workflow file (`.github/workflows/monitor.yml`):
   - Replace `YOUR_PROJECT_NUMBER` and `YOUR_PROJECT_ID` with your actual GCP values:
```yaml
   - uses: google-github-actions/auth@v2
     with:
       workload_identity_provider: 'projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
       service_account: 'gdrive-notify-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com'
```

4. Enable GitHub Actions:
   - Go to the **Actions** tab in your forked repository.
   - Enable workflows to automatically run the script.

5. Update `config.json` with the folder IDs you want to monitor:
```json
   {
       "folder_ids": [
           "your_first_google_drive_folder_id",
           "your_second_google_drive_folder_id"
       ]
   }
```
   > The folder ID is the part of the Google Drive URL after `/folders/`.

---

## How It Works
1. GitHub Actions runs the script on a schedule (every 6 hours) or on every push to `main`.
2. The script authenticates to Google Cloud using Workload Identity Federation — no static keys involved.
3. It checks the configured Drive folders for new files.
4. Any new files are sent as Discord notifications via webhook.
5. Notified file IDs are saved to `notified_files.json` and committed back to the repo to prevent duplicate notifications.