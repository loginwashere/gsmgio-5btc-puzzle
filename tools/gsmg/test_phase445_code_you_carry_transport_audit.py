#!/usr/bin/env python3
"""Tests for the frozen Phase 445 CODE YOU CARRY transport audit."""

import phase445_code_you_carry_transport_audit as phase445


def test_phase445_self_test_passes():
    phase445.self_test()


def test_phase445_native_graph_and_carrier_gates():
    report = phase445.audit()
    nodes = {node["id"]: node for node in report["nodes"]}
    assert len(nodes) == 13
    assert nodes["raw_encoded_321"]["native_consumed"] is True
    assert nodes["cp1141_ciphertext"]["native_consumed"] is True
    assert nodes["validation_num"]["native_consumed"] is True
    assert nodes["answer_321"]["carrier_eligible"] is True
    assert nodes["answer_322"]["carrier_eligible"] is True
    assert nodes["p32_envelope"]["carrier_eligible"] is False


def test_phase445_stops_without_unique_binding_or_oracle():
    report = phase445.audit()
    assert report["eligible_carried_outputs"] == ("answer_321", "answer_322")
    assert report["established_consumer_binding_count"] == 0
    assert report["unique_transport_edge_selected"] is False
    assert report["decision"] == "two_native_carriers_no_established_consumer_binding"
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
    assert report["docker_touched"] is False
