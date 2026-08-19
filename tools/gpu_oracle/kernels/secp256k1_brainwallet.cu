/*
 * secp256k1_brainwallet.cu — standalone GPU key-shape deriver used by
 * secp256k1_gpu.rs (stream_key_check.rs's fallback path when the merged
 * on-device flow in aes_kdf_oracle.cu isn't used, e.g. no GPU available at
 * all -- see that file's own header comment for the primary, merged path).
 *
 * Field/EC/hash primitives come from secp256k1_device.cuh -- see its header
 * comment for provenance (a verbatim excerpt of
 * ../../../key-seeker/kernels/secp256k1.cu, not a hand-port).
 */

#include "secp256k1_device.cuh"

/*
 * secp256k1_brainwallet — one thread per arbitrary 32-byte private key.
 * Compressed-hash160 only. Kept for parity with upstream key-seeker;
 * secp256k1_brainwallet_both below is what this project actually uses
 * (crypto.rs always checks both compressed and uncompressed).
 *
 * Input:  privkeys[count × 32]  — raw 32-byte big-endian private keys
 * Output: hash160_out[count × 20] — Bitcoin hash160 per key
 */
extern "C" __global__ void secp256k1_brainwallet(
    const uint8_t *privkeys,
    uint64_t count,
    uint8_t *hash160_out
) {
    uint64_t tid = (uint64_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= count) return;

    JacPoint P = scalar_mul_G(privkeys + tid * 32);
    uint256 ax, ay;
    jac_to_affine(P, ax, ay);

    uint8_t pubkey[33];
    serialize_pubkey(ax, ay, pubkey);
    uint8_t sha_out[32];
    sha256_33(pubkey, sha_out);
    ripemd160_32(sha_out, hash160_out + tid * 20);
}

/*
 * secp256k1_brainwallet_both — like secp256k1_brainwallet, but derives both
 * the compressed and uncompressed hash160 per key in one launch.
 *
 * Input:  privkeys[count × 32]        — raw 32-byte big-endian private keys
 * Output: hash160_compressed_out[count × 20]
 *         hash160_uncompressed_out[count × 20]
 */
extern "C" __global__ void secp256k1_brainwallet_both(
    const uint8_t *privkeys,
    uint64_t count,
    uint8_t *hash160_compressed_out,
    uint8_t *hash160_uncompressed_out
) {
    uint64_t tid = (uint64_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= count) return;

    derive_hash160_both(privkeys + tid * 32, hash160_compressed_out + tid * 20, hash160_uncompressed_out + tid * 20);
}
