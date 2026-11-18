"""Port check: rabbit_cryptojs.py against vectors produced by the real crypto-js 4.1.1 library
(generated 2026-10-07 with node; frozen here so the test does not need node)."""
import base64

import numpy as np

import rabbit_cryptojs as r

KEYSTREAM_VECTORS = [
    {
        "alg": "Rabbit",
        "key": "000102030405060708090a0b0c0d0e0f",
        "iv": "0001020304050607",
        "keystream80": "f28919dda128f8f90a30346e9794d2b74c69a2d9913727bc5a3018e6332af7f3be3ac3efb368f43a4cb85867b81c91f924290c816b8b578898c57fb4c0ba05bd9293046b1d02108c04d3806210c95d2c"
    },
    {
        "alg": "RabbitLegacy",
        "key": "000102030405060708090a0b0c0d0e0f",
        "iv": "0001020304050607",
        "keystream80": "69bf3dd75efcf6c05da715440a6b7fd9701dc582af89ab53b28598daef63316fbf76a3269407d12f053b71011ff910451a8e7170306ca52901f13f17c51d09a46c900182c05f8470e34924d63da90b57"
    },
    {
        "alg": "Rabbit",
        "key": "91283bf0a5c11e44d2e39f0a77b6c512",
        "iv": "f0e1d2c3b4a59687",
        "keystream80": "a9a6148458e6d687580d56691c41f4f10b67079e55054049d74f9ee9a8a30b2a27a5f4aa9eff9391932780240fd99a2e10d5dd626538009503964f5f2e0c8db2be4184f00de026779e4d7face6941a20"
    },
    {
        "alg": "RabbitLegacy",
        "key": "91283bf0a5c11e44d2e39f0a77b6c512",
        "iv": "f0e1d2c3b4a59687",
        "keystream80": "075b5c826d7c823a81e191c0013565d5e587e7c4aa520c2b32cc2e9094918e4a8489b23fb346c4cbdba7f7ca635e56aca08a6e8eb9edf217c6414571a00160f4630378b7fc8b18ec0fa084ee76865849"
    },
    {
        "alg": "Rabbit",
        "key": "00000000000000000000000000000000",
        "iv": "0000000000000000",
        "keystream80": "edb70567375dcd7cd89554f85e27a7c68d4adc7032298f7bd4eff504aca6295f668fbf478adb2be51e6cde292b82de2ab48d2ac6565979220ec909a7e75760983924a18eb9e645e6ba0a8a645109e353"
    },
    {
        "alg": "RabbitLegacy",
        "key": "00000000000000000000000000000000",
        "iv": "0000000000000000",
        "keystream80": "edb70567375dcd7cd89554f85e27a7c68d4adc7032298f7bd4eff504aca6295f668fbf478adb2be51e6cde292b82de2ab48d2ac6565979220ec909a7e75760983924a18eb9e645e6ba0a8a645109e353"
    }
]

ENVELOPE_VECTORS = [
    {
        "alg": "Rabbit",
        "passphrase": "causality",
        "plaintext": "Follow the white rabbit. This is a planted CryptoJS Rabbit envelope for the oracle!!",
        "b64": "U2FsdGVkX18BrHc+eIW3tQdtFFtqeATBu4nnJY6nkZTnq8wpmKZ9+Teac35aHYrKRJu6DQwqh0J5bP11XpK9YLO+MtnGnGErfKlAJW14j5EPmgxTVpbK5OK5SQ/yn+gy48u/zQ=="
    },
    {
        "alg": "RabbitLegacy",
        "passphrase": "causality",
        "plaintext": "Follow the white rabbit. This is a planted CryptoJS Rabbit envelope for the oracle!!",
        "b64": "U2FsdGVkX18ZOmCTMOL/wXHw4vwgfIDo4m/qP6ccHpPu5DNXhFCHyj2cinpBMAlQUaNphjkHY+64O4RAKy0SQVBnOkjxDj0v0GW79wG4i822fR1hoXeGQ+tN7Lz7ck0nP1QKWQ=="
    },
    {
        "alg": "Rabbit",
        "passphrase": "eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf",
        "plaintext": "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3 planted WIF-shaped line padding ok",
        "b64": "U2FsdGVkX19AjNZVxGunGOebBPcMyjajD+dLsFq+HREZDMrVm6X3d6jjCfmb7JqwQbElkQVvYXXJkpnOki9DwmmxfZ7GuFPvOFv9QW8Skl+aHr1dCCcwjth40pylUrm/ZIfuDvC3"
    },
    {
        "alg": "RabbitLegacy",
        "passphrase": "eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf",
        "plaintext": "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3 planted WIF-shaped line padding ok",
        "b64": "U2FsdGVkX19z3o3IxqTRaRvGL96zSP9RIMlJgMMMEimQ3kiL7jDiJ4ml2s8pxS81mEVkF5grRuFfn9BztZ4Zzh5NNH31IByCNeF5+JtjiF5OIjQB92VfoF0566LDT9WXiimL1IR+"
    }
]


def test_keystream_matches_cryptojs():
    for t in KEYSTREAM_VECTORS:
        k = np.frombuffer(bytes.fromhex(t["key"]), np.uint8)[None]
        iv = np.frombuffer(bytes.fromhex(t["iv"]), np.uint8)[None]
        n = len(t["keystream80"]) // 2
        got = r.keystream(k, iv, n, legacy=t["alg"] == "RabbitLegacy")[0].tobytes().hex()
        assert got == t["keystream80"], t


def test_passphrase_envelopes_decrypt():
    for e in ENVELOPE_VECTORS:
        raw = base64.b64decode(e["b64"])
        assert raw[:8] == b"Salted__"
        key, iv = r.evp_key_iv(e["passphrase"].encode(), raw[8:16])
        ks = r.keystream(np.frombuffer(key, np.uint8)[None], np.frombuffer(iv, np.uint8)[None], len(raw) - 16,
                         legacy=e["alg"] == "RabbitLegacy")[0].tobytes()
        assert bytes(a ^ b for a, b in zip(raw[16:], ks)).decode() == e["plaintext"], e["alg"]


def test_batch_rows_are_independent():
    keys = np.random.default_rng(1).integers(0, 256, (5, 16), dtype=np.uint8)
    ivs = np.random.default_rng(2).integers(0, 256, (5, 8), dtype=np.uint8)
    batch = r.keystream(keys, ivs, 48)
    for i in range(5):
        assert (r.keystream(keys[i:i + 1], ivs[i:i + 1], 48)[0] == batch[i]).all()
