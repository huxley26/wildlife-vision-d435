"""Read-only YOLO dataset audit. Missing labels may be intentional background images."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

def audit(root):
    report, hashes = {}, {}
    for split in ('train', 'val'):
        images = [p for p in (root/'images'/split).iterdir()
                  if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp')]
        labels = [p for p in (root/'labels'/split).glob('*.txt') if p.name != 'classes.txt']
        image_stems, label_stems = {p.stem for p in images}, {p.stem for p in labels}
        counts, errors = Counter(), []
        for p in labels:
            for n, line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    fields = line.split()
                    cls = int(fields[0])
                    values = list(map(float, fields[1:]))
                    if (len(fields) != 5 or not 0 <= cls < 5
                        or not all(math.isfinite(v) and 0 <= v <= 1 for v in values)
                        or values[2] <= 0 or values[3] <= 0):
                        raise ValueError('invalid YOLO box')
                    counts[cls] += 1
                except (ValueError, IndexError):
                    errors.append({'file': p.name, 'line': n})
        hashes[split] = {hashlib.sha256(p.read_bytes()).hexdigest() for p in images}
        report[split] = {'images': len(images), 'labels': len(labels),
                         'images_without_labels': len(image_stems-label_stems),
                         'labels_without_images': len(label_stems-image_stems),
                         'boxes_per_class': dict(counts), 'invalid_rows': errors}
    report['exact_image_hash_overlap'] = len(hashes['train'] & hashes['val'])
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.root), ensure_ascii=False, indent=2))
