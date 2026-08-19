//! cudarc wiring + launch loop -- pattern copied from key-seeker's
//! src/gpu/milksad.rs (single stream, fixed-capacity hit buffer + atomic
//! counter, `checked_hit_count` overflow guard) rather than the
//! double-buffered src/gpu/cuda.rs, since our candidate scale (hundreds of
//! thousands to low millions) doesn't need the extra complexity.

use cudarc::driver::safe::{CudaContext, CudaSlice};
use cudarc::driver::PushKernelArg;
use cudarc::nvrtc::Ptx;
use std::sync::Arc;

use crate::blobs::{Blob, MAX_BLOB_CT_LEN};

pub const MAX_CANDIDATE_LEN: usize = 512; // must match kernels/aes_kdf_oracle.cu's MAX_CANDIDATE_LEN

const BLOCK_SIZE: u32 = 256;
const GRID_SIZE: u32 = 256;
const BATCH_CANDIDATES: u32 = GRID_SIZE * BLOCK_SIZE; // 65,536 candidates/launch
const MAX_HITS: u32 = 100_000;

// Empirically measured against this project's real db/addresses.hash160.bloom
// (m=958,505,856 bits, k=14, ~27% of bits set -- k wasn't re-optimized down
// for this file's actual, smaller-than-"optimal-tuning-assumes" entry count):
// zero false positives in 500,000 random 20-byte queries, true positive
// confirmed on the known genesis-address hash160. Implied real FP rate
// ~1e-8, not the ~1e-4 a naive "optimal k for this m/n" calculation would
// suggest -- so even at this kernel's full-corpus query volume (order 1e8),
// a few tens of thousands of expected false positives never materializes;
// expected count is closer to single digits. 10,000 capacity is generous
// headroom over that, not a tight bound.
const MAX_STREAM_HITS: u32 = 10_000;

// Layout must match struct DecryptHit in kernels/aes_kdf_oracle.cu exactly.
#[repr(C)]
#[derive(Debug, Default, Clone, Copy)]
pub struct DecryptHit {
    pub candidate_idx: u32,
    pub variant_idx: u32,
    pub blob_idx: u32,
    pub hit_kind: u32, // 1=weak, 2=strong, 3=structural
    pub z_score: f32,
    pub _pad: [u8; 12],
}

// SAFETY: DecryptHit is a plain-data, fixed-layout struct; all bit patterns are valid.
unsafe impl cudarc::driver::DeviceRepr for DecryptHit {}
unsafe impl cudarc::driver::ValidAsZeroBits for DecryptHit {}

// Layout must match struct StreamKeyHit in kernels/aes_kdf_oracle.cu exactly.
// Bloom-only, same as every other Bloom hit in this project: the host still
// runs the mandatory live API confirmation (keyshape::record_precomputed_hit)
// before treating anything here as real.
#[repr(C)]
#[derive(Debug, Default, Clone, Copy)]
pub struct StreamKeyHit {
    pub candidate_idx: u32,
    pub variant_idx: u32,
    pub blob_idx: u32,
    pub chunk_index: u32,  // 0 = half, 1 = better_half
    pub address_type: u32, // 0 = compressed, 1 = uncompressed
    pub private_key: [u8; 32],
    pub hash160: [u8; 20],
    pub _pad: [u8; 8],
}

// SAFETY: StreamKeyHit is a plain-data, fixed-layout struct; all bit patterns are valid.
unsafe impl cudarc::driver::DeviceRepr for StreamKeyHit {}
unsafe impl cudarc::driver::ValidAsZeroBits for StreamKeyHit {}

pub(crate) fn checked_hit_count(raw_count: u32, capacity: u32) -> Result<usize, Box<dyn std::error::Error>> {
    if raw_count > capacity {
        return Err(format!(
            "GPU hit buffer overflow: {raw_count} matches exceeded capacity {capacity}; \
             aborting rather than silently dropping candidates. Re-run with a smaller batch \
             or raise MAX_HITS."
        )
        .into());
    }
    Ok(raw_count as usize)
}

pub struct GpuOracle {
    ctx: Arc<CudaContext>,
}

impl GpuOracle {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let ctx = CudaContext::new(0)?;
        Ok(Self { ctx })
    }

    pub fn device_name(&self) -> Result<String, Box<dyn std::error::Error>> {
        Ok(self.ctx.name()?)
    }

    /// Runs the full scan over `candidates` (already-expanded passphrase
    /// strings), skipping any index present in `skip_indices` (resume
    /// support). Calls `on_hit` for every raw GPU hit (weak/strong/structural)
    /// -- caller is responsible for CPU-side re-verification before treating
    /// anything as real, matching this project's house rule that the GPU
    /// tool is a finder, not a source of truth.
    ///
    /// `bloom`, when `Some`, is also checked entirely on-device against every
    /// CFB/OFB/CTR candidate's decrypted half/better_half chunks (see
    /// aes_kdf_oracle.cu's stream-mode branch) -- `on_stream_key_hit` fires
    /// for each Bloom hit (same "Bloom pre-filters, host does the mandatory
    /// live API confirmation" contract as every other Bloom hit in this
    /// project; see keyshape::record_precomputed_hit). `None` (no local
    /// Bloom cache) skips this check entirely, same as `--no-bloom-verify`.
    #[allow(clippy::too_many_arguments)]
    pub fn scan<F, G>(
        &self,
        candidates: &[String],
        skip_indices: &std::collections::HashSet<u64>,
        blobs: &[Blob],
        variants: &[(i32, i32, i32)],
        bloom: Option<&crate::checker::BloomChecker>,
        mut on_hit: F,
        mut on_stream_key_hit: G,
        mut on_progress: impl FnMut(u64, u64, f64),
        mut on_batch_done: impl FnMut(&[u32]),
        interrupted: &std::sync::atomic::AtomicBool,
    ) -> Result<(), Box<dyn std::error::Error>>
    where
        F: FnMut(&DecryptHit),
        G: FnMut(&StreamKeyHit),
    {
        let ptx_bytes = include_bytes!(env!("AES_KDF_ORACLE_PTX_PATH"));
        let ptx = Ptx::from_src(std::str::from_utf8(ptx_bytes)?);
        let module = self.ctx.load_module(ptx)?;
        let stream = self.ctx.default_stream();

        eprintln!("[gpu] Device: {}", self.ctx.name()?);

        // Upload the fixed blob table once.
        {
            let mut salts_flat = vec![0u8; blobs.len() * 8];
            let mut cts_flat = vec![0u8; blobs.len() * MAX_BLOB_CT_LEN];
            let mut ct_lens = vec![0u32; blobs.len()];
            for (i, b) in blobs.iter().enumerate() {
                salts_flat[i * 8..i * 8 + 8].copy_from_slice(&b.salt);
                assert!(b.ciphertext.len() <= MAX_BLOB_CT_LEN, "{} exceeds MAX_BLOB_CT_LEN", b.tag);
                cts_flat[i * MAX_BLOB_CT_LEN..i * MAX_BLOB_CT_LEN + b.ciphertext.len()]
                    .copy_from_slice(&b.ciphertext);
                ct_lens[i] = b.ciphertext.len() as u32;
            }
            let salts_dev: CudaSlice<u8> = stream.clone_htod(&salts_flat)?;
            let cts_dev: CudaSlice<u8> = stream.clone_htod(&cts_flat)?;
            let lens_dev: CudaSlice<u32> = stream.clone_htod(&ct_lens)?;
            let count = blobs.len() as u32;

            let init_fn = module.load_function("blob_init")?;
            unsafe {
                stream
                    .launch_builder(&init_fn)
                    .arg(&salts_dev)
                    .arg(&cts_dev)
                    .arg(&lens_dev)
                    .arg(&count)
                    .launch(cudarc::driver::LaunchConfig { grid_dim: (1, 1, 1), block_dim: (1, 1, 1), shared_mem_bytes: 0 })?;
            }
            stream.synchronize()?;
        }

        // Upload the fixed variant table once.
        {
            let kdf_kinds: Vec<i32> = variants.iter().map(|(k, _, _)| *k).collect();
            let key_lens: Vec<i32> = variants.iter().map(|(_, l, _)| *l).collect();
            let modes: Vec<i32> = variants.iter().map(|(_, _, m)| *m).collect();
            let kdf_dev: CudaSlice<i32> = stream.clone_htod(&kdf_kinds)?;
            let keylen_dev: CudaSlice<i32> = stream.clone_htod(&key_lens)?;
            let mode_dev: CudaSlice<i32> = stream.clone_htod(&modes)?;
            let count = variants.len() as u32;

            let init_fn = module.load_function("variant_init")?;
            unsafe {
                stream
                    .launch_builder(&init_fn)
                    .arg(&kdf_dev)
                    .arg(&keylen_dev)
                    .arg(&mode_dev)
                    .arg(&count)
                    .launch(cudarc::driver::LaunchConfig { grid_dim: (1, 1, 1), block_dim: (1, 1, 1), shared_mem_bytes: 0 })?;
            }
            stream.synchronize()?;
        }

        // Populate the precomputed G-table required by scalar_mul_G (see
        // secp256k1_device.cuh) -- needed even when `bloom` is None, since
        // the stream-mode branch always derives hash160s before checking
        // bloom_m > 0; gtable_init just wouldn't matter functionally if it
        // weren't called, but skipping it isn't worth a special case.
        {
            let (gtable_x, gtable_y) = crate::gtable::compute_gtable();
            let gtable_x_dev: CudaSlice<u32> = stream.clone_htod(&gtable_x)?;
            let gtable_y_dev: CudaSlice<u32> = stream.clone_htod(&gtable_y)?;
            let init_fn = module.load_function("gtable_init")?;
            unsafe {
                stream
                    .launch_builder(&init_fn)
                    .arg(&gtable_x_dev)
                    .arg(&gtable_y_dev)
                    .launch(cudarc::driver::LaunchConfig { grid_dim: (1, 1, 1), block_dim: (256, 1, 1), shared_mem_bytes: 0 })?;
            }
            stream.synchronize()?;
        }

        // Upload the Bloom filter bits once, kept resident for the whole
        // scan. `bloom_m == 0` tells the kernel to skip the stream-mode
        // Bloom check entirely (see aes_kdf_oracle.cu) -- used for both
        // `bloom.is_none()` and as the harmless value passed alongside a
        // required-but-then-unused dummy device slice.
        let (bloom_bits_dev, bloom_m, bloom_k): (CudaSlice<u64>, u64, u32) = match bloom {
            Some(b) => (stream.clone_htod(b.raw_bits())?, b.num_bits(), b.num_hashes()),
            None => (stream.alloc_zeros(1)?, 0, 0),
        };

        let func = module.load_function("aes_kdf_scan")?;

        // Indices not already checkpointed as done, in order.
        let pending: Vec<u32> = (0..candidates.len() as u64)
            .filter(|i| !skip_indices.contains(i))
            .map(|i| i as u32)
            .collect();

        let mut hits_dev: CudaSlice<DecryptHit> = stream.alloc_zeros(MAX_HITS as usize)?;
        let mut hit_count_dev: CudaSlice<u32> = stream.alloc_zeros(1)?;
        let mut stream_hits_dev: CudaSlice<StreamKeyHit> = stream.alloc_zeros(MAX_STREAM_HITS as usize)?;
        let mut stream_hit_count_dev: CudaSlice<u32> = stream.alloc_zeros(1)?;

        let total = pending.len() as u64;
        let mut done: u64 = 0;
        let t0 = std::time::Instant::now();

        for chunk in pending.chunks(BATCH_CANDIDATES as usize) {
            if interrupted.load(std::sync::atomic::Ordering::SeqCst) {
                eprintln!("[gpu] stopping before next batch (interrupted, progress already checkpointed)");
                break;
            }
            let batch = chunk.len() as u32;

            let mut cand_flat = vec![0u8; chunk.len() * MAX_CANDIDATE_LEN];
            let mut cand_lens = vec![0u32; chunk.len()];
            for (i, &orig_idx) in chunk.iter().enumerate() {
                let s = candidates[orig_idx as usize].as_bytes();
                assert!(
                    s.len() <= MAX_CANDIDATE_LEN,
                    "candidate {orig_idx} is {} bytes, exceeds MAX_CANDIDATE_LEN={MAX_CANDIDATE_LEN}",
                    s.len()
                );
                cand_flat[i * MAX_CANDIDATE_LEN..i * MAX_CANDIDATE_LEN + s.len()].copy_from_slice(s);
                cand_lens[i] = s.len() as u32;
            }
            let cand_dev: CudaSlice<u8> = stream.clone_htod(&cand_flat)?;
            let lens_dev: CudaSlice<u32> = stream.clone_htod(&cand_lens)?;

            stream.memset_zeros(&mut hit_count_dev)?;
            stream.memset_zeros(&mut stream_hit_count_dev)?;
            let grid_needed = (batch + BLOCK_SIZE - 1) / BLOCK_SIZE;
            let cfg = cudarc::driver::LaunchConfig {
                grid_dim: (grid_needed, 1, 1),
                block_dim: (BLOCK_SIZE, 1, 1),
                shared_mem_bytes: 0,
            };

            unsafe {
                let mut builder = stream.launch_builder(&func);
                builder.arg(&cand_dev);
                builder.arg(&lens_dev);
                builder.arg(&batch);
                builder.arg(&mut hits_dev);
                builder.arg(&mut hit_count_dev);
                builder.arg(&MAX_HITS);
                builder.arg(&bloom_bits_dev);
                builder.arg(&bloom_m);
                builder.arg(&bloom_k);
                builder.arg(&mut stream_hits_dev);
                builder.arg(&mut stream_hit_count_dev);
                builder.arg(&MAX_STREAM_HITS);
                builder.launch(cfg)?;
            }
            self.ctx.synchronize()?;

            let hit_count_host = stream.clone_dtoh(&hit_count_dev)?;
            let n_hits = checked_hit_count(hit_count_host[0], MAX_HITS)?;
            if n_hits > 0 {
                let hits_host = stream.clone_dtoh(&hits_dev)?;
                for h in &hits_host[..n_hits] {
                    // candidate_idx from the kernel is an index into THIS
                    // batch's flat buffer, i.e. chunk[h.candidate_idx] is the
                    // real index into `candidates`.
                    let mut h_fixed = *h;
                    h_fixed.candidate_idx = chunk[h.candidate_idx as usize];
                    on_hit(&h_fixed);
                }
            }

            let stream_hit_count_host = stream.clone_dtoh(&stream_hit_count_dev)?;
            let n_stream_hits = checked_hit_count(stream_hit_count_host[0], MAX_STREAM_HITS)?;
            if n_stream_hits > 0 {
                let stream_hits_host = stream.clone_dtoh(&stream_hits_dev)?;
                for h in &stream_hits_host[..n_stream_hits] {
                    let mut h_fixed = *h;
                    h_fixed.candidate_idx = chunk[h.candidate_idx as usize];
                    on_stream_key_hit(&h_fixed);
                }
            }

            done += batch as u64;
            let elapsed = t0.elapsed().as_secs_f64();
            on_progress(done, total, elapsed);
            on_batch_done(chunk);
        }

        Ok(())
    }
}
