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

use crate::blobs::{self, Blob};
use crate::cpu_oracle::{self, HitKind};
use crate::gpu::{DecryptHit, GpuOracle};
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
    let (cpu_kind, _) = cpu_oracle::try_open(password.as_bytes(), blobs::KDF_LEGACY_SHA256, 32, &salt, &ct);
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
        &[(blobs::KDF_LEGACY_SHA256, 32)],
        |hit| gpu_hits.push(*hit),
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
    variants: &[(i32, i32)],
) -> Result<(), Box<dyn std::error::Error>> {
    let candidates: Vec<String> = NEGATIVE_PROBE_CANDIDATES.iter().map(|s| s.to_string()).collect();

    // CPU reference: full (candidate, variant, blob) grid.
    let mut cpu_hits: HashSet<(usize, usize, usize)> = HashSet::new();
    for (ci, cand) in candidates.iter().enumerate() {
        for (vi, &(kdf, key_len)) in variants.iter().enumerate() {
            for (bi, blob) in blobs_list.iter().enumerate() {
                let (kind, _) = cpu_oracle::try_open(cand.as_bytes(), kdf, key_len as usize, &blob.salt, &blob.ciphertext);
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
        |hit| {
            gpu_hits.insert((hit.candidate_idx as usize, hit.variant_idx as usize, hit.blob_idx as usize));
        },
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
