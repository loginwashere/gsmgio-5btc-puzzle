#!/usr/bin/env python3
"""Regression tests for Phase 450."""

import phase450_g_prime_consumer_selector_audit as phase450


def test_phase450_mechanics():
    result = phase450.self_test()
    assert result["verdict"] == "consumer_found"
    assert result["fefe_naive_extension"]["value"] == 100
    assert result["fefe_naive_extension"]["matches_target"] is False


if __name__ == "__main__":
    test_phase450_mechanics()
    print("[*] Phase 450 tests passed")
