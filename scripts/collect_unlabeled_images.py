# Owner: HAWRAA
"""
Streams 48 images from the RVL-CDIP test split (3 per class, balanced)
and saves them with neutral filenames so they can be labeled without hints.

Outputs:
  app/classifier/eval/to_label/img_001.tiff  ...  img_048.tiff
  app/classifier/eval/to_label/manifest.json   ← RVL-CDIP ground truth kept
                                                  for post-labeling comparison
                                                  (NOT shown in labeling UI)
Run from project root:
  PYTHONPATH=. python scripts/collect_unlabeled_images.py
"""

import json
from pathlib import Path

from datasets import load_dataset

CLASSES = [
    "letter", "form", "email", "handwritten", "advertisement",
    "scientific_report", "scientific_publication", "specification",
    "file_folder", "news_article", "budget", "invoice",
    "presentation", "questionnaire", "resume", "memo",
]

PER_CLASS_TARGET = 3
MAX_SCAN = 5_000
OUT_DIR = Path("app/classifier/eval/golden_images")
MANIFEST = Path("app/classifier/eval/to_label/manifest.json")


def main() -> None:
    if MANIFEST.exists():
        print(f"Images already collected at {OUT_DIR}/")
        print("Delete the folder and re-run to recollect.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {c: 0 for c in CLASSES}
    entries: list[dict] = []
    scanned = 0
    img_index = 1

    print("Streaming RVL-CDIP test split (no model filtering — you label these)...")
    dataset = load_dataset("aharley/rvl_cdip", split="test", streaming=True, trust_remote_code=True)

    for example in dataset:
        if scanned >= MAX_SCAN:
            print(f"Reached scan limit ({MAX_SCAN}).")
            break

        gt = CLASSES[example["label"]]

        if counts[gt] >= PER_CLASS_TARGET:
            scanned += 1
            continue

        filename = f"img_{img_index:03d}.tiff"
        example["image"].save(OUT_DIR / filename, format="TIFF")

        # Store RVL-CDIP ground truth in manifest — NOT exposed in labeling UI
        entries.append({"filename": filename, "rvlcdip_gt": gt})

        counts[gt] += 1
        img_index += 1
        scanned += 1

        print(f"  saved {filename}  (hidden gt: {gt})  [{sum(counts.values())}/48]")

        if all(v >= PER_CLASS_TARGET for v in counts.values()):
            break

    with open(MANIFEST, "w") as f:
        json.dump(entries, f, indent=2)

    print(f"\nDone. {len(entries)} images saved to {OUT_DIR}/")
    print("Run  PYTHONPATH=. python scripts/label_golden_set.py  to start labeling.")


if __name__ == "__main__":
    main()
