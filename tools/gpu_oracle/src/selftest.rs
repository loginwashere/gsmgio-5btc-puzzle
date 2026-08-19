//! Mandatory correctness gate, run before any real sweep (mirrors
//! cb_common.py's own VALIDATION_NUM / PHASE32_BLOB_B64 startup self-tests).
//!
//! 1. The known-positive Phase 3.2 vector must produce a Strong hit on GPU,
//!    matching the CPU reference's z-score.
//! 2. A batch of known-negative candidates must produce IDENTICAL
//!    (candidate, variant, blob) -> hit-kind classification between GPU and
//!    CPU, across every Phase-1 variant and every tracked blob.
//!
//! A subtly wrong AES/KDF port would silently produce false negatives across
//! a whole sweep -- this is the safety net against that, not a formality.

use crate::blobs::{self, Blob, CIPHER_CBC, CIPHER_SEED_CBC, KDF_LEGACY_SHA256};
use crate::checker::BloomChecker;
use crate::cpu_oracle::{self, HitKind};
use crate::crypto::privkey_to_addresses;
use crate::gpu::{DecryptHit, GpuOracle, StreamKeyHit};
use crate::seed_cipher::{seed_encrypt_block, seed_set_key};
use std::collections::HashSet;

const NEGATIVE_PROBE_CANDIDATES: &[&str] = &[
    "yellowblueprimes",
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "yinyang",
    "wewontgiveawaythepassword",
    "itsinfrontofyoureyesbutyourenotseeingit",
    "verylaststepisatruegiveaway",
    "promised",
    "password",
    "salphaseion",
    "cosmicduality",
    "test123",
];

pub fn run(gpu: &GpuOracle) -> Result<(), Box<dyn std::error::Error>> {
    println!("[selftest] Running mandatory correctness gate before any real sweep...");

    let blobs = blobs::load_blobs();
    let variants = blobs::variant_table();

    run_known_positive(gpu, &blobs)?;
    run_negative_cross_check(gpu, &blobs, &variants)?;
    run_seed_cross_check(gpu, &blobs)?;
    run_cbc_bloom_chunk_check(gpu, &blobs)?;

    println!("[selftest] PASSED -- GPU kernel output matches the CPU reference oracle.");
    Ok(())
}

fn run_known_positive(gpu: &GpuOracle, _blobs: &[Blob]) -> Result<(), Box<dyn std::error::Error>> {
    let raw = blobs::b64_decode_pub(&blobs::phase32_blob_b64());
    let mut salt = [0u8; 8];
    salt.copy_from_slice(&raw[8..16]);
    let ct = raw[16..].to_vec();

    let phase32_blob = Blob { tag: "PHASE32_SELFTEST", salt, ciphertext: ct.clone() };
    let password = blobs::phase32_password().to_string();

    // CPU reference: must be a Strong hit with a large z-score (~22 per
    // cb_common.py's own comments -- assert a generous but meaningful floor).
    let (cpu_kind, _) = cpu_oracle::try_open(password.as_bytes(), blobs::KDF_LEGACY_SHA256, 32, blobs::CIPHER_CBC, &salt, &ct);
    let cpu_z = match cpu_kind {
        HitKind::Strong(z) => z,
        other => return Err(format!("CPU reference itself failed on the known-positive vector: {other:?}").into()),
    };
    if cpu_z < 15.0 {
        return Err(format!("CPU reference z-score suspiciously low ({cpu_z}); aborting before trusting GPU against it").into());
    }

    // GPU: run the single known password through only the exact variant that
    // should hit (legacy-sha256, AES-256) against only this one blob.
    let candidates = vec![password.clone()];
    let mut gpu_hits: Vec<DecryptHit> = Vec::new();
    gpu.scan(
        &candidates,
        &HashSet::new(),
        std::slice::from_ref(&phase32_blob),
        &[(blobs::KDF_LEGACY_SHA256, 32, blobs::CIPHER_CBC)],
        None,
        |hit| gpu_hits.push(*hit),
        |_| {},
        |_, _, _| {},
        |_| {},
        &std::sync::atomic::AtomicBool::new(false),
    )?;

    if gpu_hits.is_empty() {
        return Err("GPU kernel produced NO hit for the known-positive Phase 3.2 vector -- kernel is broken".into());
    }
    let strong = gpu_hits.iter().find(|h| h.hit_kind == 2 || h.hit_kind == 3);
    let Some(h) = strong else {
        return Err(format!("GPU kernel hit was not Strong/Structural: {gpu_hits:?}").into());
    };
    if h.hit_kind == 2 {
        let diff = (h.z_score as f64 - cpu_z).abs();
        if diff > 0.05 {
            return Err(format!(
                "GPU z-score {} disagrees with CPU reference z-score {cpu_z} by {diff} -- kernel bug",
                h.z_score
            )
            .into());
        }
    }

    println!("[selftest] Known-positive Phase 3.2 vector: GPU and CPU agree (z_cpu={cpu_z:.2}).");
    Ok(())
}

fn run_negative_cross_check(
    gpu: &GpuOracle,
    blobs_list: &[Blob],
    variants: &[(i32, i32, i32)],
) -> Result<(), Box<dyn std::error::Error>> {
    let candidates: Vec<String> = NEGATIVE_PROBE_CANDIDATES.iter().map(|s| s.to_string()).collect();

    // CPU reference: full (candidate, variant, blob) grid.
    let mut cpu_hits: HashSet<(usize, usize, usize)> = HashSet::new();
    for (ci, cand) in candidates.iter().enumerate() {
        for (vi, &(kdf, key_len, mode)) in variants.iter().enumerate() {
            for (bi, blob) in blobs_list.iter().enumerate() {
                let (kind, _) = cpu_oracle::try_open(cand.as_bytes(), kdf, key_len as usize, mode, &blob.salt, &blob.ciphertext);
                if !matches!(kind, HitKind::None) {
                    cpu_hits.insert((ci, vi, bi));
                }
            }
        }
    }

    let mut gpu_hits: HashSet<(usize, usize, usize)> = HashSet::new();
    gpu.scan(
        &candidates,
        &HashSet::new(),
        blobs_list,
        variants,
        None,
        |hit| {
            gpu_hits.insert((hit.candidate_idx as usize, hit.variant_idx as usize, hit.blob_idx as usize));
        },
        |_| {},
        |_, _, _| {},
        |_| {},
        &std::sync::atomic::AtomicBool::new(false),
    )?;

    if cpu_hits != gpu_hits {
        let only_cpu: Vec<_> = cpu_hits.difference(&gpu_hits).collect();
        let only_gpu: Vec<_> = gpu_hits.difference(&cpu_hits).collect();
        return Err(format!(
            "GPU/CPU disagree on the negative probe grid ({} candidates x {} variants x {} blobs).\n\
             CPU found hits GPU missed: {only_cpu:?}\nGPU found hits CPU didn't: {only_gpu:?}",
            candidates.len(), variants.len(), blobs_list.len()
        )
        .into());
    }

    println!(
        "[selftest] Negative cross-check: {} candidates x {} variants x {} blobs, GPU and CPU agree \
         ({} shared hits, expected mostly/all zero).",
        candidates.len(), variants.len(), blobs_list.len(), cpu_hits.len()
    );
    Ok(())
}

/// SEED-CBC gate: no real puzzle blob has ever opened under SEED-CBC (it's a
/// Phase-253-motivated, thematically-supported but unconfirmed cipher
/// family), so there's no known-positive real vector to cross-check against
/// the way run_known_positive() does for AES. Instead, this builds a
/// synthetic SEED-encrypted blob from scratch (own key schedule, own CBC
/// chaining, independent of both cpu_oracle.rs and the CUDA port under
/// test) and confirms GPU and CPU agree on recovering it -- the same
/// "would a subtly wrong port silently produce a false negative" risk the
/// AES self-test guards against, just with a self-supplied positive vector
/// instead of a real one. Also negative-cross-checks the probe candidates
/// against SEED-CBC across all 4 real blobs (expected: no hits).
fn run_seed_cross_check(gpu: &GpuOracle, blobs_list: &[Blob]) -> Result<(), Box<dyn std::error::Error>> {
    let seed_variants = blobs::seed_variant_table();
    let kdf = seed_variants[0].0; // legacy-md5, key_len=16, CIPHER_SEED_CBC

    let salt: [u8; 8] = *b"seedgate";
    let candidate = "theseedisplanted";
    let (key, iv) = cpu_oracle::derive_key_iv(kdf, candidate.as_bytes(), &salt, 16, CIPHER_SEED_CBC);
    let mut key16 = [0u8; 16];
    let mut iv16 = [0u8; 16];
    key16.copy_from_slice(&key);
    iv16.copy_from_slice(&iv);
    let ks = seed_set_key(&key16);

    let plaintext = b"gsmgio the seed is planted here!"; // 32 printable bytes
    let mut padded = plaintext.to_vec();
    padded.extend(std::iter::repeat(16u8).take(16)); // full dummy pad block -> Structural

    let mut ct = Vec::new();
    let mut prev = iv16;
    for chunk in padded.chunks_exact(16) {
        let mut block_in = [0u8; 16];
        for i in 0..16 {
            block_in[i] = chunk[i] ^ prev[i];
        }
        let block_out = seed_encrypt_block(&ks, &block_in);
        ct.extend_from_slice(&block_out);
        prev = block_out;
    }

    let (cpu_kind, _) = cpu_oracle::try_open(candidate.as_bytes(), kdf, 16, CIPHER_SEED_CBC, &salt, &ct);
    if !matches!(cpu_kind, HitKind::Structural) {
        return Err(format!("CPU reference itself failed on the synthetic SEED-CBC vector: {cpu_kind:?}").into());
    }

    let seed_blob = Blob { tag: "SEED_SELFTEST", salt, ciphertext: ct };
    let candidates = vec![candidate.to_string()];
    let mut gpu_hits: Vec<DecryptHit> = Vec::new();
    gpu.scan(
        &candidates,
        &HashSet::new(),
        std::slice::from_ref(&seed_blob),
        std::slice::from_ref(&seed_variants[0]),
        None,
        |hit| gpu_hits.push(*hit),
        |_| {},
        |_, _, _| {},
        |_| {},
        &std::sync::atomic::AtomicBool::new(false),
    )?;

    let structural = gpu_hits.iter().find(|h| h.hit_kind == 3);
    if structural.is_none() {
        return Err(format!(
            "GPU kernel produced NO Structural hit for the synthetic SEED-CBC vector -- SEED CUDA port is broken. Hits: {gpu_hits:?}"
        )
        .into());
    }

    // Negative cross-check: probe candidates x all 4 SEED-CBC KDF variants x
    // all 4 real blobs -- expected all-miss, same as the AES negative grid.
    let candidates: Vec<String> = NEGATIVE_PROBE_CANDIDATES.iter().map(|s| s.to_string()).collect();
    let mut cpu_hits: HashSet<(usize, usize, usize)> = HashSet::new();
    for (ci, cand) in candidates.iter().enumerate() {
        for (vi, &(kdf, key_len, mode)) in seed_variants.iter().enumerate() {
            for (bi, blob) in blobs_list.iter().enumerate() {
                let (kind, _) = cpu_oracle::try_open(cand.as_bytes(), kdf, key_len as usize, mode, &blob.salt, &blob.ciphertext);
                if !matches!(kind, HitKind::None) {
                    cpu_hits.insert((ci, vi, bi));
                }
            }
        }
    }

    let mut gpu_hits: HashSet<(usize, usize, usize)> = HashSet::new();
    gpu.scan(
        &candidates,
        &HashSet::new(),
        blobs_list,
        &seed_variants,
        None,
        |hit| {
            gpu_hits.insert((hit.candidate_idx as usize, hit.variant_idx as usize, hit.blob_idx as usize));
        },
        |_| {},
        |_, _, _| {},
        |_| {},
        &std::sync::atomic::AtomicBool::new(false),
    )?;

    if cpu_hits != gpu_hits {
        return Err(format!(
            "GPU/CPU disagree on the SEED-CBC negative probe grid. CPU-only: {:?}, GPU-only: {:?}",
            cpu_hits.difference(&gpu_hits).collect::<Vec<_>>(),
            gpu_hits.difference(&cpu_hits).collect::<Vec<_>>()
        )
        .into());
    }

    println!(
        "[selftest] SEED-CBC cross-check: synthetic positive vector recovered (Structural), \
         negative probe grid ({} candidates x {} variants x {} blobs) GPU/CPU agree.",
        candidates.len(), seed_variants.len(), blobs_list.len()
    );
    Ok(())
}

/// Gate for `bloom_check_key_chunks` (kernels/aes_kdf_oracle.cu): a CBC/ECB/
/// SEED_CBC candidate whose decrypt is PKCS7-valid but neither structural
/// (full dummy pad) nor printable can still, in principle, have real key
/// bytes in its first 32-byte chunk -- previously only stream-mode (CFB/OFB/
/// CTR) candidates got Bloom-checked unconditionally; CBC/ECB/SEED_CBC did
/// not. Builds a synthetic AES-256-CBC blob whose body is [private key
/// bytes (32, non-printable) | 8 filler bytes (non-printable) | PKCS7 pad=8
/// (not 16, so NOT structural)], confirms the CPU reference sees no hit at
/// all (z-score gate correctly rejects it), then confirms the GPU kernel
/// still recovers the embedded key via the Bloom path.
fn run_cbc_bloom_chunk_check(gpu: &GpuOracle, _blobs_list: &[Blob]) -> Result<(), Box<dyn std::error::Error>> {
    use aes::cipher::{BlockEncryptMut, KeyIvInit};
    type Aes256CbcEnc = cbc::Encryptor<aes::Aes256>;

    let secp = secp256k1::Secp256k1::new();
    let mut private_key = [0u8; 32];
    private_key[31] = 1; // scalar 1 -- known address, already covered by crypto::tests
    let addresses = privkey_to_addresses(&secp, &private_key)
        .ok_or("scalar 1 must be a valid private key")?;

    let salt: [u8; 8] = *b"blmchunk";
    let candidate = "bloomchunkcandidate";
    let (key, iv) = cpu_oracle::derive_key_iv(KDF_LEGACY_SHA256, candidate.as_bytes(), &salt, 32, CIPHER_CBC);

    let mut body = Vec::with_capacity(48);
    body.extend_from_slice(&private_key); // chunk 0: the raw key, non-printable (mostly 0x00)
    body.extend_from_slice(&[0xffu8; 8]); // filler, also non-printable
    body.extend_from_slice(&[8u8; 8]); // valid PKCS7 pad=8 (NOT 16 -- must not be Structural)
    assert_eq!(body.len(), 48);

    let mut buf = body.clone();
    let ct_len = buf.len();
    let ct = Aes256CbcEnc::new_from_slices(&key, &iv)
        .map_err(|e| format!("CBC init failed: {e}"))?
        .encrypt_padded_mut::<aes::cipher::block_padding::NoPadding>(&mut buf, ct_len)
        .map_err(|e| format!("CBC encrypt failed: {e}"))?
        .to_vec();

    let (cpu_kind, _) = cpu_oracle::try_open(candidate.as_bytes(), KDF_LEGACY_SHA256, 32, CIPHER_CBC, &salt, &ct);
    if !matches!(cpu_kind, HitKind::None) {
        return Err(format!(
            "test vector construction bug: expected the CPU reference to see no z-score/structural \
             hit at all (this test exists specifically to prove the Bloom path catches what the \
             printable gate misses), got {cpu_kind:?}"
        )
        .into());
    }

    let bloom = BloomChecker::from_hash160_list(&[addresses.compressed_hash160]);
    let blob = Blob { tag: "BLOOM_CHUNK_SELFTEST", salt, ciphertext: ct };
    let candidates = vec![candidate.to_string()];
    let variant = (KDF_LEGACY_SHA256, 32, CIPHER_CBC);

    let mut stream_hits: Vec<StreamKeyHit> = Vec::new();
    gpu.scan(
        &candidates,
        &HashSet::new(),
        std::slice::from_ref(&blob),
        std::slice::from_ref(&variant),
        Some(&bloom),
        |_| {},
        |hit| stream_hits.push(*hit),
        |_, _, _| {},
        |_| {},
        &std::sync::atomic::AtomicBool::new(false),
    )?;

    let found = stream_hits.iter().find(|h| h.chunk_index == 0 && h.private_key == private_key);
    if found.is_none() {
        return Err(format!(
            "GPU kernel did NOT recover the embedded key via bloom_check_key_chunks on a non-\
             printable, non-structural CBC body -- the CBC/ECB/SEED_CBC Bloom-chunk path is broken. \
             stream_hits: {stream_hits:?}"
        )
        .into());
    }

    println!(
        "[selftest] CBC Bloom-chunk check: GPU recovered a raw key embedded in a non-printable, \
         non-structural CBC body (CPU z-score gate correctly saw no hit at all)."
    );
    Ok(())
}
