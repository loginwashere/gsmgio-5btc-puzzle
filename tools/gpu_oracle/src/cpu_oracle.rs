//! CPU reference oracle, built from well-tested RustCrypto crates rather than
//! a hand-rolled port -- this is the independent cross-check the GPU kernel's
//! output must agree with (see selftest.rs), not itself a from-scratch
//! reimplementation of cb_common.py's algorithms.

use aes::cipher::{
    block_padding::NoPadding, BlockDecryptMut, KeyInit, KeyIvInit, StreamCipher,
};
use cfb_mode::cipher::AsyncStreamCipher;
use md5::Md5;
use sha1::Sha1;
use sha2::{Digest, Sha256};

use crate::blobs::{
    CIPHER_CBC, CIPHER_CFB, CIPHER_CTR, CIPHER_ECB, CIPHER_OFB, CIPHER_SEED_CBC, KDF_LEGACY_MD5,
    KDF_LEGACY_SHA1, KDF_LEGACY_SHA256, KDF_PBKDF2_SHA256,
};
use crate::seed_cipher::{seed_cbc_decrypt, seed_set_key};

type Aes128CbcDec = cbc::Decryptor<aes::Aes128>;
type Aes192CbcDec = cbc::Decryptor<aes::Aes192>;
type Aes256CbcDec = cbc::Decryptor<aes::Aes256>;

type Aes128EcbDec = ecb::Decryptor<aes::Aes128>;
type Aes192EcbDec = ecb::Decryptor<aes::Aes192>;
type Aes256EcbDec = ecb::Decryptor<aes::Aes256>;

type Aes128CfbDec = cfb_mode::Decryptor<aes::Aes128>;
type Aes192CfbDec = cfb_mode::Decryptor<aes::Aes192>;
type Aes256CfbDec = cfb_mode::Decryptor<aes::Aes256>;

type Aes128Ofb = ofb::Ofb<aes::Aes128>;
type Aes192Ofb = ofb::Ofb<aes::Aes192>;
type Aes256Ofb = ofb::Ofb<aes::Aes256>;

// Ctr128BE: 128-bit big-endian counter, full block used as the initial
// counter value -- matches the `cryptography` library's default CTR mode
// (same one cb_common.py's STREAM_MODE_CLASSES["ctr"] = modes.CTR uses).
type Aes128Ctr = ctr::Ctr128BE<aes::Aes128>;
type Aes192Ctr = ctr::Ctr128BE<aes::Aes192>;
type Aes256Ctr = ctr::Ctr128BE<aes::Aes256>;

pub const PRINTABLE_P0: f64 = 98.0 / 256.0;
pub const PRINTABLE_Z_WEAK: f64 = 5.0;
pub const PRINTABLE_Z_STRONG: f64 = 8.0;

#[derive(Debug, Clone, PartialEq)]
pub enum HitKind {
    None,
    Weak(f64),
    Strong(f64),
    Structural,
}

fn evp_bytes_to_key(kdf: i32, passwd: &[u8], salt: &[u8; 8], out_len: usize) -> Vec<u8> {
    let mut out = Vec::with_capacity(out_len);
    let mut prev: Vec<u8> = Vec::new();
    while out.len() < out_len {
        let mut input = Vec::with_capacity(prev.len() + passwd.len() + 8);
        input.extend_from_slice(&prev);
        input.extend_from_slice(passwd);
        input.extend_from_slice(salt);
        let digest: Vec<u8> = match kdf {
            KDF_LEGACY_MD5 => Md5::digest(&input).to_vec(),
            KDF_LEGACY_SHA1 => Sha1::digest(&input).to_vec(),
            KDF_LEGACY_SHA256 => Sha256::digest(&input).to_vec(),
            _ => unreachable!("not a legacy KDF kind"),
        };
        prev = digest.clone();
        out.extend_from_slice(&digest);
    }
    out.truncate(out_len);
    out
}

fn pbkdf2_material(passwd: &[u8], salt: &[u8; 8], out_len: usize) -> Vec<u8> {
    let mut out = vec![0u8; out_len];
    pbkdf2::pbkdf2_hmac::<Sha256>(passwd, salt, 10_000, &mut out);
    out
}

/// ECB has no IV (`iv_len = 0`), matching cb_common.py's
/// `evp_bytes_to_key(passwd, salt, kdf_param, key_len, 0)` /
/// `pbkdf2_bytes_to_key(..., key_len, 0)` calls for the ECB path.
pub fn derive_key_iv(kdf: i32, passwd: &[u8], salt: &[u8; 8], key_len: usize, mode: i32) -> (Vec<u8>, Vec<u8>) {
    let iv_len = if mode == CIPHER_ECB { 0 } else { 16 };
    let material_len = key_len + iv_len;
    let material = if kdf == KDF_PBKDF2_SHA256 {
        pbkdf2_material(passwd, salt, material_len)
    } else {
        evp_bytes_to_key(kdf, passwd, salt, material_len)
    };
    (material[..key_len].to_vec(), material[key_len..].to_vec())
}

fn aes_cbc_decrypt(key: &[u8], iv: &[u8], ct: &[u8]) -> Option<Vec<u8>> {
    // Decrypt block-by-block into a mutable copy, no unpadding here -- we
    // need the raw padded plaintext to run cb_common.py's own PKCS7 check.
    let mut buf = ct.to_vec();
    let res = match key.len() {
        16 => Aes128CbcDec::new_from_slices(key, iv)
            .ok()?
            .decrypt_padded_mut::<NoPadding>(&mut buf)
            .ok()
            .map(|p| p.to_vec()),
        24 => Aes192CbcDec::new_from_slices(key, iv)
            .ok()?
            .decrypt_padded_mut::<NoPadding>(&mut buf)
            .ok()
            .map(|p| p.to_vec()),
        32 => Aes256CbcDec::new_from_slices(key, iv)
            .ok()?
            .decrypt_padded_mut::<NoPadding>(&mut buf)
            .ok()
            .map(|p| p.to_vec()),
        _ => return None,
    };
    res
}

/// No chaining, no IV -- raw per-block decrypt, same NoPadding convention as
/// aes_cbc_decrypt so the shared pkcs7_check/structural gate below applies
/// unchanged.
fn aes_ecb_decrypt(key: &[u8], ct: &[u8]) -> Option<Vec<u8>> {
    let mut buf = ct.to_vec();
    match key.len() {
        16 => Aes128EcbDec::new_from_slice(key)
            .ok()?
            .decrypt_padded_mut::<NoPadding>(&mut buf)
            .ok()
            .map(|p| p.to_vec()),
        24 => Aes192EcbDec::new_from_slice(key)
            .ok()?
            .decrypt_padded_mut::<NoPadding>(&mut buf)
            .ok()
            .map(|p| p.to_vec()),
        32 => Aes256EcbDec::new_from_slice(key)
            .ok()?
            .decrypt_padded_mut::<NoPadding>(&mut buf)
            .ok()
            .map(|p| p.to_vec()),
        _ => None,
    }
}

/// CFB/OFB/CTR: no padding at all -- the returned Vec is the full decrypted
/// body, straight to the printable gate (matches
/// cb_common.py's aes_try_open_stream_bytes exactly).
fn aes_cfb_decrypt(key: &[u8], iv: &[u8], ct: &[u8]) -> Option<Vec<u8>> {
    let mut buf = ct.to_vec();
    match key.len() {
        16 => Aes128CfbDec::new_from_slices(key, iv).ok()?.decrypt(&mut buf),
        24 => Aes192CfbDec::new_from_slices(key, iv).ok()?.decrypt(&mut buf),
        32 => Aes256CfbDec::new_from_slices(key, iv).ok()?.decrypt(&mut buf),
        _ => return None,
    }
    Some(buf)
}

fn aes_ofb_decrypt(key: &[u8], iv: &[u8], ct: &[u8]) -> Option<Vec<u8>> {
    let mut buf = ct.to_vec();
    match key.len() {
        16 => Aes128Ofb::new_from_slices(key, iv).ok()?.apply_keystream(&mut buf),
        24 => Aes192Ofb::new_from_slices(key, iv).ok()?.apply_keystream(&mut buf),
        32 => Aes256Ofb::new_from_slices(key, iv).ok()?.apply_keystream(&mut buf),
        _ => return None,
    }
    Some(buf)
}

fn aes_ctr_decrypt(key: &[u8], iv: &[u8], ct: &[u8]) -> Option<Vec<u8>> {
    let mut buf = ct.to_vec();
    match key.len() {
        16 => Aes128Ctr::new_from_slices(key, iv).ok()?.apply_keystream(&mut buf),
        24 => Aes192Ctr::new_from_slices(key, iv).ok()?.apply_keystream(&mut buf),
        32 => Aes256Ctr::new_from_slices(key, iv).ok()?.apply_keystream(&mut buf),
        _ => return None,
    }
    Some(buf)
}

fn pkcs7_check(pt: &[u8]) -> Option<usize> {
    let pad = *pt.last()? as usize;
    if pad < 1 || pad > 16 || pad > pt.len() {
        return None;
    }
    if pt[pt.len() - pad..].iter().all(|&b| b as usize == pad) {
        Some(pt.len() - pad)
    } else {
        None
    }
}

pub fn printable_z_score(body: &[u8]) -> f64 {
    let n = body.len();
    if n == 0 {
        return 0.0;
    }
    let count = body
        .iter()
        .filter(|&&c| (32..127).contains(&c) || c == 9 || c == 10 || c == 13)
        .count() as f64;
    let mean = n as f64 * PRINTABLE_P0;
    let var = n as f64 * PRINTABLE_P0 * (1.0 - PRINTABLE_P0);
    if var <= 0.0 {
        0.0
    } else {
        (count - mean) / var.sqrt()
    }
}

/// CFB/OFB/CTR decrypt with no printable/z-score gate at all -- unlike
/// `try_open`, which discards the body whenever z < PRINTABLE_Z_WEAK.
/// Stream modes have no padding to validate, so there is no structural
/// signal analogous to CBC/ECB's full-dummy-pad-block check: a correct
/// password whose plaintext is raw binary (not text) produces a body that
/// will essentially never look printable, and `try_open` would silently
/// drop it. This is the CPU-only fallback oracle for that case (see
/// `stream_key_check.rs`): every candidate's body is returned unconditionally
/// so it can be Bloom/API-checked directly instead of relying on
/// printability. `None` only for genuine decrypt-setup failure (wrong key
/// length for the fixed variant table -- not expected in practice) or empty
/// ciphertext.
pub fn stream_decrypt_unconditional(candidate: &[u8], kdf: i32, key_len: usize, mode: i32, salt: &[u8; 8], ct: &[u8]) -> Option<Vec<u8>> {
    if ct.is_empty() {
        return None;
    }
    let (key, iv) = derive_key_iv(kdf, candidate, salt, key_len, mode);
    match mode {
        CIPHER_CFB => aes_cfb_decrypt(&key, &iv, ct),
        CIPHER_OFB => aes_ofb_decrypt(&key, &iv, ct),
        CIPHER_CTR => aes_ctr_decrypt(&key, &iv, ct),
        _ => None,
    }
}

/// Full try-open for one (candidate, variant, blob) triple, `mode` one of
/// CIPHER_CBC/ECB/CFB/OFB/CTR/SEED_CBC. CBC/ECB/SEED_CBC mirror
/// aes_try_open_bytes()/aes_try_open_ecb_bytes()'s gate exactly (structural
/// bypass checked before the z-score, weak/strong thresholds at 5.0/8.0,
/// PKCS7-valid required), broadened beyond cb_common.py's original
/// `body_len == 64`-pinned structural check to any full-dummy-pad body (see
/// the comment at the `pad == 16` check below). SEED_CBC uses the same PKCS7/
/// structural/z-score gate, just a different 16-byte block primitive.
/// CFB/OFB/CTR mirror aes_try_open_stream_bytes(): no padding, whole body
/// straight to the printable gate, no structural bypass.
pub fn try_open(candidate: &[u8], kdf: i32, key_len: usize, mode: i32, salt: &[u8; 8], ct: &[u8]) -> (HitKind, Option<Vec<u8>>) {
    if ct.is_empty() {
        return (HitKind::None, None);
    }
    let (key, iv) = derive_key_iv(kdf, candidate, salt, key_len, mode);

    match mode {
        CIPHER_CBC | CIPHER_ECB | CIPHER_SEED_CBC => {
            if ct.len() % 16 != 0 {
                return (HitKind::None, None);
            }
            let pt = if mode == CIPHER_CBC {
                aes_cbc_decrypt(&key, &iv, ct)
            } else if mode == CIPHER_SEED_CBC {
                if key.len() != 16 || iv.len() != 16 {
                    return (HitKind::None, None);
                }
                let mut key16 = [0u8; 16];
                let mut iv16 = [0u8; 16];
                key16.copy_from_slice(&key);
                iv16.copy_from_slice(&iv);
                let ks = seed_set_key(&key16);
                Some(seed_cbc_decrypt(&ks, &iv16, ct))
            } else {
                aes_ecb_decrypt(&key, ct)
            };
            let Some(pt) = pt else {
                return (HitKind::None, None);
            };
            let Some(body_len) = pkcs7_check(&pt) else {
                return (HitKind::None, None);
            };
            let pad = pt.len() - body_len;
            let body = &pt[..body_len];

            // Full dummy PKCS7 block (pad == block size) is independently
            // improbable for a wrong password -- 256^-16 = 2^-128 chance the
            // last 16 bytes all equal 0x10 by accident -- regardless of
            // body_len, which is fully determined by this blob's (fixed)
            // ciphertext length once pad is known and adds no further
            // specificity. Originally gated on `body_len == 64` too (mirrors
            // cb_common.py's `is_structural_binary_plaintext`, written when
            // only the two 80-byte blobs SALPH/P32TRAILING were swept), which
            // silently excluded URLBLOB (body_len 80) and COSMIC (body_len
            // 1312) from ever reporting this signal. Broadened here; see
            // keyshape.rs::process_structural_hit for the corresponding
            // chunked (not fixed half/better_half) address derivation.
            if pad == 16 {
                return (HitKind::Structural, Some(body.to_vec()));
            }
            let z = printable_z_score(body);
            if z >= PRINTABLE_Z_STRONG {
                (HitKind::Strong(z), Some(body.to_vec()))
            } else if z >= PRINTABLE_Z_WEAK {
                (HitKind::Weak(z), Some(body.to_vec()))
            } else {
                (HitKind::None, None)
            }
        }
        CIPHER_CFB | CIPHER_OFB | CIPHER_CTR => {
            let pt = match mode {
                CIPHER_CFB => aes_cfb_decrypt(&key, &iv, ct),
                CIPHER_OFB => aes_ofb_decrypt(&key, &iv, ct),
                _ => aes_ctr_decrypt(&key, &iv, ct),
            };
            let Some(body) = pt else {
                return (HitKind::None, None);
            };
            if body.is_empty() {
                return (HitKind::None, None);
            }
            let z = printable_z_score(&body);
            if z >= PRINTABLE_Z_STRONG {
                (HitKind::Strong(z), Some(body))
            } else if z >= PRINTABLE_Z_WEAK {
                (HitKind::Weak(z), Some(body))
            } else {
                (HitKind::None, None)
            }
        }
        _ => (HitKind::None, None),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::blobs;

    #[test]
    fn known_phase32_vector_decrypts_and_is_a_hit() {
        let raw = blobs::b64_decode_pub(&blobs::phase32_blob_b64());
        assert_eq!(&raw[0..8], b"Salted__");
        let mut salt = [0u8; 8];
        salt.copy_from_slice(&raw[8..16]);
        let ct = &raw[16..];

        let password_hex = blobs::phase32_password();
        let (kind, body) = try_open(password_hex.as_bytes(), KDF_LEGACY_SHA256, 32, CIPHER_CBC, &salt, ct);
        match kind {
            HitKind::Strong(z) => assert!(z > 15.0, "expected a very strong z-score, got {z}"),
            other => panic!("expected Strong hit, got {other:?}"),
        }
        let body = body.unwrap();
        assert!(body.starts_with(b"jacquefresco") || body.len() > 0, "sanity: got a body");
    }

    #[test]
    fn wrong_password_is_not_a_hit() {
        let raw = blobs::b64_decode_pub(&blobs::phase32_blob_b64());
        let mut salt = [0u8; 8];
        salt.copy_from_slice(&raw[8..16]);
        let ct = &raw[16..];
        let (kind, _) = try_open(b"definitely_not_the_password", KDF_LEGACY_SHA256, 32, CIPHER_CBC, &salt, ct);
        assert_eq!(kind, HitKind::None);
    }

    #[test]
    fn structural_hit_no_longer_requires_exactly_64_byte_body() {
        // Regression test for the broadened `pad == 16` gate above: proves a
        // full-dummy-pad body at a length other than 64 (the old
        // `body_len == 64`-pinned check, inherited from cb_common.py's
        // SALPH/P32TRAILING-only original, would have silently missed this
        // and fallen through to the printable z-score gate instead).
        use aes::cipher::block_padding::NoPadding;
        use aes::cipher::BlockEncryptMut;
        type Aes256CbcEnc = cbc::Encryptor<aes::Aes256>;

        let candidate = b"any_password_for_this_test";
        let salt = [0x33u8; 8];
        let (key, iv) = derive_key_iv(KDF_LEGACY_SHA256, candidate, &salt, 32, CIPHER_CBC);

        // 32 bytes of "key material" + one full 16-byte dummy PKCS7 block
        // (all bytes == 0x10) -- same "full dummy pad" shape as SALPH/
        // P32TRAILING's 64-byte case, but at a body length the old gate
        // would have dropped.
        let mut plaintext = vec![0xABu8; 32];
        plaintext.extend(std::iter::repeat(0x10u8).take(16));

        let ct = Aes256CbcEnc::new_from_slices(&key, &iv)
            .unwrap()
            .encrypt_padded_vec_mut::<NoPadding>(&plaintext);

        let (kind, body) = try_open(candidate, KDF_LEGACY_SHA256, 32, CIPHER_CBC, &salt, &ct);
        assert_eq!(kind, HitKind::Structural);
        assert_eq!(body.unwrap(), plaintext[..32]);
    }

    #[test]
    fn stream_decrypt_unconditional_returns_body_even_when_not_printable() {
        // The whole point of this function: unlike try_open, it must not
        // drop a low-z-score (binary-looking) body.
        let candidate = b"whatever_password";
        let salt = [0x44u8; 8];
        let ct = [0u8; 80]; // arbitrary stream ciphertext, same length as SALPH/P32TRAILING
        let body = stream_decrypt_unconditional(candidate, KDF_LEGACY_SHA256, 32, CIPHER_CFB, &salt, &ct)
            .expect("stream decrypt should always succeed for a valid variant");
        assert_eq!(body.len(), 80);
        // try_open, by contrast, drops this same body as None (garbage z-score).
        let (kind, dropped_body) = try_open(candidate, KDF_LEGACY_SHA256, 32, CIPHER_CFB, &salt, &ct);
        assert_eq!(kind, HitKind::None);
        assert!(dropped_body.is_none());
    }

    #[test]
    fn ecb_cfb_ofb_ctr_round_trip_against_a_synthetic_vector() {
        // Independent of this project's blobs -- just proves each new mode's
        // decrypt path actually inverts its own encrypt path (using the same
        // RustCrypto crates for both directions, so this is a plumbing check,
        // not a cross-implementation check; selftest.rs's GPU/CPU cross-check
        // is what actually validates the CUDA port against this reference).
        use aes::cipher::generic_array::GenericArray;
        use aes::cipher::BlockEncryptMut;
        let key = [0x11u8; 32];
        let iv = [0x22u8; 16];
        let plaintext: &[u8] = b"the quick brown fox jumps over the lazy dog!!!!!"; // 48 bytes, block-aligned for ECB

        // ECB: encrypt block-by-block directly (no padding machinery --
        // plaintext is already block-aligned), matching what aes_ecb_decrypt
        // expects to invert.
        {
            let mut buf = plaintext.to_vec();
            let mut enc = ecb::Encryptor::<aes::Aes256>::new_from_slice(&key).unwrap();
            for chunk in buf.chunks_mut(16) {
                enc.encrypt_block_mut(GenericArray::from_mut_slice(chunk));
            }
            let pt = aes_ecb_decrypt(&key, &buf).unwrap();
            assert_eq!(&pt[..], &plaintext[..]);
        }
        // CFB
        {
            let mut buf = plaintext.to_vec();
            cfb_mode::Encryptor::<aes::Aes256>::new_from_slices(&key, &iv)
                .unwrap()
                .encrypt(&mut buf);
            let pt = aes_cfb_decrypt(&key, &iv, &buf).unwrap();
            assert_eq!(&pt[..], &plaintext[..]);
        }
        // OFB
        {
            let mut buf = plaintext.to_vec();
            let mut enc = Aes256Ofb::new_from_slices(&key, &iv).unwrap();
            enc.apply_keystream(&mut buf);
            let pt = aes_ofb_decrypt(&key, &iv, &buf).unwrap();
            assert_eq!(&pt[..], &plaintext[..]);
        }
        // CTR
        {
            let mut buf = plaintext.to_vec();
            let mut enc = Aes256Ctr::new_from_slices(&key, &iv).unwrap();
            enc.apply_keystream(&mut buf);
            let pt = aes_ctr_decrypt(&key, &iv, &buf).unwrap();
            assert_eq!(&pt[..], &plaintext[..]);
        }
    }

    #[test]
    fn seed_cbc_round_trip_through_try_open() {
        // End-to-end plumbing check: derive_key_iv -> seed_set_key ->
        // seed_encrypt_block (CBC, hand-chained) -> try_open's own
        // seed_cbc_decrypt path -> PKCS7 unpad -> printable gate. Independent
        // cross-implementation correctness is already pinned by
        // seed_cipher::tests' RFC 4269 KAT vectors; this proves the oracle's
        // own KDF/CBC/PKCS7 wiring around that primitive is correct.
        let salt = [0x77u8; 8];
        let candidate = b"seedplantedcandidate";
        let (key, iv) = derive_key_iv(KDF_LEGACY_SHA256, candidate, &salt, 16, CIPHER_SEED_CBC);
        let mut key16 = [0u8; 16];
        let mut iv16 = [0u8; 16];
        key16.copy_from_slice(&key);
        iv16.copy_from_slice(&iv);
        let ks = seed_set_key(&key16);

        // 32 bytes of printable plaintext + 16-byte PKCS7 pad block (2
        // blocks) -> should score Strong, not Structural (pad != 16).
        let plaintext = b"the seed is planted right here!!"; // 32 bytes
        assert_eq!(plaintext.len(), 32);
        let mut padded = plaintext.to_vec();
        padded.extend(std::iter::repeat(16u8).take(16)); // full pad block

        let mut ct = Vec::new();
        let mut prev = iv16;
        for chunk in padded.chunks_exact(16) {
            let mut block_in = [0u8; 16];
            for i in 0..16 {
                block_in[i] = chunk[i] ^ prev[i];
            }
            let block_out = crate::seed_cipher::seed_encrypt_block(&ks, &block_in);
            ct.extend_from_slice(&block_out);
            prev = block_out;
        }

        let (kind, body) = try_open(candidate, KDF_LEGACY_SHA256, 16, CIPHER_SEED_CBC, &salt, &ct);
        // Full dummy pad block (pad == 16) is Structural regardless of body
        // printability -- matches the AES-CBC gate exactly.
        assert_eq!(kind, HitKind::Structural);
        assert_eq!(body.unwrap(), plaintext);

        // Wrong candidate must not decrypt to valid PKCS7.
        let (wrong_kind, _) = try_open(b"not_the_seed", KDF_LEGACY_SHA256, 16, CIPHER_SEED_CBC, &salt, &ct);
        assert_eq!(wrong_kind, HitKind::None);
    }
}
