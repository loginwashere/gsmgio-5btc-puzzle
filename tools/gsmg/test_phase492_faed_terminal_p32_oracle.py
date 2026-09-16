import base64
import hashlib
import unittest

import phase492_faed_terminal_p32_oracle as phase492


class Phase492Tests(unittest.TestCase):
    def test_exact_candidate_universe(self):
        rows, hashes = phase492.source_candidates()
        self.assertEqual(len(rows), 10)
        self.assertEqual(set(hashes), {"width30", "width19"})
        self.assertEqual(sum(row["width"] == 30 for row in rows), 4)
        self.assertEqual(sum(row["width"] == 19 for row in rows), 6)

    def test_only_phase410_password_form(self):
        rows, _ = phase492.source_candidates()
        for row in rows:
            preimage = base64.b64decode(row["preimage_b64"], validate=True)
            password = base64.b64decode(row["password_b64"], validate=True)
            self.assertEqual(password,
                             hashlib.sha256(preimage).hexdigest().encode("ascii"))
            self.assertEqual(len(password), 64)

    def test_self_test(self):
        self.assertTrue(phase492.self_test()["positive_control"])


if __name__ == "__main__":
    unittest.main()
