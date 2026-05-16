# Owner: HAWRAA
import json
import sys
from pathlib import Path

import torch

from app.classifier.inference.predictor import load_model, predict

GOLDEN_DIR = Path("app/classifier/eval/golden_images")
GOLDEN_EXPECTED_PATH = Path("app/classifier/eval/golden_expected.json")
CONFIDENCE_TOLERANCE = 1e-6

# golden_expected.json format:
# [
#   {"filename": "img_001.tiff", "label": "presentation", "confidence": 0.9823},
#   ...
# ]
#
# label      = human-decided ground truth (Hawraa)
# confidence = model's confidence at creation time, or null for known model misses
#
# CI behaviour:
#   - confidence != null  →  strict: label AND confidence must match  (regression test)
#   - confidence == null  →  known miss: label mismatch is reported but does NOT exit(1)
#                            exit(1) only if the model STARTS agreeing then later regresses


def run_golden_test() -> None:
    device = torch.device("cpu")  # always CPU for reproducible floats

    model = load_model(device)

    with open(GOLDEN_EXPECTED_PATH) as f:
        expected_entries = json.load(f)

    regressions = []   # previously-passing images that now fail  → CI-blocking
    known_misses = []  # confidence=null images model still gets wrong  → informational
    known_fixed  = []  # confidence=null images model now gets right  → update JSON!

    for entry in expected_entries:
        filename = entry["filename"]
        expected_label = entry["label"]
        expected_confidence = entry["confidence"]

        image_path = GOLDEN_DIR / filename
        result = predict(model, str(image_path), device)

        if expected_confidence is not None:
            # Strict check — this image was passing before
            if result.label != expected_label:
                regressions.append(
                    f"{filename}: label regression — expected '{expected_label}', got '{result.label}'"
                )
            else:
                delta = abs(result.confidence - expected_confidence)
                if delta > CONFIDENCE_TOLERANCE:
                    regressions.append(
                        f"{filename}: confidence delta {delta:.2e} exceeds tolerance {CONFIDENCE_TOLERANCE}"
                    )
        else:
            # Known miss — just track
            if result.label == expected_label:
                known_fixed.append(f"{filename}: now correct ('{result.label}', conf={result.confidence:.4f}) — update JSON")
            else:
                known_misses.append(f"{filename}: gt='{expected_label}'  model='{result.label}'")

    strict_total = sum(1 for e in expected_entries if e["confidence"] is not None)
    known_total  = len(expected_entries) - strict_total

    print(f"Strict (confidence locked): {strict_total - len(regressions)}/{strict_total} pass")
    print(f"Known misses              : {known_total} images (model errors on hard cases)")

    if known_fixed:
        print("\nKnown misses now fixed — run scripts/build_golden_set.py to update confidence:")
        for line in known_fixed:
            print(f"  FIXED: {line}")

    if known_misses:
        print("\nKnown misses still wrong (expected):")
        for line in known_misses:
            print(f"  MISS : {line}")

    if regressions:
        print("\nREGRESSIONS (CI FAIL):")
        for line in regressions:
            print(f"  FAIL : {line}")
        sys.exit(1)

    print(f"\nPASS: no regressions on {strict_total} locked images")


if __name__ == "__main__":
    run_golden_test()
