//! GPU secp256k1 point-mult + hash160 derivation for arbitrary 32-byte key
//! material, via kernels/secp256k1_brainwallet.cu's `secp256k1_brainwallet_both`
//! kernel (see that file's header comment for provenance). Used by
//! stream_key_check.rs to move the actual bottleneck off CPU: a plain
//! rayon-parallel CPU loop (secp256k1 crate, one scalar_mul per chunk)
//! measured ~176 candidates/s aggregate for the full medium_curated_all.txt
//! stream-cipher sweep on this project's dev machine -- a real GPU
//! (RTX 5070) behind a comparatively weak CPU, so pushing the EC math onto
//! the GPU is the difference between a ~50min run and a ~1min one.
//!
//! Unlike `gpu.rs`'s `GpuOracle::scan`, this has no Bloom/API step of its
//! own -- it only derives hash160s. `stream_key_check.rs` still does the
//! Bloom pre-filter + mandatory API confirmation on CPU via the existing
//! `checker::VerifiedBloomChecker`/`keyshape::KeyShapeWriter`, so a real hit
//! goes through the exact same audit trail as a CBC/ECB structural hit.

use cudarc::driver::safe::{CudaContext, CudaSlice};
use cudarc::driver::PushKernelArg;
use cudarc::nvrtc::Ptx;
use std::sync::Arc;

const BLOCK_SIZE: u32 = 256;
/// Keys per kernel launch -- matches key-seeker's src/gpu/brainwallet.rs.
const BATCH_KEYS: usize = 1024 * BLOCK_SIZE as usize; // 262,144

pub struct GpuKeyDeriver {
    ctx: Arc<CudaContext>,
}

impl GpuKeyDeriver {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let ctx = CudaContext::new(0)?;
        Ok(Self { ctx })
    }

    pub fn device_name(&self) -> Result<String, Box<dyn std::error::Error>> {
        Ok(self.ctx.name()?)
    }

    /// Derives `(compressed_hash160, uncompressed_hash160)` for every entry
    /// in `keys`, in the same order. Batches internally at `BATCH_KEYS`
    /// entries per launch, so `keys` can be arbitrarily large without an
    /// oversized single allocation/launch.
    pub fn derive_hash160_pairs(&self, keys: &[[u8; 32]]) -> Result<Vec<([u8; 20], [u8; 20])>, Box<dyn std::error::Error>> {
        let ptx_bytes = include_bytes!(env!("SECP256K1_BRAINWALLET_PTX_PATH"));
        let ptx = Ptx::from_src(std::str::from_utf8(ptx_bytes)?);
        let module = self.ctx.load_module(ptx)?;
        let stream = self.ctx.default_stream();

        // Populate the precomputed G-table required by scalar_mul_G -- once,
        // regardless of how many batches `keys` needs below.
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

        let func = module.load_function("secp256k1_brainwallet_both")?;
        let mut out = Vec::with_capacity(keys.len());

        for chunk in keys.chunks(BATCH_KEYS) {
            let count = chunk.len();
            let mut keys_flat = vec![0u8; count * 32];
            for (i, k) in chunk.iter().enumerate() {
                keys_flat[i * 32..i * 32 + 32].copy_from_slice(k);
            }

            let keys_dev: CudaSlice<u8> = stream.clone_htod(&keys_flat)?;
            let mut compressed_dev: CudaSlice<u8> = stream.alloc_zeros(count * 20)?;
            let mut uncompressed_dev: CudaSlice<u8> = stream.alloc_zeros(count * 20)?;
            let count_u64 = count as u64;

            let grid_size = (count as u32 + BLOCK_SIZE - 1) / BLOCK_SIZE;
            let cfg = cudarc::driver::LaunchConfig { grid_dim: (grid_size, 1, 1), block_dim: (BLOCK_SIZE, 1, 1), shared_mem_bytes: 0 };

            unsafe {
                stream
                    .launch_builder(&func)
                    .arg(&keys_dev)
                    .arg(&count_u64)
                    .arg(&mut compressed_dev)
                    .arg(&mut uncompressed_dev)
                    .launch(cfg)?;
            }
            self.ctx.synchronize()?;

            let compressed_host = stream.clone_dtoh(&compressed_dev)?;
            let uncompressed_host = stream.clone_dtoh(&uncompressed_dev)?;
            for i in 0..count {
                let c: [u8; 20] = compressed_host[i * 20..i * 20 + 20].try_into().unwrap();
                let u: [u8; 20] = uncompressed_host[i * 20..i * 20 + 20].try_into().unwrap();
                out.push((c, u));
            }
        }

        Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Known vectors (same ones crypto.rs's CPU-side tests use): key=1 and
    /// key=2 have well-known compressed/uncompressed hash160s. Requires a
    /// real GPU -- skips gracefully (rather than failing the whole suite)
    /// when none is available, matching this project's other real-hardware
    /// tests (e.g. checker/bloom.rs's real_bloom_cache_recognizes_genesis_address).
    #[test]
    fn known_privkey_1_and_2_hash160s_match_cpu_reference() {
        let Ok(deriver) = GpuKeyDeriver::new() else {
            eprintln!("[secp256k1_gpu test] no GPU available, skipping");
            return;
        };

        let mut key1 = [0u8; 32];
        key1[31] = 1;
        let mut key2 = [0u8; 32];
        key2[31] = 2;

        let secp = secp256k1::Secp256k1::new();
        let addrs1 = crate::crypto::privkey_to_addresses(&secp, &key1).unwrap();
        let addrs2 = crate::crypto::privkey_to_addresses(&secp, &key2).unwrap();

        let results = deriver.derive_hash160_pairs(&[key1, key2]).expect("GPU derive should succeed");
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].0, addrs1.compressed_hash160, "key=1 compressed hash160 mismatch");
        assert_eq!(results[0].1, addrs1.uncompressed_hash160, "key=1 uncompressed hash160 mismatch");
        assert_eq!(results[1].0, addrs2.compressed_hash160, "key=2 compressed hash160 mismatch");
        assert_eq!(results[1].1, addrs2.uncompressed_hash160, "key=2 uncompressed hash160 mismatch");
    }

    #[test]
    fn batches_larger_than_one_launch_produce_correct_count() {
        let Ok(deriver) = GpuKeyDeriver::new() else {
            eprintln!("[secp256k1_gpu test] no GPU available, skipping");
            return;
        };
        // A little over one BATCH_KEYS launch, to prove the chunking loop
        // stitches results back together in order across multiple launches.
        let n = BATCH_KEYS + 100;
        let mut keys = Vec::with_capacity(n);
        for i in 0..n {
            let mut k = [0u8; 32];
            k[28..32].copy_from_slice(&((i as u32) + 1).to_be_bytes());
            keys.push(k);
        }
        let results = deriver.derive_hash160_pairs(&keys).expect("GPU derive should succeed");
        assert_eq!(results.len(), n);

        let secp = secp256k1::Secp256k1::new();
        let addrs_last = crate::crypto::privkey_to_addresses(&secp, keys.last().unwrap()).unwrap();
        assert_eq!(results[n - 1].0, addrs_last.compressed_hash160);
    }
}
