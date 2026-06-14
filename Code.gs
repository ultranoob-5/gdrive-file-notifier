const DISCORD_WEBHOOK_URL = "your_discord_webhook_url_here";
const FOLDER_IDS = [
  "your_google_drive_folder_id_here"
];

function checkNewFiles() {
  const properties = PropertiesService.getScriptProperties();
  const notifiedFiles = new Set(JSON.parse(properties.getProperty("notifiedFiles") || "[]"));

  for (const folderId of FOLDER_IDS) {
    const folder = DriveApp.getFolderById(folderId);
    const folderName = folder.getName();
    const files = folder.getFiles();

    while (files.hasNext()) {
      const file = files.next();
      const fileId = file.getId();

      if (!notifiedFiles.has(fileId)) {
        const success = notifyDiscord(file.getName(), fileId, file.getMimeType(), folderName);
        if (success) {
          notifiedFiles.add(fileId);
        }
      }
    }

    const subfolders = folder.getFolders();
    while (subfolders.hasNext()) {
      const subfolder = subfolders.next();
      const subfolderId = subfolder.getId();

      if (!notifiedFiles.has(subfolderId)) {
        const success = notifyDiscord(subfolder.getName(), subfolderId, "application/vnd.google-apps.folder", folderName);
        if (success) {
          notifiedFiles.add(subfolderId);
        }
      }
    }
  }

  properties.setProperty("notifiedFiles", JSON.stringify([...notifiedFiles]));
}

function notifyDiscord(itemName, itemId, mimeType, folderName) {
  const isFolder = mimeType === "application/vnd.google-apps.folder";
  const emoji = isFolder ? "📁" : "📄";
  const itemType = isFolder ? "Folder" : "File";
  const viewLink = isFolder
    ? `https://drive.google.com/drive/folders/${itemId}`
    : `https://drive.google.com/file/d/${itemId}/view`;
  const downloadLink = isFolder
    ? viewLink
    : `https://drive.google.com/uc?id=${itemId}&export=download`;

  const payload = {
    embeds: [{
      title: `${emoji} New ${itemType} in **${folderName}**`,
      description: `**${itemName}**`,
      color: 0x5865F2,
      fields: [
        { name: "🔗 View", value: `[Open ${itemType}](${viewLink})`, inline: true },
        { name: "⬇️ Download", value: `[Download ${itemType}](${downloadLink})`, inline: true }
      ]
    }]
  };

  const response = UrlFetchApp.fetch(DISCORD_WEBHOOK_URL, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const responseCode = response.getResponseCode();

  if (responseCode === 429) {
    const responseData = JSON.parse(response.getContentText());    
    const retryAfterSeconds = responseData.retry_after || 5;     
    const waitTimeMs = (retryAfterSeconds * 1000) + 500; 

    Logger.log(`Rate limited! Discord requested a pause of ${retryAfterSeconds}s. Sleeping for ${waitTimeMs}ms. Skipping "${itemName}" until the next run.`);
    
    Utilities.sleep(waitTimeMs); 
    
    return false;

  } else if (responseCode >= 200 && responseCode < 300) {
    Logger.log(`Notified Discord: ${itemName}`);
    
    Utilities.sleep(1000); 
    return true; 
    
  } else {
    Logger.log(`Failed to notify "${itemName}". Error code: ${responseCode}. Response: ${response.getContentText()}`);
    return false;
  }
}

function createTrigger() {
  // Delete existing triggers to avoid duplicates
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));

  // Run every minute
  ScriptApp.newTrigger("checkNewFiles")
    .timeBased()
    .everyMinutes(1)
    .create();

  Logger.log("Trigger created.");
}
