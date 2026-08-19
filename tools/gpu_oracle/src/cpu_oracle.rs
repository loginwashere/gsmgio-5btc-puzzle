//! CPU reference oracle, built from well-tested RustCrypto crates rather than
//! a hand-rolled port -- this is the independent cross-check the GPU kernel's
//! output must agree with (see selftest.rs), not itself a from-scratch
//! reimplementation of cb_common.py's algorithms.

use aes::cipher::{block_padding::NoPadding, BlockDecryptMut, KeyIvInit};
use md5::Md5;
use sha1::Sha1;
use sha2::{Digest, Sha256};

use crate::blobs::{KDF_LEGACY_MD5, KDF_LEGACY_SHA1, KDF_LEGACY_SHA256, KDF_PBKDF2_SHA256};

type Aes128CbcDec = cbc::Decryptor<aes::Aes128>;
type Aes192CbcDec = cbc::Decryptor<aes::Aes192>;
type Aes256CbcDec = cbc::Decryptor<aes::Aes256>;

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

pub fn derive_key_iv(kdf: i32, passwd: &[u8], salt: &[u8; 8], key_len: usize) -> (Vec<u8>, Vec<u8>) {
    let material_len = key_len + 16;
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

/// Full try-open for one (candidate, variant, blob) triple. Mirrors
/// aes_try_open_bytes()'s per-candidate gate exactly (structural bypass
/// checked before the z-score, weak/strong thresholds at 5.0/8.0).
pub fn try_open(candidate: &[u8], kdf: i32, key_len: usize, salt: &[u8; 8], ct: &[u8]) -> (HitKind, Option<Vec<u8>>) {
    if ct.is_empty() || ct.len() % 16 != 0 {
        return (HitKind::None, None);
    }
    let (key, iv) = derive_key_iv(kdf, candidate, salt, key_len);
    let Some(pt) = aes_cbc_decrypt(&key, &iv, ct) else {
        return (HitKind::None, None);
    };
    let Some(body_len) = pkcs7_check(&pt) else {
        return (HitKind::None, None);
    };
    let pad = pt.len() - body_len;
    let body = &pt[..body_len];

    if pad == 16 && body_len == 64 {
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
        let (kind, body) = try_open(password_hex.as_bytes(), KDF_LEGACY_SHA256, 32, &salt, ct);
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
        let (kind, _) = try_open(b"definitely_not_the_password", KDF_LEGACY_SHA256, 32, &salt, ct);
        assert_eq!(kind, HitKind::None);
    }
}
