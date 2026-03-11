"""
insert_proposal_images.py

Inserts screenshots from residency notes into the Call & Shift Patterns
and Clinic Template Expansion Google Docs proposals.

For each image:
  1. Uploads to Google Drive (temp public file)
  2. Finds the anchor heading/text in the document
  3. Inserts the image + caption after it

Usage:
  python3 insert_proposal_images.py
"""

import sys
import struct
import time
import io
from pathlib import Path

sys.path.insert(0, '/Users/chriskim/google-services')
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from google_client import _get_credentials

creds = _get_credentials()
docs_svc  = build('docs', 'v1', credentials=creds)
drive_svc = build('drive', 'v3', credentials=creds)

DOC1 = '16vNPIof661-X22W9gSmKzt7neB5TkxYa2E9LYVNsQKI'  # Call & Shift Patterns
DOC2 = '1_FmsFlppKNhrHxEZE2LE1OIghwEHBOTzUxRcanLgFks'  # Clinic Template Expansion

SCREENSHOTS = Path("/Users/chriskim/notes/residency/user-journeys/screenshots")

# ── Image plan ────────────────────────────────────────────────────────────────
# Each entry: (doc_id, anchor_text, image_filename, caption, insert_position)
# insert_position: 'after_heading' = right after the heading paragraph
#                  'after_section'  = after the next paragraph block following the heading
IMAGE_PLAN = [
    # ── DOC 1: Call & Shift Patterns ─────────────────────────────────────────
    (
        DOC1,
        "RELATED UI/UX DESIGNS AND INTERACTIONS",
        "manager-rules-templates.png",
        "Rules & Templates today — Auto Assignment, Availability Rule, Clinic Template, and Target Rule are the only rule types available. Call & Shift Patterns doesn't exist yet; this is where it will appear.",
        "after_heading",
    ),
    (
        DOC1,
        "What the feature needs to support",
        "manager-services-call.png",
        "Call Services in Amion Next — each row is a candidate for a named pattern. Programs like ARMC have 20+ call service rows that today require entry-by-entry manual scheduling.",
        "after_heading",
    ),
    (
        DOC1,
        "Pattern links:",
        "viewer-call-calendar.png",
        "Viewer call calendar — dense rows with no visual indicator of which assignments belong to the same pattern vs. which were entered manually. Pattern links make this readable.",
        "after_section",
    ),

    # ── DOC 2: Clinic Template Expansion ─────────────────────────────────────
    (
        DOC2,
        "RELATED UI/UX DESIGNS AND INTERACTIONS",
        "manager-clinic-templates-panel.png",
        "Clinic Templates today — the panel shows the existing template rule. Weekly and biweekly cadences only, no 4-week cycle option, no cancel rule integration.",
        "after_heading",
    ),
    (
        DOC2,
        "4-Week Block Cadence:",
        "manager-services-clinics.png",
        "Clinic Services in Amion Next — programs like ARMC maintain 50+ distinct clinics. The 4-week cadence extension must work across any combination of these service configurations.",
        "after_section",
    ),
]


def png_dimensions(path: Path):
    """Read width, height from PNG header bytes 16-24."""
    with open(path, 'rb') as f:
        f.read(16)
        w = struct.unpack('>I', f.read(4))[0]
        h = struct.unpack('>I', f.read(4))[0]
    return w, h


def upload_to_drive(image_path: Path) -> str:
    """Upload image to Drive, make public, return a URL Google Docs API can fetch."""
    print(f"  Uploading {image_path.name} to Drive...")
    meta = {"name": f"proposal-image-{image_path.name}", "mimeType": "image/png"}
    media = MediaFileUpload(str(image_path), mimetype="image/png")
    file = drive_svc.files().create(body=meta, media_body=media, fields="id").execute()
    fid = file["id"]
    # Make publicly readable so Google Docs API can fetch it
    drive_svc.permissions().create(
        fileId=fid,
        body={"role": "reader", "type": "anyone"},
    ).execute()
    # Use the direct download URL
    url = f"https://drive.google.com/uc?id={fid}&export=view"
    print(f"    → Drive file ID: {fid}")
    return url, fid


def find_paragraph_end(doc_content, anchor_text, after_next=False):
    """
    Scan doc body content for a paragraph containing anchor_text.
    Returns the endIndex of:
      - that paragraph (after_next=False)
      - the paragraph immediately following it (after_next=True)
    Returns None if not found.
    """
    paragraphs = [e for e in doc_content if e.get('paragraph')]
    for i, elem in enumerate(paragraphs):
        para = elem['paragraph']
        text = ''.join(
            r.get('textRun', {}).get('content', '')
            for r in para.get('elements', [])
        )
        if anchor_text in text:
            if after_next and i + 1 < len(paragraphs):
                return paragraphs[i + 1]['endIndex']
            return elem['endIndex']
    return None


def insert_image_with_caption(doc_id, anchor_text, image_url, caption, insert_after_next, width_px, height_px):
    """Insert image + caption into doc after the paragraph matching anchor_text."""
    doc = docs_svc.documents().get(documentId=doc_id).execute()
    content = doc['body']['content']

    insert_idx = find_paragraph_end(content, anchor_text, after_next=insert_after_next)
    if insert_idx is None:
        print(f"  WARNING: Could not find anchor '{anchor_text[:50]}' in doc {doc_id}")
        return

    # Scale image to max width of 500pt (≈ 667px at 96dpi)
    max_w_pt = 480
    ratio = height_px / width_px
    img_w_pt = min(max_w_pt, width_px * 0.75)  # rough px→pt
    img_h_pt = img_w_pt * ratio

    requests = [
        # 1. Insert caption text paragraph after anchor
        {
            "insertText": {
                "location": {"index": insert_idx},
                "text": caption + "\n",
            }
        },
        # 2. Insert image before caption (at same index — will push caption down)
        {
            "insertInlineImage": {
                "location": {"index": insert_idx},
                "uri": image_url,
                "objectSize": {
                    "width":  {"magnitude": img_w_pt, "unit": "PT"},
                    "height": {"magnitude": img_h_pt, "unit": "PT"},
                },
            }
        },
    ]

    # Apply italic + small font to caption (it's at insert_idx + image_width_chars + 1)
    # We do this in a second call after we know the final indices
    docs_svc.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": requests}
    ).execute()

    # Style the caption: italic, 9pt — fetch updated doc to get new indices
    time.sleep(0.5)
    doc2 = docs_svc.documents().get(documentId=doc_id).execute()
    content2 = doc2['body']['content']
    # Find the caption paragraph (contains the caption text)
    caption_snippet = caption[:30]
    cap_start = cap_end = None
    for elem in content2:
        if not elem.get('paragraph'):
            continue
        text = ''.join(
            r.get('textRun', {}).get('content', '')
            for r in elem['paragraph'].get('elements', [])
        )
        if caption_snippet in text:
            # Get the range of just the text (exclude trailing newline)
            cap_start = elem['startIndex']
            cap_end   = elem['endIndex'] - 1
            break

    if cap_start is not None:
        docs_svc.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [
                {
                    "updateTextStyle": {
                        "range": {"startIndex": cap_start, "endIndex": cap_end},
                        "textStyle": {"italic": True, "fontSize": {"magnitude": 9, "unit": "PT"}},
                        "fields": "italic,fontSize",
                    }
                }
            ]}
        ).execute()


def cleanup_drive_files(file_ids):
    """Delete temp Drive files after insertion."""
    for fid in file_ids:
        try:
            drive_svc.files().delete(fileId=fid).execute()
            print(f"  Cleaned up Drive file {fid}")
        except Exception as e:
            print(f"  Could not delete {fid}: {e}")


def main():
    uploaded = {}  # image_name → (url, fid)
    fids_to_cleanup = []

    # Pre-upload all unique images
    needed = set(row[2] for row in IMAGE_PLAN)
    for img_name in needed:
        path = SCREENSHOTS / img_name
        if not path.exists():
            print(f"SKIP (not found): {img_name}")
            continue
        url, fid = upload_to_drive(path)
        uploaded[img_name] = (url, fid)
        fids_to_cleanup.append(fid)

    # Insert into docs
    for doc_id, anchor, img_name, caption, position in IMAGE_PLAN:
        if img_name not in uploaded:
            print(f"SKIP insert (image not uploaded): {img_name}")
            continue

        path = SCREENSHOTS / img_name
        w, h = png_dimensions(path)
        url = uploaded[img_name][0]
        after_next = (position == "after_section")

        doc_label = "Call & Shift Patterns" if doc_id == DOC1 else "Clinic Template Expansion"
        print(f"\nInserting {img_name} into [{doc_label}] after '{anchor[:40]}...'")
        insert_image_with_caption(doc_id, anchor, url, caption, after_next, w, h)
        time.sleep(1)  # rate limit buffer

    print("\nAll images inserted.")
    print(f"\nDOC1: https://docs.google.com/document/d/{DOC1}/edit")
    print(f"DOC2: https://docs.google.com/document/d/{DOC2}/edit")

    # Note: Drive files stay public so Google Docs can render them.
    # If you want to clean up later, run:
    #   python3 -c "import insert_proposal_images as m; m.cleanup_drive_files({file_ids})"
    print(f"\nDrive file IDs (keep public for Docs rendering): {fids_to_cleanup}")


if __name__ == "__main__":
    main()
