/*
 * secp256k1_device.cuh — device-only functions (no __global__ kernels, so
 * safe to #include from more than one .cu compilation unit), extracted from
 * ../../../key-seeker's kernels/secp256k1.cu. See
 * kernels/secp256k1_brainwallet.cu's header comment for why this is a
 * verbatim copy rather than a hand-port, and why only lines 1-1361 +
 * murmur3_x86_32_20/bloom_check (the field/EC/hash/bloom primitives, not the
 * numeric-range-batch or kangaroo kernels) were pulled in.
 *
 * Used by two .cu files, each compiled to its own standalone PTX module
 * (this project's build.rs doesn't use nvcc's `-rdc=true` relocatable device
 * code, so cross-TU device-function linking isn't available -- a header
 * textually included by both is the straightforward alternative):
 *   - kernels/secp256k1_brainwallet.cu: standalone GPU key-shape deriver
 *     (secp256k1_gpu.rs), used when stream_key_check.rs falls back off the
 *     merged kernel path below (no GPU, or GPU init failed).
 *   - kernels/aes_kdf_oracle.cu: the merged on-device path -- decrypt, KDF,
 *     AND now (Phase 325 GPU-KDF merge) secp256k1 point-mult + hash160 +
 *     Bloom check for stream-mode candidates, entirely inside `aes_kdf_scan`,
 *     with zero host round-trip except on an actual (rare) Bloom hit. This
 *     is the fix for the finding that a CPU-decrypt + GPU-point-mult split
 *     pipeline gained almost nothing: PBKDF2-HMAC-SHA256/10000 (already
 *     on-device in aes_kdf_oracle.cu, see its own pbkdf2_hmac_sha256), not
 *     point multiplication, was the actual bottleneck -- so the fix has to
 *     put the KDF and the EC math in the same kernel, not just the EC math.
 *
 * `derive_hash160_both`, appended at the end of this header after the
 * excerpt, is new: a small wrapper combining scalar_mul_G + both pubkey
 * serializations + their hashes, so callers don't repeat that sequence.
 *
 * ── original upstream header ──
 * secp256k1.cu — CUDA kernel for Bitcoin address derivation
 *
 * Pipeline per thread:
 *   starting_key + thread_id * stride
 *   → one full EC scalar multiply (double-and-add)
 *   → loop stride times:
 *       → serialize compressed pubkey (33 bytes)
 *       → SHA256(pubkey) → RIPEMD160 → hash160[20]
 *       → store to output buffer
 *       → P = P + G  (incremental point addition)
 *
 * Field arithmetic adapted from BitCrack (MIT License)
 * https://github.com/brichard19/BitCrack
 */

#include <stdint.h>
#include <string.h>

// ── secp256k1 parameters ────────────────────────────────────────────────────

// p = 2^256 - 2^32 - 977
__device__ __constant__ uint32_t FIELD_P[8] = {
    0xFFFFFC2F, 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFF,
    0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF
};

// n (curve order)
__device__ __constant__ uint32_t CURVE_N[8] = {
    0xD0364141, 0xBFD25E8C, 0xAF48A03B, 0xBAAEDCE6,
    0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF
};

// G.x
__device__ __constant__ uint32_t GX[8] = {
    0x16F81798, 0x59F2815B, 0x2DCE28D9, 0x029BFCDB,
    0xCE870B07, 0x55A06295, 0xF9DCBBAC, 0x79BE667E
};

// G.y
__device__ __constant__ uint32_t GY[8] = {
    0xFB10D4B8, 0x9C47D08F, 0xA6855419, 0xFD17B448,
    0x0E1108A8, 0x5DA4FBFC, 0x26A3C465, 0x483ADA77
};

// Precomputed G-table: GTABLE_X[i] / GTABLE_Y[i] = affine coords of 2^i × G.
// Populated once at startup by the gtable_init kernel via the Rust host.
// Using __device__ (not __constant__) so the host can write via a device pointer.
// Warp-uniform access pattern means L1/L2 broadcast handles this with the same
// efficiency as constant memory for this workload.
__device__ uint32_t GTABLE_X[256][8];
__device__ uint32_t GTABLE_Y[256][8];

// Exact puzzle targets: up to 8 × 20-byte hash160s for GPU-side exact matching.
// Populated once at startup by the exact_targets_init kernel via the Rust host.
// Using __device__ (not __constant__) so the host can write via a device pointer.
// Warp-uniform access pattern means L1/L2 broadcast handles this with the same
// efficiency as constant memory for this workload.
__device__ uint8_t  EXACT_TARGETS[8 * 20];
__device__ uint32_t N_EXACT_TARGETS;

// ── 256-bit integer type ────────────────────────────────────────────────────

typedef struct { uint32_t v[8]; } uint256;

__device__ bool u256_equal(const uint256 &a, const uint256 &b) {
    for (int i = 0; i < 8; i++) if (a.v[i] != b.v[i]) return false;
    return true;
}

__device__ bool u256_is_zero(const uint256 &a) {
    for (int i = 0; i < 8; i++) if (a.v[i]) return false;
    return true;
}

// a < b (big-endian word order)
__device__ bool u256_lt(const uint256 &a, const uint256 &b) {
    for (int i = 7; i >= 0; i--) {
        if (a.v[i] < b.v[i]) return true;
        if (a.v[i] > b.v[i]) return false;
    }
    return false;
}

// c = a + b mod 2^256, returns carry  (PTX carry-chain, lever E; little-endian v[0]=LSW)
__device__ uint32_t u256_add(uint256 &c, const uint256 &a, const uint256 &b) {
    uint32_t carry;
    asm volatile(
        "add.cc.u32  %0, %9,  %17;\n\t"
        "addc.cc.u32 %1, %10, %18;\n\t"
        "addc.cc.u32 %2, %11, %19;\n\t"
        "addc.cc.u32 %3, %12, %20;\n\t"
        "addc.cc.u32 %4, %13, %21;\n\t"
        "addc.cc.u32 %5, %14, %22;\n\t"
        "addc.cc.u32 %6, %15, %23;\n\t"
        "addc.cc.u32 %7, %16, %24;\n\t"
        "addc.u32    %8, 0, 0;\n\t"
        // early-clobber (&): outputs must not alias still-live inputs (c may alias a/b).
        : "=&r"(c.v[0]),"=&r"(c.v[1]),"=&r"(c.v[2]),"=&r"(c.v[3]),
          "=&r"(c.v[4]),"=&r"(c.v[5]),"=&r"(c.v[6]),"=&r"(c.v[7]),"=&r"(carry)
        : "r"(a.v[0]),"r"(a.v[1]),"r"(a.v[2]),"r"(a.v[3]),
          "r"(a.v[4]),"r"(a.v[5]),"r"(a.v[6]),"r"(a.v[7]),
          "r"(b.v[0]),"r"(b.v[1]),"r"(b.v[2]),"r"(b.v[3]),
          "r"(b.v[4]),"r"(b.v[5]),"r"(b.v[6]),"r"(b.v[7]));
    return carry;
}

// c = a - b mod 2^256, returns borrow (0/1)  (PTX carry-chain, lever E)
__device__ uint32_t u256_sub(uint256 &c, const uint256 &a, const uint256 &b) {
    uint32_t borrow;
    asm volatile(
        "sub.cc.u32  %0, %9,  %17;\n\t"
        "subc.cc.u32 %1, %10, %18;\n\t"
        "subc.cc.u32 %2, %11, %19;\n\t"
        "subc.cc.u32 %3, %12, %20;\n\t"
        "subc.cc.u32 %4, %13, %21;\n\t"
        "subc.cc.u32 %5, %14, %22;\n\t"
        "subc.cc.u32 %6, %15, %23;\n\t"
        "subc.cc.u32 %7, %16, %24;\n\t"
        "subc.u32    %8, 0, 0;\n\t"      // 0-0-borrow = 0xFFFFFFFF iff final borrow
        : "=&r"(c.v[0]),"=&r"(c.v[1]),"=&r"(c.v[2]),"=&r"(c.v[3]),
          "=&r"(c.v[4]),"=&r"(c.v[5]),"=&r"(c.v[6]),"=&r"(c.v[7]),"=&r"(borrow)
        : "r"(a.v[0]),"r"(a.v[1]),"r"(a.v[2]),"r"(a.v[3]),
          "r"(a.v[4]),"r"(a.v[5]),"r"(a.v[6]),"r"(a.v[7]),
          "r"(b.v[0]),"r"(b.v[1]),"r"(b.v[2]),"r"(b.v[3]),
          "r"(b.v[4]),"r"(b.v[5]),"r"(b.v[6]),"r"(b.v[7]));
    return borrow & 1u;
}

// ── Field arithmetic mod p ──────────────────────────────────────────────────

__device__ uint256 field_p() {
    uint256 r; for (int i = 0; i < 8; i++) r.v[i] = FIELD_P[i]; return r;
}

// secp256k1 prime is 2^256 - C with C = 0x1_00_00_03_D1 (= 2^32 + 977); only the two
// low words of C are non-zero. Inputs are assumed reduced (< p), matching the prior code.
// fp_add: s = a+b (carry); t = s + C (carry2); reduced result = (carry|carry2) ? t : s.
//   carry  set  ⇒ a+b ≥ 2^256 = p+C ⇒ a+b-p = s+C = t.
//   carry2 set  ⇒ s ≥ p (since s+C ≥ p+C = 2^256) ⇒ s-p = t.  Else s already < p.
// No field_p() rebuild, no u256_lt, branchless select. (lever E)
__device__ uint256 fp_add(const uint256 &a, const uint256 &b) {
    uint256 s, t;
    uint32_t carry  = u256_add(s, a, b);
    uint32_t carry2;
    asm volatile(
        "add.cc.u32  %0, %9,  0x000003D1;\n\t"
        "addc.cc.u32 %1, %10, 0x00000001;\n\t"
        "addc.cc.u32 %2, %11, 0;\n\t"
        "addc.cc.u32 %3, %12, 0;\n\t"
        "addc.cc.u32 %4, %13, 0;\n\t"
        "addc.cc.u32 %5, %14, 0;\n\t"
        "addc.cc.u32 %6, %15, 0;\n\t"
        "addc.cc.u32 %7, %16, 0;\n\t"
        "addc.u32    %8, 0, 0;\n\t"
        : "=&r"(t.v[0]),"=&r"(t.v[1]),"=&r"(t.v[2]),"=&r"(t.v[3]),
          "=&r"(t.v[4]),"=&r"(t.v[5]),"=&r"(t.v[6]),"=&r"(t.v[7]),"=&r"(carry2)
        : "r"(s.v[0]),"r"(s.v[1]),"r"(s.v[2]),"r"(s.v[3]),
          "r"(s.v[4]),"r"(s.v[5]),"r"(s.v[6]),"r"(s.v[7]));
    uint32_t use_t = carry | carry2;
    uint256 r;
    #pragma unroll
    for (int i = 0; i < 8; i++) r.v[i] = use_t ? t.v[i] : s.v[i];
    return r;
}

// fp_sub: d = a-b (borrow); if borrow, d += p = d - C (mod 2^256). Branchless via mask.
__device__ uint256 fp_sub(const uint256 &a, const uint256 &b) {
    uint256 d;
    uint32_t borrow = u256_sub(d, a, b);
    uint32_t clo = borrow ? 0x000003D1u : 0u;   // C low word, masked
    uint32_t chi = borrow ? 0x00000001u : 0u;   // C second word, masked
    asm volatile(
        "sub.cc.u32  %0, %0, %8;\n\t"
        "subc.cc.u32 %1, %1, %9;\n\t"
        "subc.cc.u32 %2, %2, 0;\n\t"
        "subc.cc.u32 %3, %3, 0;\n\t"
        "subc.cc.u32 %4, %4, 0;\n\t"
        "subc.cc.u32 %5, %5, 0;\n\t"
        "subc.cc.u32 %6, %6, 0;\n\t"
        "subc.cc.u32 %7, %7, 0;\n\t"
        : "+&r"(d.v[0]),"+&r"(d.v[1]),"+&r"(d.v[2]),"+&r"(d.v[3]),
          "+&r"(d.v[4]),"+&r"(d.v[5]),"+&r"(d.v[6]),"+&r"(d.v[7])
        : "r"(clo),"r"(chi));
    return d;
}

// ── PTX carry-chain modular multiply (lever B) ───────────────────────────────
// Ported from BitCrack (MIT) but emitted as SINGLE asm blocks: a carry chain split
// across separate asm-volatile statements can be broken by compiler-inserted spills
// (clobbering CC.CF) → wrong results. One block per chain keeps the carry intact.
// BitCrack word order is BIG-ENDIAN (w[7]=LSW); kept internally, adapted at fp_mul.
// See doc/KANGAROO_PTX_MULMOD_PLAN.md.

__device__ __constant__ uint32_t BC_P[8] = {
    0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF,
    0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFE, 0xFFFFFC2F
};

// c = c + b (in place), returns carry.  b read-only.
__device__ static uint32_t bc_add(uint32_t c[8], const uint32_t b[8]) {
    uint32_t ret;
    asm volatile(
        "add.cc.u32 %7, %7, %16;\n\t"
        "addc.cc.u32 %6, %6, %15;\n\t"
        "addc.cc.u32 %5, %5, %14;\n\t"
        "addc.cc.u32 %4, %4, %13;\n\t"
        "addc.cc.u32 %3, %3, %12;\n\t"
        "addc.cc.u32 %2, %2, %11;\n\t"
        "addc.cc.u32 %1, %1, %10;\n\t"
        "addc.cc.u32 %0, %0, %9;\n\t"
        "addc.u32 %8, 0, 0;\n\t"
        // early-clobber (&): outputs are written before all inputs are consumed,
        // so ptxas must not alias an output onto a still-live input register.
        : "+&r"(c[0]),"+&r"(c[1]),"+&r"(c[2]),"+&r"(c[3]),"+&r"(c[4]),"+&r"(c[5]),"+&r"(c[6]),"+&r"(c[7]), "=&r"(ret)
        : "r"(b[0]),"r"(b[1]),"r"(b[2]),"r"(b[3]),"r"(b[4]),"r"(b[5]),"r"(b[6]),"r"(b[7]));
    return ret;
}

// c = c - b (in place), returns borrow (0/1).  b read-only.
__device__ static uint32_t bc_sub(uint32_t c[8], const uint32_t b[8]) {
    uint32_t ret;
    asm volatile(
        "sub.cc.u32 %7, %7, %16;\n\t"
        "subc.cc.u32 %6, %6, %15;\n\t"
        "subc.cc.u32 %5, %5, %14;\n\t"
        "subc.cc.u32 %4, %4, %13;\n\t"
        "subc.cc.u32 %3, %3, %12;\n\t"
        "subc.cc.u32 %2, %2, %11;\n\t"
        "subc.cc.u32 %1, %1, %10;\n\t"
        "subc.cc.u32 %0, %0, %9;\n\t"
        "subc.u32 %8, 0, 0;\n\t"
        // early-clobber (&): outputs are written before all inputs are consumed.
        : "+&r"(c[0]),"+&r"(c[1]),"+&r"(c[2]),"+&r"(c[3]),"+&r"(c[4]),"+&r"(c[5]),"+&r"(c[6]),"+&r"(c[7]), "=&r"(ret)
        : "r"(b[0]),"r"(b[1]),"r"(b[2]),"r"(b[3]),"r"(b[4]),"r"(b[5]),"r"(b[6]),"r"(b[7]));
    return ret & 1u;
}

// c = (a * b) mod p.  Single-block multiply + secp fast reduction, then normalise.
__device__ static void bc_mulModP(const uint32_t a[8], const uint32_t b[8], uint32_t c[8]) {
    for (int i = 0; i < 8; i++) c[i] = 0;
    uint32_t overflow_w;
    asm volatile(
        "{\n\t"
        ".reg .u32 h0,h1,h2,h3,h4,h5,h6,h7,h6s,h7s,T;\n\t"
        "mov.u32 h0,0; mov.u32 h1,0; mov.u32 h2,0; mov.u32 h3,0;\n\t"
        "mov.u32 h4,0; mov.u32 h5,0; mov.u32 h6,0; mov.u32 h7,0;\n\t"
        "mov.u32 T, %16;\n\t"
        "mul.lo.u32 %0, T, %17;\n\t"
        "mul.lo.u32 %1, T, %18;\n\t"
        "mul.lo.u32 %2, T, %19;\n\t"
        "mul.lo.u32 %3, T, %20;\n\t"
        "mul.lo.u32 %4, T, %21;\n\t"
        "mul.lo.u32 %5, T, %22;\n\t"
        "mul.lo.u32 %6, T, %23;\n\t"
        "mul.lo.u32 %7, T, %24;\n\t"
        "mad.hi.cc.u32 %6, T, %24, %6;\n\t"
        "madc.hi.cc.u32 %5, T, %23, %5;\n\t"
        "madc.hi.cc.u32 %4, T, %22, %4;\n\t"
        "madc.hi.cc.u32 %3, T, %21, %3;\n\t"
        "madc.hi.cc.u32 %2, T, %20, %2;\n\t"
        "madc.hi.cc.u32 %1, T, %19, %1;\n\t"
        "madc.hi.cc.u32 %0, T, %18, %0;\n\t"
        "madc.hi.u32 h7, T, %17, h7;\n\t"
        "mov.u32 T, %15;\n\t"
        "mad.lo.cc.u32 %6, T, %24, %6;\n\t"
        "madc.lo.cc.u32 %5, T, %23, %5;\n\t"
        "madc.lo.cc.u32 %4, T, %22, %4;\n\t"
        "madc.lo.cc.u32 %3, T, %21, %3;\n\t"
        "madc.lo.cc.u32 %2, T, %20, %2;\n\t"
        "madc.lo.cc.u32 %1, T, %19, %1;\n\t"
        "madc.lo.cc.u32 %0, T, %18, %0;\n\t"
        "madc.lo.cc.u32 h7, T, %17, h7;\n\t"
        "addc.u32 h6, h6, 0;\n\t"
        "mad.hi.cc.u32 %5, T, %24, %5;\n\t"
        "madc.hi.cc.u32 %4, T, %23, %4;\n\t"
        "madc.hi.cc.u32 %3, T, %22, %3;\n\t"
        "madc.hi.cc.u32 %2, T, %21, %2;\n\t"
        "madc.hi.cc.u32 %1, T, %20, %1;\n\t"
        "madc.hi.cc.u32 %0, T, %19, %0;\n\t"
        "madc.hi.cc.u32 h7, T, %18, h7;\n\t"
        "madc.hi.u32 h6, T, %17, h6;\n\t"
        "mov.u32 T, %14;\n\t"
        "mad.lo.cc.u32 %5, T, %24, %5;\n\t"
        "madc.lo.cc.u32 %4, T, %23, %4;\n\t"
        "madc.lo.cc.u32 %3, T, %22, %3;\n\t"
        "madc.lo.cc.u32 %2, T, %21, %2;\n\t"
        "madc.lo.cc.u32 %1, T, %20, %1;\n\t"
        "madc.lo.cc.u32 %0, T, %19, %0;\n\t"
        "madc.lo.cc.u32 h7, T, %18, h7;\n\t"
        "madc.lo.cc.u32 h6, T, %17, h6;\n\t"
        "addc.u32 h5, h5, 0;\n\t"
        "mad.hi.cc.u32 %4, T, %24, %4;\n\t"
        "madc.hi.cc.u32 %3, T, %23, %3;\n\t"
        "madc.hi.cc.u32 %2, T, %22, %2;\n\t"
        "madc.hi.cc.u32 %1, T, %21, %1;\n\t"
        "madc.hi.cc.u32 %0, T, %20, %0;\n\t"
        "madc.hi.cc.u32 h7, T, %19, h7;\n\t"
        "madc.hi.cc.u32 h6, T, %18, h6;\n\t"
        "madc.hi.u32 h5, T, %17, h5;\n\t"
        "mov.u32 T, %13;\n\t"
        "mad.lo.cc.u32 %4, T, %24, %4;\n\t"
        "madc.lo.cc.u32 %3, T, %23, %3;\n\t"
        "madc.lo.cc.u32 %2, T, %22, %2;\n\t"
        "madc.lo.cc.u32 %1, T, %21, %1;\n\t"
        "madc.lo.cc.u32 %0, T, %20, %0;\n\t"
        "madc.lo.cc.u32 h7, T, %19, h7;\n\t"
        "madc.lo.cc.u32 h6, T, %18, h6;\n\t"
        "madc.lo.cc.u32 h5, T, %17, h5;\n\t"
        "addc.u32 h4, h4, 0;\n\t"
        "mad.hi.cc.u32 %3, T, %24, %3;\n\t"
        "madc.hi.cc.u32 %2, T, %23, %2;\n\t"
        "madc.hi.cc.u32 %1, T, %22, %1;\n\t"
        "madc.hi.cc.u32 %0, T, %21, %0;\n\t"
        "madc.hi.cc.u32 h7, T, %20, h7;\n\t"
        "madc.hi.cc.u32 h6, T, %19, h6;\n\t"
        "madc.hi.cc.u32 h5, T, %18, h5;\n\t"
        "madc.hi.u32 h4, T, %17, h4;\n\t"
        "mov.u32 T, %12;\n\t"
        "mad.lo.cc.u32 %3, T, %24, %3;\n\t"
        "madc.lo.cc.u32 %2, T, %23, %2;\n\t"
        "madc.lo.cc.u32 %1, T, %22, %1;\n\t"
        "madc.lo.cc.u32 %0, T, %21, %0;\n\t"
        "madc.lo.cc.u32 h7, T, %20, h7;\n\t"
        "madc.lo.cc.u32 h6, T, %19, h6;\n\t"
        "madc.lo.cc.u32 h5, T, %18, h5;\n\t"
        "madc.lo.cc.u32 h4, T, %17, h4;\n\t"
        "addc.u32 h3, h3, 0;\n\t"
        "mad.hi.cc.u32 %2, T, %24, %2;\n\t"
        "madc.hi.cc.u32 %1, T, %23, %1;\n\t"
        "madc.hi.cc.u32 %0, T, %22, %0;\n\t"
        "madc.hi.cc.u32 h7, T, %21, h7;\n\t"
        "madc.hi.cc.u32 h6, T, %20, h6;\n\t"
        "madc.hi.cc.u32 h5, T, %19, h5;\n\t"
        "madc.hi.cc.u32 h4, T, %18, h4;\n\t"
        "madc.hi.u32 h3, T, %17, h3;\n\t"
        "mov.u32 T, %11;\n\t"
        "mad.lo.cc.u32 %2, T, %24, %2;\n\t"
        "madc.lo.cc.u32 %1, T, %23, %1;\n\t"
        "madc.lo.cc.u32 %0, T, %22, %0;\n\t"
        "madc.lo.cc.u32 h7, T, %21, h7;\n\t"
        "madc.lo.cc.u32 h6, T, %20, h6;\n\t"
        "madc.lo.cc.u32 h5, T, %19, h5;\n\t"
        "madc.lo.cc.u32 h4, T, %18, h4;\n\t"
        "madc.lo.cc.u32 h3, T, %17, h3;\n\t"
        "addc.u32 h2, h2, 0;\n\t"
        "mad.hi.cc.u32 %1, T, %24, %1;\n\t"
        "madc.hi.cc.u32 %0, T, %23, %0;\n\t"
        "madc.hi.cc.u32 h7, T, %22, h7;\n\t"
        "madc.hi.cc.u32 h6, T, %21, h6;\n\t"
        "madc.hi.cc.u32 h5, T, %20, h5;\n\t"
        "madc.hi.cc.u32 h4, T, %19, h4;\n\t"
        "madc.hi.cc.u32 h3, T, %18, h3;\n\t"
        "madc.hi.u32 h2, T, %17, h2;\n\t"
        "mov.u32 T, %10;\n\t"
        "mad.lo.cc.u32 %1, T, %24, %1;\n\t"
        "madc.lo.cc.u32 %0, T, %23, %0;\n\t"
        "madc.lo.cc.u32 h7, T, %22, h7;\n\t"
        "madc.lo.cc.u32 h6, T, %21, h6;\n\t"
        "madc.lo.cc.u32 h5, T, %20, h5;\n\t"
        "madc.lo.cc.u32 h4, T, %19, h4;\n\t"
        "madc.lo.cc.u32 h3, T, %18, h3;\n\t"
        "madc.lo.cc.u32 h2, T, %17, h2;\n\t"
        "addc.u32 h1, h1, 0;\n\t"
        "mad.hi.cc.u32 %0, T, %24, %0;\n\t"
        "madc.hi.cc.u32 h7, T, %23, h7;\n\t"
        "madc.hi.cc.u32 h6, T, %22, h6;\n\t"
        "madc.hi.cc.u32 h5, T, %21, h5;\n\t"
        "madc.hi.cc.u32 h4, T, %20, h4;\n\t"
        "madc.hi.cc.u32 h3, T, %19, h3;\n\t"
        "madc.hi.cc.u32 h2, T, %18, h2;\n\t"
        "madc.hi.u32 h1, T, %17, h1;\n\t"
        "mov.u32 T, %9;\n\t"
        "mad.lo.cc.u32 %0, T, %24, %0;\n\t"
        "madc.lo.cc.u32 h7, T, %23, h7;\n\t"
        "madc.lo.cc.u32 h6, T, %22, h6;\n\t"
        "madc.lo.cc.u32 h5, T, %21, h5;\n\t"
        "madc.lo.cc.u32 h4, T, %20, h4;\n\t"
        "madc.lo.cc.u32 h3, T, %19, h3;\n\t"
        "madc.lo.cc.u32 h2, T, %18, h2;\n\t"
        "madc.lo.cc.u32 h1, T, %17, h1;\n\t"
        "addc.u32 h0, h0, 0;\n\t"
        "mad.hi.cc.u32 h7, T, %24, h7;\n\t"
        "madc.hi.cc.u32 h6, T, %23, h6;\n\t"
        "madc.hi.cc.u32 h5, T, %22, h5;\n\t"
        "madc.hi.cc.u32 h4, T, %21, h4;\n\t"
        "madc.hi.cc.u32 h3, T, %20, h3;\n\t"
        "madc.hi.cc.u32 h2, T, %19, h2;\n\t"
        "madc.hi.cc.u32 h1, T, %18, h1;\n\t"
        "madc.hi.u32 h0, T, %17, h0;\n\t"
        "mov.u32 h7s, h7;\n\t"
        "mov.u32 h6s, h6;\n\t"
        "add.cc.u32 %6, h7, %6;\n\t"
        "addc.cc.u32 %5, h6, %5;\n\t"
        "addc.cc.u32 %4, h5, %4;\n\t"
        "addc.cc.u32 %3, h4, %3;\n\t"
        "addc.cc.u32 %2, h3, %2;\n\t"
        "addc.cc.u32 %1, h2, %1;\n\t"
        "addc.cc.u32 %0, h1, %0;\n\t"
        "addc.cc.u32 h7, h0, 0;\n\t"
        "addc.u32 h6, 0, 0;\n\t"
        "mad.lo.cc.u32 %7, h7s, 977, %7;\n\t"
        "madc.lo.cc.u32 %6, h6s, 977, %6;\n\t"
        "madc.lo.cc.u32 %5, h5, 977, %5;\n\t"
        "madc.lo.cc.u32 %4, h4, 977, %4;\n\t"
        "madc.lo.cc.u32 %3, h3, 977, %3;\n\t"
        "madc.lo.cc.u32 %2, h2, 977, %2;\n\t"
        "madc.lo.cc.u32 %1, h1, 977, %1;\n\t"
        "madc.lo.cc.u32 %0, h0, 977, %0;\n\t"
        "addc.cc.u32 h7, h7, 0;\n\t"
        "addc.u32 h6, h6, 0;\n\t"
        "mad.hi.cc.u32 %6, h7s, 977, %6;\n\t"
        "madc.hi.cc.u32 %5, h6s, 977, %5;\n\t"
        "madc.hi.cc.u32 %4, h5, 977, %4;\n\t"
        "madc.hi.cc.u32 %3, h4, 977, %3;\n\t"
        "madc.hi.cc.u32 %2, h3, 977, %2;\n\t"
        "madc.hi.cc.u32 %1, h2, 977, %1;\n\t"
        "madc.hi.cc.u32 %0, h1, 977, %0;\n\t"
        "madc.hi.cc.u32 h7, h0, 977, h7;\n\t"
        "addc.u32 h6, h6, 0;\n\t"
        "mov.u32 h7s, h7;\n\t"
        "mov.u32 h6s, h6;\n\t"
        "add.cc.u32 %6, h7, %6;\n\t"
        "addc.cc.u32 %5, h6, %5;\n\t"
        "addc.cc.u32 %4, %4, 0;\n\t"
        "addc.cc.u32 %3, %3, 0;\n\t"
        "addc.cc.u32 %2, %2, 0;\n\t"
        "addc.cc.u32 %1, %1, 0;\n\t"
        "addc.cc.u32 %0, %0, 0;\n\t"
        "addc.u32 h7, 0, 0;\n\t"
        "mad.lo.cc.u32 %7, h7s, 977, %7;\n\t"
        "madc.lo.cc.u32 %6, h6s, 977, %6;\n\t"
        "addc.cc.u32 %5, %5, 0;\n\t"
        "addc.cc.u32 %4, %4, 0;\n\t"
        "addc.cc.u32 %3, %3, 0;\n\t"
        "addc.cc.u32 %2, %2, 0;\n\t"
        "addc.cc.u32 %1, %1, 0;\n\t"
        "addc.cc.u32 %0, %0, 0;\n\t"
        "addc.u32 h7, h7, 0;\n\t"
        "mad.hi.cc.u32 %6, h7s, 977, %6;\n\t"
        "madc.hi.cc.u32 %5, h6s, 977, %5;\n\t"
        "addc.cc.u32 %4, %4, 0;\n\t"
        "addc.cc.u32 %3, %3, 0;\n\t"
        "addc.cc.u32 %2, %2, 0;\n\t"
        "addc.cc.u32 %1, %1, 0;\n\t"
        "addc.cc.u32 %0, %0, 0;\n\t"
        "addc.u32 h7, h7, 0;\n\t"
        "mov.u32 %8, h7;\n\t"
        "}\n\t"
        // early-clobber (&): the multiply writes the c[] outputs in its first
        // instructions but keeps reading the a[] inputs (%9..%16) to the end, so
        // ptxas must not reuse an input register as an output. Without this the
        // path miscompiles under register pressure (scalar_mul_G/jac_add_affine).
        : "+&r"(c[0]),"+&r"(c[1]),"+&r"(c[2]),"+&r"(c[3]),"+&r"(c[4]),"+&r"(c[5]),"+&r"(c[6]),"+&r"(c[7]), "=&r"(overflow_w)
        : "r"(a[0]),"r"(a[1]),"r"(a[2]),"r"(a[3]),"r"(a[4]),"r"(a[5]),"r"(a[6]),"r"(a[7]),
          "r"(b[0]),"r"(b[1]),"r"(b[2]),"r"(b[3]),"r"(b[4]),"r"(b[5]),"r"(b[6]),"r"(b[7]));
    bool overflow = overflow_w != 0;
    uint32_t borrow = bc_sub(c, BC_P);
    if (overflow) { if (!borrow) bc_sub(c, BC_P); }
    else          { if ( borrow) bc_add(c, BC_P); }
}

// ── Lever J: 64-bit-limb PTX modular multiply (doc/KANGAROO_PTX_J_64BIT_PLAN.md) ──
// SHELVED 2026-06-21 (qualified result, like lever F). Correct (20 049-case num-bigint
// differential + #55/#66 solve) and full-mulmod SASS is −31%/−90% carry-ops vs 32-bit, BUT
// in-kernel it costs +20 registers (80→100): classic grp gains +8.9% (1487→1619 Msteps/s)
// yet the latency-bound SOTA grp — the #135 path — LOSES 26% (1409→1036). maxrregcount can't
// recover it. Net loss for the actual goal, so kept dormant behind KS_LEVER_J_64BIT (default
// off ⇒ build identical to the proven 32-bit path). See KANGAROO_PTX_J_64BIT_PLAN.md and
// [[project_ptx_64bit_madcc_trap]]. NOTE: uses mul.lo/mul.hi + add.cc chains, NOT mad.cc.u64
// (the 64-bit mad.cc forms miscompile on ptxas 12.8/sm_120 — see the plan doc).
//
// [LEVER X Phase 4b] These 64-bit primitives are now ALWAYS compiled (the native u64[4] field layer
// `fe_*` below + KernelA64 use them directly). Only the fp_mul *swap* stays behind KS_LEVER_J_64BIT.
#define SECP_C64 0x1000003D1ULL
__device__ __constant__ uint64_t BC_P64[4] = {
    0xFFFFFFFEFFFFFC2FULL, 0xFFFFFFFFFFFFFFFFULL,
    0xFFFFFFFFFFFFFFFFULL, 0xFFFFFFFFFFFFFFFFULL
};

// c = c + b (4×u64, in place), returns carry.  Early-clobber: outputs written before
// all inputs consumed (see FP_MUL_EARLYCLOBBER_FIX_PLAN.md).
__device__ static uint32_t bc_add64(uint64_t c[4], const uint64_t b[4]) {
    uint64_t ret;
    asm volatile(
        "add.cc.u64  %0, %0, %5;\n\t"
        "addc.cc.u64 %1, %1, %6;\n\t"
        "addc.cc.u64 %2, %2, %7;\n\t"
        "addc.cc.u64 %3, %3, %8;\n\t"
        "addc.u64    %4, 0, 0;\n\t"
        : "+&l"(c[0]),"+&l"(c[1]),"+&l"(c[2]),"+&l"(c[3]),"=&l"(ret)
        : "l"(b[0]),"l"(b[1]),"l"(b[2]),"l"(b[3]));
    return (uint32_t)ret;
}

// c = c - b (4×u64, in place), returns borrow (0/1).
__device__ static uint32_t bc_sub64(uint64_t c[4], const uint64_t b[4]) {
    uint64_t ret;
    asm volatile(
        "sub.cc.u64  %0, %0, %5;\n\t"
        "subc.cc.u64 %1, %1, %6;\n\t"
        "subc.cc.u64 %2, %2, %7;\n\t"
        "subc.cc.u64 %3, %3, %8;\n\t"
        "subc.u64    %4, 0, 0;\n\t"   // 0 if no borrow, all-ones if borrow
        : "+&l"(c[0]),"+&l"(c[1]),"+&l"(c[2]),"+&l"(c[3]),"=&l"(ret)
        : "l"(b[0]),"l"(b[1]),"l"(b[2]),"l"(b[3]));
    return (uint32_t)(ret & 1ULL);
}

// c = (a * b) mod p, all little-endian 4×u64.
//
// IMPORTANT — uses ONLY mul.lo/mul.hi + add.cc/addc chains, NOT mad.{lo,hi}.cc.u64.
// The fused 64-bit multiply-add-with-carry forms MISCOMPILE on ptxas 12.8/sm_120 with
// runtime operands (a two-pass operand-scan `mad.hi.cc.u64` chain silently produces wrong
// high limbs — verified vs host over 500k random; the 32-bit mad.cc.u32 forms are fine).
// Constant-folded single-thread tests hide it, so every block below was validated at scale
// with non-constant inputs. Each carry chain is its own asm block (spike-style, robust).
// Even without mad-fusion this is −31% SASS / −90% IADD3 / −7 registers vs the 32-bit path.
__device__ static void bc_mulModP_64(const uint64_t a[4], const uint64_t b[4], uint64_t c[4]) {
    const uint64_t a0=a[0],a1=a[1],a2=a[2],a3=a[3],b0=b[0],b1=b[1],b2=b[2],b3=b[3];
    uint64_t p0,p1,p2,p3,p4,p5,p6,p7;
    // 4×4 schoolbook, one row (a_i × b → 5-limb partial) per block, carries propagated up.
    // row0: p0..p4 = a0·b   (ai=%5, b=%6..%9)
    asm volatile("{\n\t.reg .u64 L0,L1,L2,L3,H0,H1,H2,H3;\n\t"
      "mul.lo.u64 L0,%5,%6; mul.lo.u64 L1,%5,%7; mul.lo.u64 L2,%5,%8; mul.lo.u64 L3,%5,%9;\n\t"
      "mul.hi.u64 H0,%5,%6; mul.hi.u64 H1,%5,%7; mul.hi.u64 H2,%5,%8; mul.hi.u64 H3,%5,%9;\n\t"
      "mov.u64 %0,L0; add.cc.u64 %1,L1,H0; addc.cc.u64 %2,L2,H1; addc.cc.u64 %3,L3,H2; addc.u64 %4,H3,0;\n\t}\n\t"
      : "=&l"(p0),"=&l"(p1),"=&l"(p2),"=&l"(p3),"=&l"(p4)
      : "l"(a0),"l"(b0),"l"(b1),"l"(b2),"l"(b3));
    p5=0; p6=0; p7=0;
    // row1: p1..p7 += a1·b   (ai=%7, b=%8..%11)
    asm volatile("{\n\t.reg .u64 L0,L1,L2,L3,H0,H1,H2,H3,q1,q2,q3,q4;\n\t"
      "mul.lo.u64 L0,%7,%8; mul.lo.u64 L1,%7,%9; mul.lo.u64 L2,%7,%10; mul.lo.u64 L3,%7,%11;\n\t"
      "mul.hi.u64 H0,%7,%8; mul.hi.u64 H1,%7,%9; mul.hi.u64 H2,%7,%10; mul.hi.u64 H3,%7,%11;\n\t"
      "add.cc.u64 q1,L1,H0; addc.cc.u64 q2,L2,H1; addc.cc.u64 q3,L3,H2; addc.u64 q4,H3,0;\n\t"
      "add.cc.u64 %0,%0,L0; addc.cc.u64 %1,%1,q1; addc.cc.u64 %2,%2,q2; addc.cc.u64 %3,%3,q3; addc.cc.u64 %4,%4,q4; addc.cc.u64 %5,%5,0; addc.u64 %6,%6,0;\n\t}\n\t"
      : "+&l"(p1),"+&l"(p2),"+&l"(p3),"+&l"(p4),"+&l"(p5),"+&l"(p6),"+&l"(p7)
      : "l"(a1),"l"(b0),"l"(b1),"l"(b2),"l"(b3));
    // row2: p2..p7 += a2·b   (ai=%6, b=%7..%10)
    asm volatile("{\n\t.reg .u64 L0,L1,L2,L3,H0,H1,H2,H3,q1,q2,q3,q4;\n\t"
      "mul.lo.u64 L0,%6,%7; mul.lo.u64 L1,%6,%8; mul.lo.u64 L2,%6,%9; mul.lo.u64 L3,%6,%10;\n\t"
      "mul.hi.u64 H0,%6,%7; mul.hi.u64 H1,%6,%8; mul.hi.u64 H2,%6,%9; mul.hi.u64 H3,%6,%10;\n\t"
      "add.cc.u64 q1,L1,H0; addc.cc.u64 q2,L2,H1; addc.cc.u64 q3,L3,H2; addc.u64 q4,H3,0;\n\t"
      "add.cc.u64 %0,%0,L0; addc.cc.u64 %1,%1,q1; addc.cc.u64 %2,%2,q2; addc.cc.u64 %3,%3,q3; addc.cc.u64 %4,%4,q4; addc.u64 %5,%5,0;\n\t}\n\t"
      : "+&l"(p2),"+&l"(p3),"+&l"(p4),"+&l"(p5),"+&l"(p6),"+&l"(p7)
      : "l"(a2),"l"(b0),"l"(b1),"l"(b2),"l"(b3));
    // row3: p3..p7 += a3·b   (ai=%5, b=%6..%9)
    asm volatile("{\n\t.reg .u64 L0,L1,L2,L3,H0,H1,H2,H3,q1,q2,q3,q4;\n\t"
      "mul.lo.u64 L0,%5,%6; mul.lo.u64 L1,%5,%7; mul.lo.u64 L2,%5,%8; mul.lo.u64 L3,%5,%9;\n\t"
      "mul.hi.u64 H0,%5,%6; mul.hi.u64 H1,%5,%7; mul.hi.u64 H2,%5,%8; mul.hi.u64 H3,%5,%9;\n\t"
      "add.cc.u64 q1,L1,H0; addc.cc.u64 q2,L2,H1; addc.cc.u64 q3,L3,H2; addc.u64 q4,H3,0;\n\t"
      "add.cc.u64 %0,%0,L0; addc.cc.u64 %1,%1,q1; addc.cc.u64 %2,%2,q2; addc.cc.u64 %3,%3,q3; addc.u64 %4,%4,q4;\n\t}\n\t"
      : "+&l"(p3),"+&l"(p4),"+&l"(p5),"+&l"(p6),"+&l"(p7)
      : "l"(a3),"l"(b0),"l"(b1),"l"(b2),"l"(b3));

    // Reduction: N ≡ lo + hi·C (mod p), lo=p[0..3], hi=p[4..7], C=0x1000003D1.
    const uint64_t Cv = SECP_C64;
    // fold1: t[0..4] = p[0..3] + p[4..7]·C  (hi·C via mul.lo/mul.hi + add, no mad.cc)
    uint64_t t0, t1, t2, t3, t4;
    asm volatile("{\n\t.reg .u64 m0,m1,m2,m3,m4,h0,h1,h2,h3;\n\t"
      "mul.lo.u64 m0,%9,%13; mul.lo.u64 m1,%10,%13; mul.lo.u64 m2,%11,%13; mul.lo.u64 m3,%12,%13;\n\t"
      "mul.hi.u64 h0,%9,%13; mul.hi.u64 h1,%10,%13; mul.hi.u64 h2,%11,%13; mul.hi.u64 h3,%12,%13;\n\t"
      "add.cc.u64 m1,m1,h0; addc.cc.u64 m2,m2,h1; addc.cc.u64 m3,m3,h2; addc.u64 m4,h3,0;\n\t"
      "add.cc.u64 %0,%5,m0; addc.cc.u64 %1,%6,m1; addc.cc.u64 %2,%7,m2; addc.cc.u64 %3,%8,m3; addc.u64 %4,m4,0;\n\t}\n\t"
      : "=&l"(t0),"=&l"(t1),"=&l"(t2),"=&l"(t3),"=&l"(t4)
      : "l"(p0),"l"(p1),"l"(p2),"l"(p3),"l"(p4),"l"(p5),"l"(p6),"l"(p7),"l"(Cv));
    // fold2: c[0..3] = t[0..3] + t4·C ; cf = carry out of bit 256 (0/1)
    uint64_t cf;
    asm volatile("{\n\t.reg .u64 lo2,hi2;\n\tmul.lo.u64 lo2,%9,%10; mul.hi.u64 hi2,%9,%10;\n\t"
      "add.cc.u64 %0,%5,lo2; addc.cc.u64 %1,%6,hi2; addc.cc.u64 %2,%7,0; addc.cc.u64 %3,%8,0; addc.u64 %4,0,0;\n\t}\n\t"
      : "=&l"(c[0]),"=&l"(c[1]),"=&l"(c[2]),"=&l"(c[3]),"=&l"(cf)
      : "l"(t0),"l"(t1),"l"(t2),"l"(t3),"l"(t4),"l"(Cv));
    // if cf: value ≥ 2²⁵⁶ ⇒ ≡ c + C (mod p); c[0..3] < 2⁶⁷ here so +C cannot overflow.
    if (cf) {
        asm volatile("add.cc.u64 %0,%0,%4; addc.cc.u64 %1,%1,0; addc.cc.u64 %2,%2,0; addc.u64 %3,%3,0;\n\t"
            : "+&l"(c[0]),"+&l"(c[1]),"+&l"(c[2]),"+&l"(c[3]) : "l"(Cv));
    }
    // c ∈ [0, 2²⁵⁶) < 2p ⇒ one conditional subtract canonicalises to [0, p).
    uint32_t borrow = bc_sub64(c, BC_P64);
    if (borrow) bc_add64(c, BC_P64);   // c was < p ⇒ restore
}

#ifdef KS_LEVER_J_64BIT
// fp_mul on the 64-bit path (lever J, opt-in via KS_LEVER_J_64BIT). LE32↔LE64 repack.
__device__ uint256 fp_mul(const uint256 &A, const uint256 &B) {
    uint64_t a[4], b[4], c[4];
#pragma unroll
    for (int i = 0; i < 4; i++) {
        a[i] = ((uint64_t)A.v[2*i+1] << 32) | A.v[2*i];
        b[i] = ((uint64_t)B.v[2*i+1] << 32) | B.v[2*i];
    }
    bc_mulModP_64(a, b, c);
    uint256 r;
#pragma unroll
    for (int i = 0; i < 4; i++) { r.v[2*i] = (uint32_t)c[i]; r.v[2*i+1] = (uint32_t)(c[i] >> 32); }
    return r;
}
#else // !KS_LEVER_J_64BIT — default: proven lever-B 32-bit BitCrack path

// PTX modular multiply over our little-endian uint256 (lever B; the hot-path fp_mul).
// Index reversal is pure register relabelling — the optimiser removes the copies.
__device__ uint256 fp_mul(const uint256 &A, const uint256 &B) {
    uint32_t a[8], b[8], c[8];
#pragma unroll
    for (int i = 0; i < 8; i++) { a[i] = A.v[7 - i]; b[i] = B.v[7 - i]; }
    bc_mulModP(a, b, c);
    uint256 r;
#pragma unroll
    for (int i = 0; i < 8; i++) r.v[i] = c[7 - i];
    return r;
}
#endif // KS_LEVER_J_64BIT

__device__ uint256 fp_sqr(const uint256 &a) { return fp_mul(a, a); }

// [D5] doc/KANGAROO_D5_FPMUL_NOINLINE_PLAN.md: thin __noinline__ wrapper delegating to the existing
// fp_mul unchanged -- the __noinline__ qualifier is the entire experimental variable, no second
// arithmetic implementation to keep in sync. Used only by secp256k1_kernelA_jl_fpmul_noinline below;
// every other fp_mul/fp_sqr caller is untouched.
__device__ __noinline__ uint256 fp_mul_noinline(const uint256 &A, const uint256 &B) {
    return fp_mul(A, B);
}

// ── Bernstein–Yang "safegcd" modular inverse (divstep) ───────────────────────
// Clean-room port of libsecp256k1 `modinv32_impl.h` (MIT, © Peter Dettman) — the
// constant-time 30-bit-limb path. This is the cheap GRP-independent inverse that
// replaces the ~384-mul Fermat fp_inv and unlocks the small-group operating point
// (doc/KANGAROO_DIVSTEP_PLAN.md, Phase 1). We keep the 32-bit limb variant (not the
// 64-bit modinv64) to match our existing field representation and dodge the ptxas
// 64-bit mad.cc trap (project_ptx_64bit_madcc_trap). Numbers are signed 30-bit
// limbs in int32_t[9] (little-endian), value = Σ limb[i]·2^(30·i).
#define MI_M30 ((int32_t)0x3FFFFFFF)          // mask for the low 30 bits
#define MI_MOD_INV30 (0x2DDACACFu)            // 1/(p mod 2^30) = (-977)^-1 mod 2^30 (Montgomery low-limb inv)
// secp256k1 field prime p = 2^256-2^32-977 in 9×30-bit little-endian limbs.
__device__ __constant__ int32_t MI_MOD[9] = {
    0x3FFFFC2F, 0x3FFFFFFB, 0x3FFFFFFF, 0x3FFFFFFF, 0x3FFFFFFF,
    0x3FFFFFFF, 0x3FFFFFFF, 0x3FFFFFFF, 0x0000FFFF
};

typedef struct { int32_t u, v, q, r; } mi_trans2x2;  // t = [[u,v],[q,r]]

// uint256 (8×32-bit LE) → 9×30-bit signed limbs (all limbs in [0,2^30)).
__device__ void mi_to_signed30(int32_t r[9], const uint256 &a) {
    const uint32_t M = 0x3FFFFFFFu;
    r[0] =  a.v[0]                          & M;
    r[1] = ((a.v[0] >> 30) | (a.v[1] <<  2)) & M;
    r[2] = ((a.v[1] >> 28) | (a.v[2] <<  4)) & M;
    r[3] = ((a.v[2] >> 26) | (a.v[3] <<  6)) & M;
    r[4] = ((a.v[3] >> 24) | (a.v[4] <<  8)) & M;
    r[5] = ((a.v[4] >> 22) | (a.v[5] << 10)) & M;
    r[6] = ((a.v[5] >> 20) | (a.v[6] << 12)) & M;
    r[7] = ((a.v[6] >> 18) | (a.v[7] << 14)) & M;
    r[8] =  (a.v[7] >> 16);                       // top 16 bits
}

// 9×30-bit signed limbs (normalized: each in [0,2^30), value < p) → uint256 (8×32-bit LE).
__device__ uint256 mi_from_signed30(const int32_t a_[9]) {
    uint32_t a[9];
    #pragma unroll
    for (int i = 0; i < 9; i++) a[i] = (uint32_t)a_[i];
    uint256 r;
    r.v[0] =  a[0]        | (a[1] << 30);
    r.v[1] = (a[1] >>  2) | (a[2] << 28);
    r.v[2] = (a[2] >>  4) | (a[3] << 26);
    r.v[3] = (a[3] >>  6) | (a[4] << 24);
    r.v[4] = (a[4] >>  8) | (a[5] << 22);
    r.v[5] = (a[5] >> 10) | (a[6] << 20);
    r.v[6] = (a[6] >> 12) | (a[7] << 18);
    r.v[7] = (a[7] >> 14) | (a[8] << 16);
    return r;
}

// Compute the transition matrix t and the new zeta after 30 divsteps. Constant-time
// (branchless) — direct port of modinv32_divsteps_30.
__device__ int32_t mi_divsteps_30(int32_t zeta, uint32_t f0, uint32_t g0, mi_trans2x2 *t) {
    uint32_t u = 1, v = 0, q = 0, r = 1;
    uint32_t c1, c2, mask1, mask2, f = f0, g = g0, x, y, z;
    #pragma unroll
    for (int i = 0; i < 30; ++i) {
        c1 = (uint32_t)(zeta >> 31);   // -1 if zeta<0 else 0
        mask1 = c1;
        c2 = g & 1;
        mask2 = -c2;                   // -1 if g odd else 0
        x = (f ^ mask1) - mask1;       // conditionally negate f,u,v (if zeta<0)
        y = (u ^ mask1) - mask1;
        z = (v ^ mask1) - mask1;
        g += x & mask2;                // if g odd: g += ±f, q += ±u, r += ±v
        q += y & mask2;
        r += z & mask2;
        mask1 &= mask2;                // (zeta<0) && (g odd)
        zeta = (zeta ^ (int32_t)mask1) - 1;
        f += g & mask1;                // conditional swap fold
        u += q & mask1;
        v += r & mask1;
        g >>= 1;
        u <<= 1;
        v <<= 1;
    }
    t->u = (int32_t)u; t->v = (int32_t)v; t->q = (int32_t)q; t->r = (int32_t)r;
    return zeta;
}

// (t/2^30) · [d,e] mod p. d,e in (-2p,p) on input/output; limbs in (-2^30,2^30).
__device__ void mi_update_de_30(int32_t d[9], int32_t e[9], const mi_trans2x2 *t) {
    const int32_t M30 = MI_M30;
    const int32_t u = t->u, v = t->v, q = t->q, r = t->r;
    int32_t di, ei, md, me, sd, se;
    int64_t cd, ce;
    sd = d[8] >> 31;
    se = e[8] >> 31;
    md = (u & sd) + (v & se);
    me = (q & sd) + (r & se);
    di = d[0]; ei = e[0];
    cd = (int64_t)u * di + (int64_t)v * ei;
    ce = (int64_t)q * di + (int64_t)r * ei;
    md -= (MI_MOD_INV30 * (uint32_t)cd + md) & M30;
    me -= (MI_MOD_INV30 * (uint32_t)ce + me) & M30;
    cd += (int64_t)MI_MOD[0] * md;
    ce += (int64_t)MI_MOD[0] * me;
    cd >>= 30;
    ce >>= 30;
    #pragma unroll
    for (int i = 1; i < 9; ++i) {
        di = d[i]; ei = e[i];
        cd += (int64_t)u * di + (int64_t)v * ei;
        ce += (int64_t)q * di + (int64_t)r * ei;
        cd += (int64_t)MI_MOD[i] * md;
        ce += (int64_t)MI_MOD[i] * me;
        d[i - 1] = (int32_t)cd & M30; cd >>= 30;
        e[i - 1] = (int32_t)ce & M30; ce >>= 30;
    }
    d[8] = (int32_t)cd;
    e[8] = (int32_t)ce;
}

// (t/2^30) · [f,g]. f,g in (-p,p].
__device__ void mi_update_fg_30(int32_t f[9], int32_t g[9], const mi_trans2x2 *t) {
    const int32_t M30 = MI_M30;
    const int32_t u = t->u, v = t->v, q = t->q, r = t->r;
    int32_t fi, gi;
    int64_t cf, cg;
    fi = f[0]; gi = g[0];
    cf = (int64_t)u * fi + (int64_t)v * gi;
    cg = (int64_t)q * fi + (int64_t)r * gi;
    cf >>= 30;
    cg >>= 30;
    #pragma unroll
    for (int i = 1; i < 9; ++i) {
        fi = f[i]; gi = g[i];
        cf += (int64_t)u * fi + (int64_t)v * gi;
        cg += (int64_t)q * fi + (int64_t)r * gi;
        f[i - 1] = (int32_t)cf & M30; cf >>= 30;
        g[i - 1] = (int32_t)cg & M30; cg >>= 30;
    }
    f[8] = (int32_t)cf;
    g[8] = (int32_t)cg;
}

// Bring r from (-2p,p) into [0,p); negate it first if sign<0. Port of modinv32_normalize_30.
__device__ void mi_normalize_30(int32_t r[9], int32_t sign) {
    const int32_t M30 = MI_M30;
    int32_t cond_add, cond_negate;
    cond_add = r[8] >> 31;
    #pragma unroll
    for (int i = 0; i < 9; ++i) r[i] += MI_MOD[i] & cond_add;
    cond_negate = sign >> 31;
    #pragma unroll
    for (int i = 0; i < 9; ++i) r[i] = (r[i] ^ cond_negate) - cond_negate;
    #pragma unroll
    for (int i = 1; i < 9; ++i) { r[i] += r[i-1] >> 30; r[i-1] &= M30; }
    cond_add = r[8] >> 31;
    #pragma unroll
    for (int i = 0; i < 9; ++i) r[i] += MI_MOD[i] & cond_add;
    #pragma unroll
    for (int i = 1; i < 9; ++i) { r[i] += r[i-1] >> 30; r[i-1] &= M30; }
}

// Extended Euclidean / Fermat: a^(p-2) mod p
__device__ uint256 fp_inv(const uint256 &a) {
#if defined(FP_INV_FAKE)
    // [DIVSTEP Phase-0 ceiling spike] TIMING-ONLY, INCORRECT result. Models a constant-cost
    // (GRP-independent) divstep inverse as FP_INV_FAKE field-squares so a GRP sweep can bound the
    // achievable speedup before the real safegcd inverse is written. FP_INV_FAKE=0 ≈ free (upper
    // bound); ≈30 ≈ realistic divstep. NEVER ship — gives wrong keys. See KANGAROO_DIVSTEP_PLAN.md.
    uint256 r = a;
    #pragma unroll 1
    for (int i = 0; i < (FP_INV_FAKE); i++) r = fp_sqr(r);
    return r;
#elif defined(FP_INV_FERMAT)
    // Reference oracle (a^(p-2) mod p) — kept behind -DFP_INV_FERMAT to cross-check
    // the divstep path. ~384 muls/call; the small-GRP-blocking cost we replaced.
    uint32_t exp[8] = {
        0xFFFFFC2D, 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFF,
        0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF
    };
    uint256 r; r.v[0]=1; for(int i=1;i<8;i++) r.v[i]=0;
    uint256 base = a;
    for (int w = 0; w < 8; w++) {
        for (int bit = 0; bit < 32; bit++) {
            if ((exp[w] >> bit) & 1) r = fp_mul(r, base);
            base = fp_sqr(base);
        }
    }
    return r;
#else
    // Default: Bernstein–Yang safegcd inverse (divstep). d=0, e=1, f=p, g=a, zeta=-1;
    // 20 iterations × 30 divsteps = 600 (≥590 needed for 256-bit). d ends as ±inv(a).
    int32_t d[9] = {0,0,0,0,0,0,0,0,0};
    int32_t e[9] = {1,0,0,0,0,0,0,0,0};
    int32_t f[9], g[9];
    #pragma unroll
    for (int i = 0; i < 9; i++) f[i] = MI_MOD[i];
    mi_to_signed30(g, a);
    int32_t zeta = -1;
    #pragma unroll 1
    for (int it = 0; it < 20; ++it) {
        mi_trans2x2 t;
        zeta = mi_divsteps_30(zeta, (uint32_t)f[0], (uint32_t)g[0], &t);
#if defined(FP_INV_FG_FIRST)
        // [D2 Phase 2] Correctness-preserving reorder test: mi_update_de_30/mi_update_fg_30 each
        // read only the already-computed t and write disjoint state (d,e vs f,g), so swapping
        // their call order changes no output value, only ptxas's scheduling freedom. g[0]/f[0]
        // (from fg_30) gate the next iteration's mi_divsteps_30 call above; d/e (from de_30) are
        // only consumed after the whole 20-iteration loop exits. See
        // doc/KANGAROO_RCK_V4_UPGRADE_PLAN.md D2 Phase 2 for the experiment this knob drives.
        mi_update_fg_30(f, g, &t);
        mi_update_de_30(d, e, &t);
#else
        mi_update_de_30(d, e, &t);
        mi_update_fg_30(f, g, &t);
#endif
    }
    // f is now ±1 (= ±gcd); normalize d (negating if f<0) to [0,p).
    mi_normalize_30(d, f[8]);
    return mi_from_signed30(d);
#endif
}

// ════════════════════════════════════════════════════════════════════════════
// [LEVER X Phase 4b] Native u64[4] field layer — held in registers through KernelA64's hot path so
// there is NO per-op LE32↔LE64 repack (the tax that capped the Phase-4a probe at +5.9%). A field
// element is `uint64_t[4]` little-endian (v[0]=LSW). add/sub mirror the proven 32-bit fp_add/fp_sub
// fold (lever E); mul/sqr = bc_mulModP_64 (lever J, validated); inv reuses the divstep fp_inv with a
// single boundary repack (called once per GRP via batch inversion ⇒ amortized). Reduction constant
// C = 2²⁵⁶−p = SECP_C64; p = BC_P64.
// ════════════════════════════════════════════════════════════════════════════
__device__ static inline bool fe_is_zero(const uint64_t a[4]) {
    return (a[0] | a[1] | a[2] | a[3]) == 0ULL;
}
// r = (a + b) mod p.  s=a+b (carry); t=s+C (carry2); r = (carry|carry2) ? t : s  (see fp_add).
__device__ static void fe_add(const uint64_t a[4], const uint64_t b[4], uint64_t r[4]) {
    uint64_t s0=a[0],s1=a[1],s2=a[2],s3=a[3],cr;
    asm volatile("add.cc.u64 %0,%0,%5; addc.cc.u64 %1,%1,%6; addc.cc.u64 %2,%2,%7;"
                 "addc.cc.u64 %3,%3,%8; addc.u64 %4,0,0;\n\t"
        : "+&l"(s0),"+&l"(s1),"+&l"(s2),"+&l"(s3),"=&l"(cr)
        : "l"(b[0]),"l"(b[1]),"l"(b[2]),"l"(b[3]));
    uint64_t t0,t1,t2,t3,cr2; const uint64_t Cv=SECP_C64;
    asm volatile("add.cc.u64 %0,%5,%9; addc.cc.u64 %1,%6,0; addc.cc.u64 %2,%7,0;"
                 "addc.cc.u64 %3,%8,0; addc.u64 %4,0,0;\n\t"
        : "=&l"(t0),"=&l"(t1),"=&l"(t2),"=&l"(t3),"=&l"(cr2)
        : "l"(s0),"l"(s1),"l"(s2),"l"(s3),"l"(Cv));
    uint64_t use = cr | cr2;
    r[0]=use?t0:s0; r[1]=use?t1:s1; r[2]=use?t2:s2; r[3]=use?t3:s3;
}
// r = (a − b) mod p.  d=a−b (borrow); if borrow d −= C  (= +p mod 2²⁵⁶)  (see fp_sub).
__device__ static void fe_sub(const uint64_t a[4], const uint64_t b[4], uint64_t r[4]) {
    uint64_t d0=a[0],d1=a[1],d2=a[2],d3=a[3],br;
    asm volatile("sub.cc.u64 %0,%0,%5; subc.cc.u64 %1,%1,%6; subc.cc.u64 %2,%2,%7;"
                 "subc.cc.u64 %3,%3,%8; subc.u64 %4,0,0;\n\t"
        : "+&l"(d0),"+&l"(d1),"+&l"(d2),"+&l"(d3),"=&l"(br)
        : "l"(b[0]),"l"(b[1]),"l"(b[2]),"l"(b[3]));
    uint64_t clo = (br & 1ULL) ? SECP_C64 : 0ULL;
    asm volatile("sub.cc.u64 %0,%0,%4; subc.cc.u64 %1,%1,0; subc.cc.u64 %2,%2,0; subc.u64 %3,%3,0;\n\t"
        : "+&l"(d0),"+&l"(d1),"+&l"(d2),"+&l"(d3)
        : "l"(clo));
    r[0]=d0; r[1]=d1; r[2]=d2; r[3]=d3;
}
__device__ static inline void fe_mul(const uint64_t a[4], const uint64_t b[4], uint64_t r[4]) {
    bc_mulModP_64(a, b, r);
}
__device__ static inline void fe_sqr(const uint64_t a[4], uint64_t r[4]) {
    bc_mulModP_64(a, a, r);
}
// r = a⁻¹ mod p.  Reuse the divstep fp_inv (uint256) with one LE64↔LE32 repack at the boundary;
// called once per GRP in the batch inversion ⇒ the repack is amortized over GRP kangaroos.
__device__ static void fe_inv(const uint64_t a[4], uint64_t r[4]) {
    uint256 A;
    #pragma unroll
    for (int i = 0; i < 4; i++) { A.v[2*i] = (uint32_t)a[i]; A.v[2*i+1] = (uint32_t)(a[i] >> 32); }
    uint256 R = fp_inv(A);
    #pragma unroll
    for (int i = 0; i < 4; i++) r[i] = ((uint64_t)R.v[2*i+1] << 32) | R.v[2*i];
}

// ── EC point (Jacobian coordinates) ────────────────────────────────────────

typedef struct { uint256 x, y, z; bool inf; } JacPoint;

__device__ JacPoint jac_infinity() {
    JacPoint p; p.inf = true;
    memset(&p.x, 0, sizeof(uint256));
    memset(&p.y, 0, sizeof(uint256));
    memset(&p.z, 0, sizeof(uint256));
    return p;
}

__device__ JacPoint jac_double(const JacPoint &P) {
    if (P.inf) return P;
    uint256 c4; memset(&c4, 0, sizeof(c4)); c4.v[0] = 4;
    uint256 c8; memset(&c8, 0, sizeof(c8)); c8.v[0] = 8;

    uint256 Y2 = fp_sqr(P.y);
    uint256 S  = fp_mul(fp_mul(c4, P.x), Y2);   // 4*X*Y²
    uint256 X2 = fp_sqr(P.x);
    uint256 M  = fp_add(fp_add(X2, X2), X2);     // 3*X² (a=0 for secp256k1)
    uint256 X3 = fp_sub(fp_sqr(M), fp_add(S, S));
    uint256 Y3 = fp_sub(fp_mul(M, fp_sub(S, X3)), fp_mul(c8, fp_sqr(Y2)));
    uint256 Z3 = fp_mul(fp_add(P.y, P.y), P.z);
    JacPoint R; R.inf = false; R.x = X3; R.y = Y3; R.z = Z3;
    return R;
}

__device__ JacPoint jac_add(const JacPoint &P, const JacPoint &Q) {
    if (P.inf) return Q;
    if (Q.inf) return P;

    uint256 Z1Z1 = fp_sqr(P.z);
    uint256 Z2Z2 = fp_sqr(Q.z);
    uint256 U1   = fp_mul(P.x, Z2Z2);
    uint256 U2   = fp_mul(Q.x, Z1Z1);
    uint256 S1   = fp_mul(fp_mul(P.y, Q.z), Z2Z2);
    uint256 S2   = fp_mul(fp_mul(Q.y, P.z), Z1Z1);
    uint256 H    = fp_sub(U2, U1);
    uint256 R    = fp_sub(S2, S1);

    if (u256_is_zero(H)) {
        if (u256_is_zero(R)) return jac_double(P);
        return jac_infinity();
    }

    uint256 c2; memset(&c2, 0, sizeof(c2)); c2.v[0] = 2;
    uint256 c4; memset(&c4, 0, sizeof(c4)); c4.v[0] = 4;

    uint256 H2   = fp_sqr(H);
    uint256 H3   = fp_mul(H, H2);
    uint256 X3   = fp_sub(fp_sub(fp_sqr(R), H3), fp_mul(fp_mul(c2, U1), H2));
    uint256 Y3   = fp_sub(fp_mul(R, fp_sub(fp_mul(U1, H2), X3)), fp_mul(S1, H3));
    uint256 Z3   = fp_mul(fp_mul(H, P.z), Q.z);

    JacPoint Out; Out.inf = false; Out.x = X3; Out.y = Y3; Out.z = Z3;
    return Out;
}

// ── Optimized G-addition (exploits G.z = 1) ────────────────────────────────

// Add G to an affine point (P.z = G.z = 1).
// Eliminates all Z1Z1/Z2Z2 multiplications; result Z3 = H.
// Cost: 8 fp_mul  (vs 18 for general jac_add)
__device__ JacPoint jac_add_G_from_affine(const uint256 &ax, const uint256 &ay) {
    uint256 Gx, Gy;
    for (int i = 0; i < 8; i++) { Gx.v[i] = GX[i]; Gy.v[i] = GY[i]; }

    uint256 H = fp_sub(Gx, ax);
    uint256 R = fp_sub(Gy, ay);

    if (u256_is_zero(H)) {
        if (u256_is_zero(R)) {
            // ax == Gx and ay == Gy  →  P == G, return 2G
            JacPoint tmp; tmp.inf = false; tmp.x = ax; tmp.y = ay;
            tmp.z.v[0] = 1; for (int i = 1; i < 8; i++) tmp.z.v[i] = 0;
            return jac_double(tmp);
        }
        return jac_infinity(); // P == -G
    }

    uint256 c2; memset(&c2, 0, sizeof(c2)); c2.v[0] = 2;
    uint256 H2 = fp_sqr(H);
    uint256 H3 = fp_mul(H, H2);
    uint256 X3 = fp_sub(fp_sub(fp_sqr(R), H3), fp_mul(fp_mul(c2, ax), H2));
    uint256 Y3 = fp_sub(fp_mul(R, fp_sub(fp_mul(ax, H2), X3)), fp_mul(ay, H3));
    JacPoint Out; Out.inf = false; Out.x = X3; Out.y = Y3; Out.z = H;
    return Out;
}

// Add G to a Jacobian point P (G.z = 1).
// Eliminates Z2Z2 and related terms; Z3 = H * P.z.
// Cost: 13 fp_mul  (vs 18 for general jac_add)
__device__ JacPoint jac_add_G(const JacPoint &P) {
    uint256 Gx, Gy;
    for (int i = 0; i < 8; i++) { Gx.v[i] = GX[i]; Gy.v[i] = GY[i]; }

    uint256 Z1Z1 = fp_sqr(P.z);
    uint256 U2   = fp_mul(Gx, Z1Z1);               // Gx * Z1²
    uint256 S2   = fp_mul(fp_mul(Gy, P.z), Z1Z1);  // Gy * Z1³
    // U1 = P.x, S1 = P.y  (Z2 = 1, so Z2Z2 = 1)

    uint256 H = fp_sub(U2, P.x);
    uint256 R = fp_sub(S2, P.y);

    if (u256_is_zero(H)) {
        if (u256_is_zero(R)) return jac_double(P);
        return jac_infinity();
    }

    uint256 c2; memset(&c2, 0, sizeof(c2)); c2.v[0] = 2;
    uint256 H2 = fp_sqr(H);
    uint256 H3 = fp_mul(H, H2);
    uint256 X3 = fp_sub(fp_sub(fp_sqr(R), H3), fp_mul(fp_mul(c2, P.x), H2));
    uint256 Y3 = fp_sub(fp_mul(R, fp_sub(fp_mul(P.x, H2), X3)), fp_mul(P.y, H3));
    uint256 Z3 = fp_mul(H, P.z);                   // H * P.z * G.z = H * P.z

    JacPoint Out; Out.inf = false; Out.x = X3; Out.y = Y3; Out.z = Z3;
    return Out;
}

// Add affine point (qx, qy, z=1) to Jacobian P.
// Generalisation of jac_add_G for any precomputed table entry.
// Cost: 13 fp_mul  (same as jac_add_G, vs 18 for general jac_add)
__device__ JacPoint jac_add_affine(const JacPoint &P, const uint256 &qx, const uint256 &qy) {
    if (P.inf) {
        JacPoint Q; Q.inf = false; Q.x = qx; Q.y = qy;
        Q.z.v[0] = 1; for (int i = 1; i < 8; i++) Q.z.v[i] = 0;
        return Q;
    }
    uint256 Z1Z1 = fp_sqr(P.z);
    uint256 U2   = fp_mul(qx, Z1Z1);
    uint256 S2   = fp_mul(fp_mul(qy, P.z), Z1Z1);
    uint256 H    = fp_sub(U2, P.x);
    uint256 R    = fp_sub(S2, P.y);

    if (u256_is_zero(H)) {
        if (u256_is_zero(R)) return jac_double(P);
        return jac_infinity();
    }

    uint256 c2; memset(&c2, 0, sizeof(c2)); c2.v[0] = 2;
    uint256 H2 = fp_sqr(H);
    uint256 H3 = fp_mul(H, H2);
    uint256 X3 = fp_sub(fp_sub(fp_sqr(R), H3), fp_mul(fp_mul(c2, P.x), H2));
    uint256 Y3 = fp_sub(fp_mul(R, fp_sub(fp_mul(P.x, H2), X3)), fp_mul(P.y, H3));
    uint256 Z3 = fp_mul(H, P.z);
    JacPoint Out; Out.inf = false; Out.x = X3; Out.y = Y3; Out.z = Z3;
    return Out;
}

// scalar × G using precomputed table: GTABLE_X[i]/GTABLE_Y[i] = 2^i × G (affine).
//
// Algorithm: binary method — for each bit i of k32, if the bit is set add T[i].
// No doublings needed: ~128 expected jac_add_affine calls (13 fp_mul each) vs
// the old double-and-add (256 doublings × 9 + 128 additions × 18 ≈ 4608 fp_mul).
//
// Warp divergence: for consecutive keys (as in secp256k1_batch), bits 5-255 are
// uniform across all 32 threads → only the 5 LSBs diverge → near-zero overhead.
__device__ JacPoint scalar_mul_G(const uint8_t *k32) {
    JacPoint R = jac_infinity();
    // k32 is 32-byte big-endian: bit i (LSB=0) lives in k32[31 - i/8] at position i%8.
    for (int i = 0; i < 256; i++) {
        int byte_idx = 31 - i / 8;
        int bit_pos  = i % 8;
        if ((k32[byte_idx] >> bit_pos) & 1) {
            uint256 tx, ty;
            for (int j = 0; j < 8; j++) tx.v[j] = GTABLE_X[i][j];
            for (int j = 0; j < 8; j++) ty.v[j] = GTABLE_Y[i][j];
            R = jac_add_affine(R, tx, ty);
        }
    }
    return R;
}

// Jacobian → affine
__device__ void jac_to_affine(const JacPoint &P, uint256 &ax, uint256 &ay) {
    uint256 zinv  = fp_inv(P.z);
    uint256 zinv2 = fp_sqr(zinv);
    uint256 zinv3 = fp_mul(zinv, zinv2);
    ax = fp_mul(P.x, zinv2);
    ay = fp_mul(P.y, zinv3);
}

// ── Compressed pubkey serialization ────────────────────────────────────────

// Write 33 bytes: 0x02/0x03 prefix + x (big-endian)
__device__ void serialize_pubkey(const uint256 &x, const uint256 &y, uint8_t out[33]) {
    out[0] = (y.v[0] & 1) ? 0x03 : 0x02;
    for (int i = 0; i < 8; i++) {
        int off = 1 + (7 - i) * 4;
        out[off + 0] = (x.v[i] >> 24) & 0xFF;
        out[off + 1] = (x.v[i] >> 16) & 0xFF;
        out[off + 2] = (x.v[i] >>  8) & 0xFF;
        out[off + 3] = (x.v[i] >>  0) & 0xFF;
    }
}

// Write 65 bytes: 0x04 prefix + x (big-endian) + y (big-endian)
__device__ void serialize_pubkey_uncompressed(const uint256 &x, const uint256 &y, uint8_t out[65]) {
    out[0] = 0x04;
    for (int i = 0; i < 8; i++) {
        int off = 1 + (7 - i) * 4;
        out[off + 0] = (x.v[i] >> 24) & 0xFF;
        out[off + 1] = (x.v[i] >> 16) & 0xFF;
        out[off + 2] = (x.v[i] >>  8) & 0xFF;
        out[off + 3] = (x.v[i] >>  0) & 0xFF;
    }
    for (int i = 0; i < 8; i++) {
        int off = 33 + (7 - i) * 4;
        out[off + 0] = (y.v[i] >> 24) & 0xFF;
        out[off + 1] = (y.v[i] >> 16) & 0xFF;
        out[off + 2] = (y.v[i] >>  8) & 0xFF;
        out[off + 3] = (y.v[i] >>  0) & 0xFF;
    }
}

// ── SHA256 ──────────────────────────────────────────────────────────────────

__device__ __constant__ uint32_t SECP_SHA256_K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

#define ROTR32(x,n) (((x) >> (n)) | ((x) << (32-(n))))
#define SHA_CH(e,f,g)  (((e)&(f))^(~(e)&(g)))
#define SHA_MAJ(a,b,c) (((a)&(b))^((a)&(c))^((b)&(c)))
#define SHA_EP0(a) (ROTR32(a,2)^ROTR32(a,13)^ROTR32(a,22))
#define SHA_EP1(e) (ROTR32(e,6)^ROTR32(e,11)^ROTR32(e,25))
#define SHA_SIG0(x) (ROTR32(x,7)^ROTR32(x,18)^((x)>>3))
#define SHA_SIG1(x) (ROTR32(x,17)^ROTR32(x,19)^((x)>>10))

// Process one 512-bit (16 × u32) SHA256 block, updating h[0..7] in-place.
//
// Uses a rolling 16-element message schedule (W[16]) instead of the
// textbook W[64].  W[i % 16] is expanded in-place, reducing the local
// array from 256 bytes to 64 bytes — small enough to stay in registers
// and avoid costly local-memory spills when the function is inlined.
__device__ __forceinline__ void sha256_compress(uint32_t h[8], const uint32_t block[16]) {
    uint32_t W[16];
    for (int i = 0; i < 16; i++) W[i] = block[i];

    uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hv=h[7];

    // Rounds 0-15: W[] is the raw message block.
    for (int i = 0; i < 16; i++) {
        uint32_t t1 = hv + SHA_EP1(e) + SHA_CH(e,f,g) + SECP_SHA256_K[i] + W[i];
        uint32_t t2 = SHA_EP0(a) + SHA_MAJ(a,b,c);
        hv=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }

    // Rounds 16-63: expand W in-place, then consume.
    // W[j] = σ1(W[(i-2)&15]) + W[(i-7)&15] + σ0(W[(i-15)&15]) + W[j]
    for (int i = 16; i < 64; i++) {
        int j = i & 15;
        W[j] = SHA_SIG1(W[(i-2)&15]) + W[(i-7)&15] + SHA_SIG0(W[(i-15)&15]) + W[j];
        uint32_t t1 = hv + SHA_EP1(e) + SHA_CH(e,f,g) + SECP_SHA256_K[i] + W[j];
        uint32_t t2 = SHA_EP0(a) + SHA_MAJ(a,b,c);
        hv=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }

    h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d;
    h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=hv;
}

// Single-block SHA256 of exactly 33 bytes (compressed pubkey).
// Uses W[64] with separate expand + round loops so NVCC can unroll both with
// compile-time-constant indices — giving maximum register-level optimization.
__device__ void sha256_33(const uint8_t in[33], uint8_t out[32]) {
    uint32_t W[64];
    // First 8 words from input (33 bytes = 8 full words + 1 byte)
    for (int i = 0; i < 8; i++) {
        int b = i * 4;
        W[i] = ((uint32_t)in[b] << 24) | ((uint32_t)in[b+1] << 16) |
               ((uint32_t)in[b+2] << 8) | in[b+3];
    }
    // 9th word: 1 byte of data + 0x80 padding + zeros
    W[8] = ((uint32_t)in[32] << 24) | 0x00800000;
    // Pad to 14 words of zeros
    for (int i = 9; i < 14; i++) W[i] = 0;
    // Length in bits = 33 * 8 = 264
    W[14] = 0;
    W[15] = 264;

    // Expand
    for (int i = 16; i < 64; i++)
        W[i] = SHA_SIG1(W[i-2]) + W[i-7] + SHA_SIG0(W[i-15]) + W[i-16];

    uint32_t h[8] = {
        0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
        0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19
    };

    for (int i = 0; i < 64; i++) {
        uint32_t t1 = h[7] + SHA_EP1(h[4]) + SHA_CH(h[4],h[5],h[6]) + SECP_SHA256_K[i] + W[i];
        uint32_t t2 = SHA_EP0(h[0]) + SHA_MAJ(h[0],h[1],h[2]);
        h[7]=h[6]; h[6]=h[5]; h[5]=h[4]; h[4]=h[3]+t1;
        h[3]=h[2]; h[2]=h[1]; h[1]=h[0]; h[0]=t1+t2;
    }

    h[0]+=0x6a09e667; h[1]+=0xbb67ae85; h[2]+=0x3c6ef372; h[3]+=0xa54ff53a;
    h[4]+=0x510e527f; h[5]+=0x9b05688c; h[6]+=0x1f83d9ab; h[7]+=0x5be0cd19;

    for (int i = 0; i < 8; i++) {
        out[i*4+0] = (h[i] >> 24) & 0xFF;
        out[i*4+1] = (h[i] >> 16) & 0xFF;
        out[i*4+2] = (h[i] >>  8) & 0xFF;
        out[i*4+3] = (h[i] >>  0) & 0xFF;
    }
}

// Two-block SHA256 of exactly 65 bytes (uncompressed pubkey: 0x04 || x || y)
// Block 1: bytes  0-63  (full 512-bit block, no padding)
// Block 2: byte  64 + 0x80 pad + zeros + length (65*8 = 520 bits)
__device__ void sha256_65(const uint8_t in[65], uint8_t out[32]) {
    uint32_t h[8] = {
        0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
        0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u
    };
    uint32_t block[16];

    // Block 1: bytes 0-63
    for (int i = 0; i < 16; i++) {
        int b = i * 4;
        block[i] = ((uint32_t)in[b]   << 24) | ((uint32_t)in[b+1] << 16)
                 | ((uint32_t)in[b+2] <<  8) |  (uint32_t)in[b+3];
    }
    sha256_compress(h, block);

    // Block 2: last data byte (in[64]) + 0x80 bit + zeros + 64-bit length
    block[0] = ((uint32_t)in[64] << 24) | 0x00800000u;
    for (int i = 1; i < 14; i++) block[i] = 0;
    block[14] = 0;
    block[15] = 520u; // 65 * 8
    sha256_compress(h, block);

    for (int i = 0; i < 8; i++) {
        out[i*4+0] = (h[i] >> 24) & 0xFF;
        out[i*4+1] = (h[i] >> 16) & 0xFF;
        out[i*4+2] = (h[i] >>  8) & 0xFF;
        out[i*4+3] = (h[i] >>  0) & 0xFF;
    }
}

// ── RIPEMD-160 ──────────────────────────────────────────────────────────────

#define ROTL32(x,n) (((x)<<(n))|((x)>>(32-(n))))

__device__ uint32_t rmd_f(int j, uint32_t x, uint32_t y, uint32_t z) {
    if      (j < 16) return x ^ y ^ z;
    else if (j < 32) return (x & y) | (~x & z);
    else if (j < 48) return (x | ~y) ^ z;
    else if (j < 64) return (x & z) | (y & ~z);
    else             return x ^ (y | ~z);
}

__device__ __constant__ uint32_t RMD_KL[5] = {0x00000000,0x5A827999,0x6ED9EBA1,0x8F1BBCDC,0xA953FD4E};
__device__ __constant__ uint32_t RMD_KR[5] = {0x50A28BE6,0x5C4DD124,0x6D703EF3,0x7A6D76E9,0x00000000};

__device__ __constant__ uint8_t RMD_RL[80] = {
    0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
    7,4,13,1,10,6,15,3,12,0,9,5,2,14,11,8,
    3,10,14,4,9,15,8,1,2,7,0,6,13,11,5,12,
    1,9,11,10,0,8,12,4,13,3,7,15,14,5,6,2,
    4,0,5,9,7,12,2,10,14,1,3,8,11,6,15,13
};
__device__ __constant__ uint8_t RMD_RR[80] = {
    5,14,7,0,9,2,11,4,13,6,15,8,1,10,3,12,
    6,11,3,7,0,13,5,10,14,15,8,12,4,9,1,2,
    15,5,1,3,7,14,6,9,11,8,12,2,10,0,4,13,
    8,6,4,1,3,11,15,0,5,12,2,13,9,7,10,14,
    12,15,10,4,1,5,8,7,6,2,13,14,0,3,9,11
};
__device__ __constant__ uint8_t RMD_SL[80] = {
    11,14,15,12,5,8,7,9,11,13,14,15,6,7,9,8,
    7,6,8,13,11,9,7,15,7,12,15,9,11,7,13,12,
    11,13,6,7,14,9,13,15,14,8,13,6,5,12,7,5,
    11,12,14,15,14,15,9,8,9,14,5,6,8,6,5,12,
    9,15,5,11,6,8,13,12,5,12,13,14,11,8,5,6
};
__device__ __constant__ uint8_t RMD_SR[80] = {
    8,9,9,11,13,15,15,5,7,7,8,11,14,14,12,6,
    9,13,15,7,12,8,9,11,7,7,12,7,6,15,13,11,
    9,7,15,11,8,6,6,14,12,13,5,14,13,13,7,5,
    15,5,8,11,14,14,6,14,6,9,12,9,12,5,15,8,
    8,5,12,9,12,5,14,6,8,13,6,5,15,13,11,11
};

// RIPEMD-160 of 32 bytes (SHA256 output)
__device__ void ripemd160_32(const uint8_t in[32], uint8_t out[20]) {
    uint32_t X[16];
    // 32 bytes of data + 0x80 + zeros + length
    for (int i = 0; i < 8; i++)
        X[i] = ((uint32_t)in[i*4]) | ((uint32_t)in[i*4+1]<<8) |
               ((uint32_t)in[i*4+2]<<16) | ((uint32_t)in[i*4+3]<<24);
    X[8]  = 0x00000080;
    for (int i = 9; i < 14; i++) X[i] = 0;
    X[14] = 256; // 32 bytes * 8 bits
    X[15] = 0;

    uint32_t al=0x67452301, bl=0xEFCDAB89, cl=0x98BADCFE, dl=0x10325476, el=0xC3D2E1F0;
    uint32_t ar=al, br=bl, cr=cl, dr=dl, er=el;

    for (int j = 0; j < 80; j++) {
        int round = j / 16;
        uint32_t tl = ROTL32(al + rmd_f(j, bl, cl, dl) + X[RMD_RL[j]] + RMD_KL[round], RMD_SL[j]) + el;
        al=el; el=dl; dl=ROTL32(cl,10); cl=bl; bl=tl;
        uint32_t tr = ROTL32(ar + rmd_f(79-j, br, cr, dr) + X[RMD_RR[j]] + RMD_KR[round], RMD_SR[j]) + er;
        ar=er; er=dr; dr=ROTL32(cr,10); cr=br; br=tr;
    }

    uint32_t h[5];
    h[0] = 0xEFCDAB89 + cl + dr;  // T = new h0
    h[1] = 0x98BADCFE + dl + er;
    h[2] = 0x10325476 + el + ar;
    h[3] = 0xC3D2E1F0 + al + br;
    h[4] = 0x67452301 + bl + cr;

    for (int i = 0; i < 5; i++) {
        out[i*4+0] = (h[i] >>  0) & 0xFF;
        out[i*4+1] = (h[i] >>  8) & 0xFF;
        out[i*4+2] = (h[i] >> 16) & 0xFF;
        out[i*4+3] = (h[i] >> 24) & 0xFF;
    }
}

// ── Main kernel ─────────────────────────────────────────────────────────────

// Mini-batch size for the stride loop.
// Each outer iteration hashes SB consecutive keys using one batch fp_inv
// instead of SB individual fp_inv calls.
// Must divide STRIDE (1024 / 512 = 2).
#define SB 512

/*
 * Each thread handles `stride` consecutive keys starting at:
 *   key = range_start + (blockIdx.x * blockDim.x + threadIdx.x) * stride
 *
 * Output: hash160_out[thread_global_id * stride + step] = 20 bytes
 *
 * Caller (Rust) provides:
 *   range_start_lo / range_start_hi — 128-bit start key split into two u64s
 *   total_keys                      — how many keys this batch covers
 *   stride                          — keys per thread
 *   hash160_out                     — device buffer, 20 * total_keys bytes
 */
/*
 * gtable_init — one-shot setup kernel that populates GTABLE_X / GTABLE_Y.
 *
 * Launch with grid=(1,1,1), block=(256,1,1).
 * Each thread i copies 8 u32 words of src_x/src_y into GTABLE_X[i]/GTABLE_Y[i].
 * Called once from Rust (GpuScanner::new) before any scalar_mul_G kernel.
 */
__device__ uint32_t murmur3_x86_32_20(const uint8_t data[20], uint32_t seed) {
    const uint32_t c1 = 0xcc9e2d51u;
    const uint32_t c2 = 0x1b873593u;
    uint32_t h = seed;

    for (int i = 0; i < 5; i++) {
        uint32_t k = (uint32_t)data[i*4+0]
                   | ((uint32_t)data[i*4+1] <<  8)
                   | ((uint32_t)data[i*4+2] << 16)
                   | ((uint32_t)data[i*4+3] << 24);
        k *= c1;
        k = (k << 15) | (k >> 17);
        k *= c2;
        h ^= k;
        h = (h << 13) | (h >> 19);
        h = h * 5u + 0xe6546b64u;
    }

    // No remainder for 20-byte input.
    h ^= 20u;
    h ^= h >> 16; h *= 0x85ebca6bu;
    h ^= h >> 13; h *= 0xc2b2ae35u;
    h ^= h >> 16;
    return h;
}

// Returns true if hash160 is (possibly) in the bloom filter.
// bloom_bits: flat u64 array; bloom_m: total bits; bloom_k: hash count.
__device__ bool bloom_check(
    const uint64_t * __restrict__ bloom_bits,
    uint64_t bloom_m,
    uint32_t bloom_k,
    const uint8_t hash160[20]
) {
    const uint32_t SEED = 0x9747b28cu;
    uint32_t h1 = murmur3_x86_32_20(hash160, SEED);
    uint32_t h2 = murmur3_x86_32_20(hash160, h1);
    for (uint32_t i = 0; i < bloom_k; i++) {
        uint64_t bit = ((uint64_t)h1 + (uint64_t)i * (uint64_t)h2) % bloom_m;
        if (!((bloom_bits[bit >> 6] >> (bit & 63u)) & 1ULL)) return false;
    }
    return true;
}

/*
 * gtable_init — populates the precomputed G-table required by scalar_mul_G.
 * Launch with grid=(1,1,1), block=(256,1,1), once per module before any
 * scalar_mul_G call in that module (GTABLE_X/GTABLE_Y are per-compilation-
 * unit __device__ globals -- each .cu file including this header needs its
 * own gtable_init call, since they don't share device memory).
 */
extern "C" __global__ void gtable_init(
    const uint32_t * __restrict__ src_x,   // 256 × 8 u32s: x-coords of 2^i × G
    const uint32_t * __restrict__ src_y    // 256 × 8 u32s: y-coords of 2^i × G
) {
    int i = threadIdx.x;
    if (i >= 256) return;
    for (int j = 0; j < 8; j++) {
        GTABLE_X[i][j] = src_x[i * 8 + j];
        GTABLE_Y[i][j] = src_y[i * 8 + j];
    }
}

// Combined helper: raw 32-byte private key -> both compressed and
// uncompressed hash160. Used by secp256k1_brainwallet_both and
// aes_kdf_oracle.cu's stream-mode Bloom check.
__device__ void derive_hash160_both(const uint8_t privkey[32], uint8_t out_compressed[20], uint8_t out_uncompressed[20]) {
    JacPoint P = scalar_mul_G(privkey);
    uint256 ax, ay;
    jac_to_affine(P, ax, ay);

    {
        uint8_t pubkey[33];
        serialize_pubkey(ax, ay, pubkey);
        uint8_t sha_out[32];
        sha256_33(pubkey, sha_out);
        ripemd160_32(sha_out, out_compressed);
    }
    {
        uint8_t pubkey[65];
        serialize_pubkey_uncompressed(ax, ay, pubkey);
        uint8_t sha_out[32];
        sha256_65(pubkey, sha_out);
        ripemd160_32(sha_out, out_uncompressed);
    }
}
