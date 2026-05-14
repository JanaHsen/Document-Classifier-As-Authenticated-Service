"""
Downloads one sample TIFF from RVL-CDIP for local inference testing.
Saves to app/classifier/eval/golden_images/test.tiff
"""
from pathlib import Path

from datasets import load_dataset

CLASSES = [
    "letter", "form", "email", "handwritten", "advertisement",
    "scientific_report", "scientific_publication", "specification",
    "file_folder", "news_article", "budget", "invoice",
    "presentation", "questionnaire", "resume", "memo"
]

OUT_PATH = Path("app/classifier/eval/golden_images/test.tiff")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

print("Streaming one sample from RVL-CDIP...")
dataset = load_dataset("aharley/rvl_cdip", streaming=True, trust_remote_code=True)
example = next(iter(dataset["test"]))

image = example["image"]
label = CLASSES[example["label"]]

image.save(OUT_PATH, format="TIFF")

print(f"Saved to: {OUT_PATH}")
print(f"Ground truth label: {label}")
print(f"Image size: {image.size}")
print(f"Image mode: {image.mode}")
