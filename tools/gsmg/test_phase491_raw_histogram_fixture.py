import collections
import unittest

import phase484a_raw_symbol_vic_solver as base
import phase491_raw_histogram_fixture as rawonly


class Phase491FixtureTests(unittest.TestCase):
    def test_profile_uses_raw_counts_only(self):
        profile = rawonly.sampled_token_profile(0)
        reconstructed = collections.Counter()
        for code, count in profile["token_counts"].items():
            for symbol in code:
                reconstructed[symbol] += count
        self.assertEqual(reconstructed, collections.Counter(rawonly.RAW_COUNTS))

    def test_fixture_round_trip_and_histogram(self):
        fixture = rawonly.make_fixture(0)
        rawonly.verify_fixture(fixture)
        restored = base.Geometry(570, 19).decrypt(
            fixture["observed"], fixture["order"])
        self.assertEqual(restored, fixture["raw"])
        self.assertEqual(collections.Counter(restored),
                         collections.Counter(rawonly.RAW_COUNTS))

    def test_token_counts_are_outputs_not_frozen_436(self):
        counts = [rawonly.sampled_token_profile(i)["token_count"]
                  for i in range(5)]
        self.assertGreater(len(set(counts)), 1)

    def test_source_regions_are_distinct_for_first_ten(self):
        regions = [rawonly.source_region("dev", i) for i in range(10)]
        self.assertEqual(len(regions), len(set(regions)))

    def test_deterministic(self):
        first = rawonly.make_fixture(0)
        rawonly.make_fixture.cache_clear()
        second = rawonly.make_fixture(0)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
