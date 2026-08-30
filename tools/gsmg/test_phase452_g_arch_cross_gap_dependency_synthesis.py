import phase452_g_arch_cross_gap_dependency_synthesis as phase452


def test_self_test_passes():
    phase452.self_test()


def test_verdict_shape():
    result = phase452.synthesize()
    verdict = result["verdict"]
    assert verdict["new_blocking_relationship_found"] is True
    assert verdict["evidentiary_status_changed"] is False
    assert verdict["btcseed_bears_on_arch"] is False
    assert verdict["priority_change_warranted"] is False


if __name__ == "__main__":
    test_self_test_passes()
    test_verdict_shape()
    print("[*] Phase 452 tests passed")
