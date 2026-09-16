import tempfile
import unittest
from pathlib import Path

import phase496_depth10_iteration_rescore as phase496


class Phase496Tests(unittest.TestCase):
    def test_self_test(self):
        result = phase496.self_test()
        self.assertFalse(result["faed_scored"])
        self.assertTrue(result["inputs_verified"])
        self.assertEqual(result["iterations"], 10000)

    def test_refuses_existing_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "result.json").write_text("{}\n")
            with self.assertRaises(FileExistsError):
                phase496.run(root)


if __name__ == "__main__":
    unittest.main()
