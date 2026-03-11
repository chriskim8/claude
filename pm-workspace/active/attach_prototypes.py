"""
attach_prototypes.py

Uploads prototype screenshots to Google Drive and embeds them into two
Google Docs product proposals with captions.
"""

import os
import sys
import struct
import io
import requests

sys.path.insert(0, os.path.expanduser("~/google-services"))

from google_client import _get_credentials, get_drive_service
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CLINIC_DOC_ID = "1_FmsFlppKNhrHxEZE2LE1OIghwEHBOTzUxRcanLgFks"
CALL_SHIFT_DOC_ID = "16vNPIof661-X22W9gSmKzt7neB5TkxYa2E9LYVNsQKI"

BASE = "/Users/chriskim/pm-workspace/active"

CLINIC_SCREENSHOTS = [
    (
        f"{BASE}/clinic-ux-prototype/screenshots/02-revised-weekly.png",
        "Revised weekly clinic modal — coordinator language, scope selector, plain-English summary",
    ),
    (
        f"{BASE}/clinic-ux-prototype/screenshots/03-revised-4week.png",
        "4-week cadence — week × day table replaces fragmented week tabs + day pills",
    ),
    (
        f"{BASE}/cancel-rules-prototype/screenshots/02-simple-cancel.png",
        "Cancel clinic rule — WHEN/THEN/FOR builder, simple case (post-call trigger)",
    ),
    (
        f"{BASE}/cancel-rules-prototype/screenshots/03-advanced-cancel.png",
        "Cancel clinic rule — advanced case (rotation-based trigger, training-level scope)",
    ),
]
CLINIC_PROTO_PATH = "file:///Users/chriskim/pm-workspace/active/clinic-ux-prototype/index.html"

CALL_SHIFT_SCREENSHOTS = [
    (
        f"{BASE}/call-shift-prototype/screenshots/02-define-pattern.png",
        "Define pattern — visual cadence selector with 14-day strip previews, rotation-scoped trigger",
    ),
    (
        f"{BASE}/call-shift-prototype/screenshots/03-apply-pattern.png",
        "Apply pattern — anchor date, scope selector, conflict detection before confirmation",
    ),
    (
        f"{BASE}/call-shift-prototype/screenshots/04-calendar-result.png",
        "Calendar result — Q3 pattern applied, green = new assignments, yellow = conflicts flagged inline",
    ),
]
CALL_SHIFT_PROTO_PATH = "file:///Users/chriskim/pm-workspace/active/call-shift-prototype/index.html"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_png_dimensions(path: str) -> tuple[int, int]:
    """Read width, height from PNG header bytes 16-24."""
    with open(path, "rb") as f:
        f.seek(16)
        data = f.read(8)
    width = struct.unpack(">I", data[0:4])[0]
    height = struct.unpack(">I", data[4:8])[0]
    return width, height


def upload_image(drive, path: str) -> str:
    """Upload a PNG to Drive, make it public, return file ID."""
    name = os.path.basename(path)
    file_metadata = {"name": name, "mimeType": "image/png"}
    media = MediaFileUpload(path, mimetype="image/png")
    file = drive.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = file["id"]
    # Make public
    drive.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()
    print(f"  Uploaded {name} → {file_id}")
    return file_id


def get_image_url(drive, file_id: str) -> str:
    """Return the direct download URL for a Drive file."""
    file = drive.files().get(fileId=file_id, fields="webContentLink").execute()
    return file["webContentLink"]


def download_bytes(url: str, creds) -> bytes:
    """Download file bytes from a URL, authenticated with OAuth token."""
    token = creds.token
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.content


def get_doc_end_index(docs, doc_id: str) -> int:
    """Return the last valid insert index in the doc body (endIndex - 1)."""
    doc = docs.documents().get(documentId=doc_id).execute()
    body_content = doc["body"]["content"]
    # endIndex of the last element minus 1 (exclude trailing newline sentinel)
    end_index = body_content[-1]["endIndex"] - 1
    return end_index


def build_insert_requests(
    docs,
    doc_id: str,
    screenshots: list[tuple[str, str]],
    drive,
    creds,
    proto_path: str,
) -> list[dict]:
    """
    Build a list of batchUpdate requests to append a heading, intro paragraph,
    and one inline image + caption per screenshot.

    We work backwards from the end so indices stay valid.
    """
    # We'll collect (index, request) tuples and sort by index descending
    # Actually, simpler: insert everything at the same end_index in reverse
    # order so each insert pushes subsequent content down correctly.

    requests_list = []

    # Get current end index
    end_index = get_doc_end_index(docs, doc_id)

    # We'll build a list of segments to insert, then convert to requests.
    # Insert order: heading first, then intro, then images.
    # Since each insertion shifts subsequent indices, we insert from the END.

    # Prepare image data
    image_entries = []
    for path, caption in screenshots:
        print(f"  Processing {os.path.basename(path)}...")
        file_id = upload_image(drive, path)
        url = get_image_url(drive, file_id)
        width, height = get_png_dimensions(path)
        image_entries.append({
            "file_id": file_id,
            "url": url,
            "caption": caption,
            "width": width,
            "height": height,
            "path": path,
        })

    # We'll insert at end_index repeatedly. Each insert call shifts the doc,
    # so we need to re-fetch end_index after each insertion.
    # Instead, build all requests with index = end_index and let Google
    # process them in order (each shifts the remaining content).
    # The batchUpdate applies requests sequentially, updating indices.

    # Strategy: insert in reverse order so we can use the same base index.
    # Order of final appearance (top to bottom):
    #   1. "UX Prototype" heading
    #   2. Intro paragraph with proto path
    #   3. For each image: image then caption paragraph
    #
    # To achieve this by inserting at the same index repeatedly (each pushes
    # previous down), we insert in REVERSE order:
    #   Last item first → first item last

    idx = end_index  # all insertions at this index

    segments = []  # (type, data) — will be reversed for insertion

    # 1. Heading
    segments.append(("heading", "UX Prototype"))

    # 2. Intro paragraph
    segments.append(("paragraph", f"Interactive HTML prototype. Open locally: {proto_path}"))

    # 3. Images + captions
    for entry in image_entries:
        segments.append(("image", entry))
        segments.append(("caption", entry["caption"]))

    # Reverse so we insert last segment first (at index idx)
    segments_reversed = list(reversed(segments))

    built_requests = []
    for seg_type, seg_data in segments_reversed:
        if seg_type == "heading":
            # Insert text then apply heading style
            built_requests.append({
                "insertText": {
                    "location": {"index": idx},
                    "text": seg_data + "\n",
                }
            })
            built_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": idx, "endIndex": idx + len(seg_data) + 1},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "fields": "namedStyleType",
                }
            })
        elif seg_type == "paragraph":
            built_requests.append({
                "insertText": {
                    "location": {"index": idx},
                    "text": seg_data + "\n",
                }
            })
            built_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": idx, "endIndex": idx + len(seg_data) + 1},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                    "fields": "namedStyleType",
                }
            })
        elif seg_type == "caption":
            built_requests.append({
                "insertText": {
                    "location": {"index": idx},
                    "text": seg_data + "\n",
                }
            })
            # Italicize caption
            built_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": idx, "endIndex": idx + len(seg_data)},
                    "textStyle": {"italic": True},
                    "fields": "italic",
                }
            })
        elif seg_type == "image":
            # Scale image to max 600px wide
            w = entry["width"]
            h = entry["height"]
            max_w = 600
            if w > max_w:
                scale = max_w / w
                w = int(w * scale)
                h = int(h * scale)

            built_requests.append({
                "insertInlineImage": {
                    "location": {"index": idx},
                    "uri": f"https://drive.google.com/uc?export=download&id={entry['file_id']}",
                    "objectSize": {
                        "width": {"magnitude": w, "unit": "PT"},
                        "height": {"magnitude": h, "unit": "PT"},
                    },
                }
            })

    return built_requests


def process_doc(docs, drive, creds, doc_id, screenshots, proto_path, label):
    print(f"\n{'='*60}")
    print(f"Processing: {label}")
    print(f"Doc ID: {doc_id}")
    print(f"{'='*60}")

    try:
        reqs = build_insert_requests(docs, doc_id, screenshots, drive, creds, proto_path)
        print(f"  Executing batchUpdate with {len(reqs)} requests...")
        result = docs.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": reqs},
        ).execute()
        print(f"  SUCCESS — doc updated. Revision: {result.get('documentId', doc_id)}")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    creds = _get_credentials()
    drive = get_drive_service()
    docs = build("docs", "v1", credentials=creds)

    results = {}

    # Doc 1: Clinic Template Expansion
    ok = process_doc(
        docs, drive, creds,
        CLINIC_DOC_ID,
        CLINIC_SCREENSHOTS,
        CLINIC_PROTO_PATH,
        "Clinic Template Expansion",
    )
    results["Clinic Template Expansion"] = ok

    # Doc 2: Call & Shift Patterns
    ok = process_doc(
        docs, drive, creds,
        CALL_SHIFT_DOC_ID,
        CALL_SHIFT_SCREENSHOTS,
        CALL_SHIFT_PROTO_PATH,
        "Call & Shift Patterns",
    )
    results["Call & Shift Patterns"] = ok

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for label, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {label}: {status}")


if __name__ == "__main__":
    main()
