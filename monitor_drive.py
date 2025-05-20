import os
import json
import base64
import time # Import time module
import requests
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# JSON file for caching folder names
FOLDER_NAMES_CACHE_JSON = "folder_names_cache.json"

# Load folder ID from config
CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file '{CONFIG_FILE}' not found.")
    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            folder_ids = config.get("folder_ids", [])
            if not isinstance(folder_ids, list) or not folder_ids:
                raise ValueError("Invalid 'folder_ids' in config file. It should be a non-empty list.")
            return folder_ids
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON in config file: {e}")

# Load cached folder names from JSON
def load_cached_folder_names():
    if not os.path.exists(FOLDER_NAMES_CACHE_JSON):
        return {}
    try:
        with open(FOLDER_NAMES_CACHE_JSON, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        print("Error decoding JSON from folder names cache. Returning empty cache.")
        return {}

# Save cached folder names to JSON
def save_cached_folder_names(cached_names):
    try:
        with open(FOLDER_NAMES_CACHE_JSON, "w") as file:
            json.dump(cached_names, file, indent=4)
    except Exception as e:
        print(f"Failed to save folder names cache: {e}")
        # We don't want to raise here, just print an error and continue

def get_folder_name(folder_id, drive_service, cache):
    """Fetch and return the name of a Google Drive folder, using cache if available."""
    if folder_id in cache:
        return cache[folder_id]
    
    try:
        folder_metadata = drive_service.files().get(fileId=folder_id, fields="name").execute()
        folder_name = folder_metadata.get("name", f"Unknown Folder ({folder_id})")
    except Exception as e:
        print(f"Error fetching folder name for {folder_id}: {e}")
        folder_name = f"Unknown Folder ({folder_id})"
    
    cache[folder_id] = folder_name  # Cache the result
    return folder_name

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
            json.dump(sorted(list(notified_files)), file, indent=4) # Ensure notified_files is a list for sorting
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
    return folder_id, [file for file in files if file['id'] not in notified_files]

def notify_discord(item_name, item_id, mime_type, folder_name):
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
                "title": f"{emoji} New {item_type} Uploaded in **{folder_name}**",
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
    start_time = time.time() # Record start time
    
    folder_ids = load_config()
    notified_files = load_notified_files()
    folder_names_cache = load_cached_folder_names() # Load cache

    try:
        # Populate folder_names dictionary using the cache
        folder_names = {}
        for folder_id in folder_ids:
            folder_names[folder_id] = get_folder_name(folder_id, drive_service, folder_names_cache)

        # Use ThreadPoolExecutor for concurrent file checking
        with ThreadPoolExecutor(max_workers=len(folder_ids) if folder_ids else 1) as executor:
            future_to_folder_id = {
                executor.submit(check_new_files, folder_id, notified_files): folder_id 
                for folder_id in folder_ids
            }
            
            for future in as_completed(future_to_folder_id):
                original_folder_id = future_to_folder_id[future]
                try:
                    returned_folder_id, new_files = future.result() 
                    if returned_folder_id in folder_names: 
                        current_folder_name = folder_names[returned_folder_id]
                        for file_item in new_files:
                            print(f"Processing new file: {file_item['name']} in folder: {current_folder_name}")
                            notify_discord(file_item['name'], file_item['id'], file_item['mimeType'], current_folder_name)
                            notified_files.add(file_item['id'])
                    else:
                        print(f"Warning: Folder ID {returned_folder_id} from task result not found in folder_names map.")
                except Exception as exc:
                    print(f"Folder {original_folder_id} generated an exception: {exc}")

    finally:
        print("Saving folder names cache...")
        save_cached_folder_names(folder_names_cache) # Save cache
        print("Folder names cache successfully saved.")
        
        print("Saving notified files...")
        save_notified_files(notified_files)
        print("Notified files successfully saved.")

        end_time = time.time() # Record end time
        elapsed_time = end_time - start_time
        print(f"Total execution time: {elapsed_time:.2f} seconds") # Print elapsed time
