//! Blob constants copied verbatim from tools/gsmg/data.py (base64 text, not
//! retyped) plus the OpenSSL "Salted__" split, matching cb_common.py's
//! `_load_blob`. Also carries the known-positive Phase 3.2 self-test vector.

pub const MAX_BLOB_CT_LEN: usize = 2432; // PHASE32_SELFTEST (2432) > COSMIC (1328); must match the .cu MAX_BLOB_CT_LEN

pub struct Blob {
    pub tag: &'static str,
    pub salt: [u8; 8],
    pub ciphertext: Vec<u8>,
}

fn b64_decode(s: &str) -> Vec<u8> {
    // Minimal base64 decoder (standard alphabet + padding) -- avoids pulling
    // in a dependency for four fixed constants decoded once at startup.
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut rev = [255u8; 256];
    for (i, &c) in TABLE.iter().enumerate() {
        rev[c as usize] = i as u8;
    }
    let clean: Vec<u8> = s.bytes().filter(|b| !b.is_ascii_whitespace()).collect();
    let mut out = Vec::with_capacity(clean.len() / 4 * 3);
    let mut chunk = [0u8; 4];
    let mut chunk_len = 0usize;
    for &b in &clean {
        if b == b'=' {
            continue;
        }
        chunk[chunk_len] = rev[b as usize];
        assert!(chunk[chunk_len] != 255, "invalid base64 byte {b}");
        chunk_len += 1;
        if chunk_len == 4 {
            out.push((chunk[0] << 2) | (chunk[1] >> 4));
            out.push((chunk[1] << 4) | (chunk[2] >> 2));
            out.push((chunk[2] << 6) | chunk[3]);
            chunk_len = 0;
        }
    }
    if chunk_len >= 2 {
        out.push((chunk[0] << 2) | (chunk[1] >> 4));
    }
    if chunk_len >= 3 {
        out.push((chunk[1] << 4) | (chunk[2] >> 2));
    }
    out
}

fn load_blob(tag: &'static str, b64: &str) -> Blob {
    let raw = b64_decode(b64);
    assert_eq!(&raw[0..8], b"Salted__", "{tag}: missing OpenSSL Salted__ header");
    let mut salt = [0u8; 8];
    salt.copy_from_slice(&raw[8..16]);
    Blob { tag, salt, ciphertext: raw[16..].to_vec() }
}

pub fn load_blobs() -> Vec<Blob> {
    let salph = concat!(
        "U2FsdGVkX186tYU0hVJBXXUnBUO7C0+X4KUWnWkCvoZSxbRD3wNsGWVHefvdrd9z",
        "QvX0t8v3jPB4okpspxebRi6sE1BMl5HI8Rku+KejUqTvdWOX6nQjSpepXwGuN/jJ",
    );
    let p32trailing = concat!(
        "U2FsdGVkX1+0Wl49gnWTyiimluu7V3+vl7st0gUt9sWDzNLxDmlPMsDSiuW2a46z",
        "gKlIi8aaqY5gpJPPEzW1n9n3/26qs4zstWtPKF8Zs/BTNN4IiEh4qu18mdC0NAv4",
    );
    let urlblob = concat!(
        "U2FsdGVkX190yXTj+S5ktZ9+oipQ3LDUKJ0XbUzp26f5mmlbjQeXtcd5HmWo0raK",
        "WHn10xrl6KJjUgXeMbhRz0OyU09YdlaW08KgH386QfcoT7vMg2UXy/e6YTxDqRnZ",
        "3GaeSCS6umpcrrd9/D4GBw==",
    );
    let cosmic = concat!(
        "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",
    );

    vec![
        load_blob("SALPH", salph),
        load_blob("COSMIC", cosmic),
        load_blob("P32TRAILING", p32trailing),
        load_blob("URLBLOB", urlblob),
    ]
}

/// Variant table: 4 KDF kinds x 3 AES key sizes x 5 cipher modes = 60
/// variants (kdf_kind, key_len_bytes, cipher_mode). Order/contents must match
/// what the checkpoint fingerprint hashes and kernels/aes_kdf_oracle.cu's
/// MAX_VARIANTS sizing.
pub const KDF_LEGACY_MD5: i32 = 0;
pub const KDF_LEGACY_SHA1: i32 = 1;
pub const KDF_LEGACY_SHA256: i32 = 2;
pub const KDF_PBKDF2_SHA256: i32 = 3;

/// AES-CBC (Phase 1 scope). AES-ECB (no IV, same PKCS7+structural gate as
/// CBC). AES-CFB/OFB/CTR (no padding, whole body goes to the printable gate
/// -- matches cb_common.py's STREAM_CIPHER_VARIANTS / ECB_CIPHER_VARIANTS).
pub const CIPHER_CBC: i32 = 0;
pub const CIPHER_ECB: i32 = 1;
pub const CIPHER_CFB: i32 = 2;
pub const CIPHER_OFB: i32 = 3;
pub const CIPHER_CTR: i32 = 4;
/// SEED-CBC (Phase 253's thematically-motivated, opt-in cipher family --
/// gsmg.io/theseedisplanted, DBBI's IZLKESEEDQPPEN). Fixed 128-bit key, CBC
/// chaining only (no creator clue supports ECB/stream SEED). Deliberately
/// NOT part of `variant_table()`'s default cross-product, same "opt-in, not
/// silently expanding existing sweeps" discipline Phase 253 itself used --
/// see `seed_variant_table()`.
pub const CIPHER_SEED_CBC: i32 = 5;

pub fn variant_table() -> Vec<(i32, i32, i32)> {
    let mut v = Vec::new();
    for &kdf in &[KDF_LEGACY_MD5, KDF_LEGACY_SHA1, KDF_LEGACY_SHA256, KDF_PBKDF2_SHA256] {
        for &key_len in &[16, 24, 32] {
            for &mode in &[CIPHER_CBC, CIPHER_ECB, CIPHER_CFB, CIPHER_OFB, CIPHER_CTR] {
                v.push((kdf, key_len, mode));
            }
        }
    }
    v
}

/// Opt-in SEED-CBC variant set (4 variants: one per KDF kind, key_len fixed
/// at 16 -- SEED's only key size). Selected via `--seed-cbc` instead of
/// being merged into `variant_table()`.
pub fn seed_variant_table() -> Vec<(i32, i32, i32)> {
    [KDF_LEGACY_MD5, KDF_LEGACY_SHA1, KDF_LEGACY_SHA256, KDF_PBKDF2_SHA256]
        .iter()
        .map(|&kdf| (kdf, 16, CIPHER_SEED_CBC))
        .collect()
}

pub fn variant_label(kdf: i32, key_len: i32, mode: i32) -> String {
    let kdf_name = match kdf {
        KDF_LEGACY_MD5 => "legacy-md5",
        KDF_LEGACY_SHA1 => "legacy-sha1",
        KDF_LEGACY_SHA256 => "legacy-sha256",
        KDF_PBKDF2_SHA256 => "pbkdf2-sha256-10000",
        _ => "unknown",
    };
    if mode == CIPHER_SEED_CBC {
        return format!("{kdf_name}/seed-128-cbc");
    }
    let mode_name = match mode {
        CIPHER_CBC => "cbc",
        CIPHER_ECB => "ecb",
        CIPHER_CFB => "cfb",
        CIPHER_OFB => "ofb",
        CIPHER_CTR => "ctr",
        _ => "unknown",
    };
    format!("{kdf_name}/aes-{}-{mode_name}", key_len * 8)
}

/// Known-positive Phase 3.2 vector (data.PHASE32_BLOB_B64 / PHASE32_PASSWORD)
/// -- the only known-plaintext AES vector for this project's actual decrypt
/// path. Used as the mandatory GPU self-test before any real sweep.
pub const PHASE32_PASSWORD_SHA256_HEX: &str =
    "250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c";
// NOTE: the password itself is SHA256("jacquefrescogiveitjustonesecond
// heisenbergsuncertaintyprinciple") -- cb_common.py feeds the *raw* clue
// concatenation through its own KDF path with digest sha256/key 32, so the
// literal string tested here is the already-hashed clue answer, matching
// PHASE32_PASSWORD = VERIFIED_PRIOR_COMMAND_HASHES["phase32_clues"] in data.py.
pub fn phase32_password() -> &'static str {
    PHASE32_PASSWORD_SHA256_HEX
}

pub fn phase32_blob_b64() -> String {
    concat!(
        "U2FsdGVkX1/u/Exb78Flah0YM7yMVzRigu/5MKd5MG/d1Yncv3MIlTSMPFl6iZtT",
        "Dx7JJRbZYZwm18L9XZ2k3+qm7gNxmg7zbg4Qz8rgUe/E3S54WuDMxxKcg7refbj2",
        "U+upsLJ7wBmZk1KHxT0MzXv7teub7GuOqyCdChPd1dRScXa3OVk3oQWpFc6nPmBM",
        "M1wBB2h41eaQc9j0p4spW+3PN0zbg5HGl8+44KvMHheNDWvw7dS18NTMKnXIx42Z",
        "2RwAZvTLxI2Lsx0RiGIcxZzCSO3kdZS0PCyPlKSRBrdTLtSWHLvM+PgdTXAWKv+u",
        "t+GKa8YrPYMeTv9v2nG6Twg/8OFRNmXI29RFOW5zEkH7ZzAZ13lIaiM6/f4DzKbk",
        "Jwky9ngIOOdcsPSTox/xFv/jB6ZYM6ElqCs+gKSo1LwsvPexco18VvfgfO4vLmWB",
        "Z1Pdgu/nUoQm71XmzCTjUjyiH9cZf+4iqjjAPl/q/pPx9TIPmejWDTQi/Tw3wtv2",
        "UpG621OUWRIle9YBSjhIVIPXpbFiUpEV85AiiQ6VdN05+WcCByZ5wIQBFPDnRjeS",
        "24CXPRKmVWfLmvXbR3DE/ICiBw8h9n3636PIScO1Nv1pUHCJvCSjxJOANl01XAEB",
        "7wrOlmn5p8mSLZQ7J0xOlBPvf5dk6T+rYROMl5rKrd+i0QXT92y3Pel5cBDQlA2D",
        "Eq2yqtqKxRGaFJkNS2u8cKI2NBskowo+aeZNg6fpLB9N12dEKAWGh18Xj5I2YUsv",
        "l9zxebddjSbFCM9PJ8FJwEKRok6jl+Jm732y2Gq8OuAHGk0IFUFE/WE2C7GpLdHn",
        "M9pN3I+r+OTYcMZ/VFKhMjqkjUWb5zquWj8HSYwsRrtPbnjaucqW4I5kyBRvvi42",
        "YD6gu0xY6ClckNoKOYyH5llRQ7E9+rgOsxrAJF3JbHiZmLg7Z/YWZkwvCnwEdR9x",
        "Y3PUyjEzT5K/D2qYYcMtgsUgYfRD9W9Z41bcMOJBKT3PNdxOAwEyFWpN7hGtRVd9",
        "ACPyz2djZYE7Fi2LzVvlRh1ViSdkQifiwrXO9WjraNV0XixJgijGrzKYPK/vaXxo",
        "8g7LboXi4/gpLN3GzOQf49g3ijfi2Mng5TL6qUwG4jjoVYa/dV2OfuCIZugCRWkg",
        "SzmqZ/Q0mwtbQNcbVFG/0ds0CDh8W8OUc4v64V8HFSx4XCjDo2Hi5DUxBGTjnGKV",
        "kmd802s7UxjbNO34Sza4xwJ24i23cq5CE2wQKhiFq8EqlbRqjzfvpHNXxdR6sVw7",
        "lrJNj8J+U7Vhb16NRUrGpBjCU2w0iRFyrDTrctVXsAwZBGDsmo77jJEvlqztZj+m",
        "MEs8lA807eo8A8lnTRTJzLMbHnqbJbNwfSfNjqJ52r7Vqh6dN6Mud0E9Iw7obKm8",
        "IzcaTCghE6Lqd5IMYy9Z/NX5qSG4KhqM4ZCslCH9GIcRW0ZOIZOopv5Gouk53A3E",
        "pDUkyC/WSukeoxbqkIfSdgi/In2Snp7SnvoF0WVjZcyrnsHcSeoRJEAeiSBQIUTL",
        "cV2sHifQMFOCPzCMY96Vkcjav38qx8tFiRcc7cb4ZE28HoqnBPmStXIW4ib3Y8+F",
        "5wKW8gmEQCb4gnwL/C9s5T44djGy+70g5c01GDpyROQJWPXAVoMaIFFkdba00Y0m",
        "NQrl9gFonLcheonYKuMtSwEU18AMT0c7+CRCb2SK2gwhh2sitA9V8T5jyAGSXc0t",
        "IZGVrKb0IIA3GfKbYfILdKgUk7C5H9DVsucAN8/vg/VjTNoGpMPv2AUfmtvjqFjI",
        "lNBam1ODn26Cfj02bJL7r+B4aqid8sgGHH9dVxFQHhnUmeg0SNjQDEr3Ws90ZJ7b",
        "cQ1Ierbq0Bxonau2YNZQ/3VfnQ9TlGJxmw9RNRoA60Vn9rBY1qbG9UPVAJe5VHoe",
        "jddj9i3rP1NZ9LVeNX0zUxbVsGCt7TihDVGWRrMJopvlywzRUMyl7CTdRu6HVg3l",
        "7pFSBb5qmq/H3s6Kgt9OOuYB4Ojy1NnR9GNR8iCnWe+eXnPMg5o0ede/zr570vr9",
        "3/ioOoT3tCBDlBY8g6J/qiqvoixVk8JBVXhQrjA40QritQeu9jzHqN0F/FmLMKnK",
        "VcVdvZOWPfw/DW/jaiaji3csKQxia2WignvDn83Iv15TridcIHELPUigfw8n4xzb",
        "irgEY3VhlSXmsQk8jKpaENJHlhCZxYhUKAxOZgZP3VLXz3GOQhYyJnv7MUexuSVK",
        "czbD+ab8uUg3W7nqoqKt02HvjKjFAYQaIZUgvX0c3EY773eFpUTO7C28okGNOUXC",
        "HJfQvc1GviKUA5Ef6xad5AQzR+0UeTkuiex/NoPB/ouVkgNReUapnvdgh+kiDOsw",
        "5P8D9zWcuyWYoDdtWeki5o2lic/hw+fx1F2FL36JYmj5IoXecMp1uq7BO8x7mZ5L",
        "ROZZKorMkL4HlUQeglk6wdY4/msZJL9dOkoaCR4rIi9eEUQlH8oTpOjgy7qMB4qC",
        "UkCEqNdyrsavw7egkb/S3gGWfBPL4E2TYrkJyLPNAfkNAq3ucuUHZnDW+Btv29ge",
        "xoJz6DTfDkBE8npGXJzrJYeWcQJOis0Wre2pKaG9IyoIBbsHpOKJ3V1xqUIONWmS",
        "VlCiVdeC08Bfe6N9qPr4I2Sh3qazGTCWS9ewTv+vDuZ3oY7esZ8eHNEHELxGUksf",
        "mDpAMfjIudqB8bshlgtAw+Uy2ess6rtF7u1bRVKAaVCdl1/cul1hhB8TS8AabtgI",
        "cNRT9V1Szs0lQ2PgdoNhiOKNusp0+TN6KgrWYrY0EEocEKRLuxrRQpMrG+LZ3eTw",
        "7ZG0Tct/yGu/GAuzvHXEss79Vram40wuA+K6WG6FTStgJBpWwtRh7/LEuXpKannQ",
        "pJR8i7Db0Su05ogJjUP8Uyd5RKPxoQV6tUWkZY5qBq47aL6M1xv/7gfkatASwdts",
        "8VfG11ynby+xfhkZJFXUMTqvQOcwkx7gVED2wRWymuP/H0yCWogzD++rkE+TJUK9",
        "hVjr2FbHN8zRtbkpYwxRln7sPe/dqHTvMoRo4r5IJsaXmaAQgEc7dBwNN7PeROzI",
        "uwXA8V+Me77PupUbA1OHVxLHqt2FeUpMT+6UeteVtyyQInJ478Qml7Hfh4zMr0O4",
        "BG3IYyFEN9ryiMoXYCogsjE9cNus9hlSrcA1NGyIl4q/bPlGCU6oaFUDCBcvzydZ",
        "yc/PWKcXaA1ANvT/Q7rMi58xHyTS5B/3rjpQ8VGq+6AMRd4VEeXitewbB16L8CPN",
    )
    .to_string()
}

pub fn b64_decode_pub(s: &str) -> Vec<u8> {
    b64_decode(s)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loads_four_blobs_with_expected_lengths() {
        let blobs = load_blobs();
        assert_eq!(blobs.len(), 4);
        let by_tag = |tag: &str| blobs.iter().find(|b| b.tag == tag).unwrap();
        assert_eq!(by_tag("SALPH").ciphertext.len(), 80);
        assert_eq!(by_tag("COSMIC").ciphertext.len(), 1328);
        assert_eq!(by_tag("P32TRAILING").ciphertext.len(), 80);
        assert_eq!(by_tag("URLBLOB").ciphertext.len(), 96);

        assert_eq!(hex::encode(by_tag("SALPH").salt), "3ab585348552415d");
        assert_eq!(hex::encode(by_tag("COSMIC").salt), "2d3f6fe06dc950e6");
        assert_eq!(hex::encode(by_tag("P32TRAILING").salt), "b45a5e3d827593ca");
        assert_eq!(hex::encode(by_tag("URLBLOB").salt), "74c974e3f92e64b5");
    }

    #[test]
    fn variant_table_has_sixty_entries() {
        assert_eq!(variant_table().len(), 60);
    }

    #[test]
    fn phase32_blob_decodes_to_expected_length() {
        let raw = b64_decode(&phase32_blob_b64());
        assert_eq!(&raw[0..8], b"Salted__");
        assert_eq!(raw.len(), 2448);
    }
}
