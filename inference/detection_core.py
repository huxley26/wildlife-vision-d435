"""Pure logic for class mapping and portfolio messages; no hardware imports."""
from collections import Counter

OUTPUT_ORDER = ('elephant', 'tiger', 'wolf', 'monkey', 'peacock')
CODES = {name: f'{index:02d}' for index, name in enumerate(OUTPUT_ORDER, 1)}

def class_mapping(names):
    mapping = dict(names) if isinstance(names, dict) else dict(enumerate(names))
    if set(mapping) != set(range(5)) or set(mapping.values()) != set(OUTPUT_ORDER):
        raise ValueError('Expected exactly five animal classes with integer IDs 0..4')
    return mapping

def summarize(counts_queue, offsets_queue):
    if not counts_queue or len(counts_queue) != len(offsets_queue):
        raise ValueError('Count and offset windows must be nonempty and equally sized')
    records = []
    for name in OUTPUT_ORDER:
        count = Counter(frame[name] for frame in counts_queue).most_common(1)[0][0]
        points = [xy for frame in offsets_queue for xy in frame[name]]
        mean = None
        if count > 0 and points:
            mean = [sum(p[0] for p in points)/len(points), sum(p[1] for p in points)/len(points)]
        records.append({'code': CODES[name], 'name': name, 'count': count, 'mean_offset_cm': mean})
    return records
