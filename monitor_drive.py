import os
import json
import base64
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Get the base64 encoded service account JSON from the environment variable
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
service_account_base64 = os.environ["SERVICE_ACCOUNT_JSON_BASE64"]

# Decode the base64 string
service_account_json = base64.b64decode(service_account_base64).decode("utf-8")

# Parse the decoded JSON
service_account_info = json.loads(service_account_json)

# Load credentials and setup API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# JSON file for tracking notified files
NOTIFIED_FILES_JSON = "notified_files.json"

# Load folder ID from config
CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file '{CONFIG_FILE}' not found.")
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON in config file: {e}")

# Load notified files from JSON
def load_notified_files():
    if not os.path.exists(NOTIFIED_FILES_JSON):
        return set()
    try:
        with open(NOTIFIED_FILES_JSON, "r") as file:
            return set(json.load(file))
    except json.JSONDecodeError:
        print("Error decoding JSON. Resetting notified files.")
        return set()

# Save notified files to JSON
def save_notified_files(notified_files):
    try:
        with open(NOTIFIED_FILES_JSON, "w") as file:
            json.dump(sorted(notified_files), file, indent=4)
    except Exception as e:
        print(f"Failed to save notified files: {e}")
        raise

def check_new_files(folder_id, notified_files):
    """Check for new files in the folder and return unsent files."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(
        q=query, fields="files(id, name, mimeType, createdTime)"
    ).execute()
    files = results.get('files', [])
    new_files = [file for file in files if file['id'] not in notified_files]
    return sorted(new_files, key=lambda x: x['createdTime'])

def notify_discord(item_name, item_id, mime_type):
    """Send a notification to Discord for a new file or folder."""
    if mime_type == "application/vnd.google-apps.folder":
        view_link = f"https://drive.google.com/drive/folders/{item_id}"
        download_link = view_link
        item_type = "Folder"
        emoji = "📁"
    else:
        view_link = f"https://drive.google.com/file/d/{item_id}/view"
        download_link = f"https://drive.google.com/uc?id={item_id}&export=download"
        item_type = "File"
        emoji = "📄"

    message = {
        "embeds": [
            {
                "title": f"{emoji} New {item_type} Uploaded",
                "description": f"**{item_name}**",
                "color": 0x5865F2,
                "fields": [
                    {"name": "🔗 View", "value": f"[Open {item_type}]({view_link})", "inline": True},
                    {"name": "⬇️ Download", "value": f"[Download {item_type}]({download_link})", "inline": True}
                ]
            }
        ]
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=message)
    if response.status_code == 204:
        print(f"Successfully notified Discord about: {item_name}")
    else:
        print(f"Failed to notify Discord. Response: {response.text}")

if __name__ == "__main__":
    config = load_config()
    FOLDER_ID = config.get("folder_id")
    if not FOLDER_ID:
        raise ValueError("Folder ID is missing in the configuration file.")

    notified_files = load_notified_files()

    try:
        new_files = check_new_files(FOLDER_ID, notified_files)
        for file in new_files:
            notify_discord(file['name'], file['id'], file['mimeType'])
            notified_files.add(file['id'])
    finally:
        print("Saving notified files...")
        save_notified_files(notified_files)
        print("Notified files successfully saved.")
