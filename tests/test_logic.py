import ast
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('detection_core', ROOT/'inference/detection_core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

class LogicTests(unittest.TestCase):
    def test_checkpoint_order_does_not_become_wire_order(self):
        names = core.class_mapping(['wolf', 'tiger', 'monkey', 'peacock', 'elephant'])
        self.assertEqual(core.CODES[names[0]], '03')
        self.assertEqual(core.CODES[names[4]], '01')
        self.assertEqual(core.class_mapping(dict(enumerate(reversed(list(names.values())))))[0], 'elephant')
        with self.assertRaises(ValueError):
            core.class_mapping(['person']*5)

    def test_zero_vote_drops_stale_position_and_keeps_all_classes(self):
        counts = [{n: 0 for n in core.OUTPUT_ORDER} for _ in range(5)]
        offsets = [{n: [] for n in core.OUTPUT_ORDER} for _ in range(5)]
        counts[0]['wolf'] = 1
        offsets[0]['wolf'] = [(10,20)]
        result = core.summarize(counts, offsets)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[2]['count'], 0)
        self.assertIsNone(result[2]['mean_offset_cm'])

    def test_class_means_are_not_mixed(self):
        counts = [{n: int(n in ('wolf','tiger')) for n in core.OUTPUT_ORDER} for _ in range(5)]
        offsets = [{n: ([(2,4)] if n=='wolf' else [(10,12)] if n=='tiger' else []) for n in core.OUTPUT_ORDER} for _ in range(5)]
        result = core.summarize(counts, offsets)
        self.assertEqual(result[1]['mean_offset_cm'], [10,12])
        self.assertEqual(result[2]['mean_offset_cm'], [2,4])

    def test_fixed_height_roi_has_expected_scale(self):
        tree = ast.parse((ROOT/'inference/ros_publisher.py').read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='get_center_roi')
        namespace = {}
        exec(compile(ast.Module(body=[node],type_ignores=[]), '<roi>', 'exec'),namespace)
        roi = namespace['get_center_roi'](1280,720,600,600,120,50)
        self.assertEqual(roi, (515,235,765,485))
        self.assertEqual((690-(roi[0]+roi[2])//2)*50/(roi[2]-roi[0]),10)

    def test_model_copy_matches_source_checksum(self):
        expected = (ROOT/'models/SHA256SUMS').read_text().split()[0]
        self.assertEqual(hashlib.sha256((ROOT/'models/best.pt').read_bytes()).hexdigest(),expected)

if __name__ == '__main__':
    unittest.main()
