import os
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from milenium.modules import logger


SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_service(credentials_path):
    creds = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _find_folder(service, name, parent_id=None):
    q = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    results = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
    items = results.get("files", [])
    return items[0]["id"] if items else None


def ensure_folder(service, name, parent_id=None):
    folder_id = _find_folder(service, name, parent_id)
    if folder_id:
        return folder_id
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        meta["parents"] = [parent_id]
    folder = service.files().create(body=meta, fields="id").execute()
    logger.progress(f"GDRIVE: создана папка {name}")
    return folder["id"]


def upload_single_file(service, local_path, parent_id):
    local_path = str(local_path)
    name = Path(local_path).name
    q = f"name='{name}' and '{parent_id}' in parents and trashed=false"
    existing = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute().get("files", [])
    media = MediaFileUpload(local_path, resumable=True)
    if existing:
        file_id = existing[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        logger.progress(f"GDRIVE: обновлён {name}")
        return file_id
    else:
        meta = {"name": name, "parents": [parent_id]}
        file = service.files().create(body=meta, media_body=media, fields="id").execute()
        logger.progress(f"GDRIVE: загружен {name}")
        return file["id"]


def upload_folder(credentials_path, local_folder, drive_folder_name="milenium_tg_dumps"):
    local_folder = Path(local_folder)
    if not local_folder.exists():
        return {"error": f"Folder not found: {local_folder}"}
    if not Path(credentials_path).exists():
        return {"error": f"Credentials not found: {credentials_path}"}

    service = get_service(credentials_path)
    parent_id = ensure_folder(service, drive_folder_name)

    uploaded = []
    for f in sorted(local_folder.iterdir()):
        if f.is_file():
            try:
                fid = upload_single_file(service, str(f), parent_id)
                uploaded.append({"name": f.name, "id": fid})
            except Exception as e:
                logger.progress(f"GDRIVE: ошибка {f.name}: {e}")

    return {"folder": drive_folder_name, "uploaded": uploaded, "count": len(uploaded)}
