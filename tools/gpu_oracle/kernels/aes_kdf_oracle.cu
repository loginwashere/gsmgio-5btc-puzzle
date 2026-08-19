// GSMG.IO puzzle AES/KDF oracle -- CUDA port of tools/gsmg/cb_common.py's
// aes_try_open_bytes() / aes_try_open_ecb_bytes() / aes_try_open_stream_bytes()
// (legacy EVP_BytesToKey + PBKDF2-HMAC-SHA256 KDFs, AES-128/192/256 decrypt
// across CBC/ECB/CFB/OFB/CTR, PKCS7 + printable-z-score gate).
//
// Scope: the AES portion of this project's oracle across 5 chaining modes x
// {legacy-MD5, legacy-SHA1, legacy-SHA256, PBKDF2-SHA256/10000} x
// {128,192,256}-bit keys = 60 variants. 3DES/Blowfish/Camellia/SEED and AES
// Key-Wrap remain out of scope (different cipher algorithms entirely, lower
// historical hit priority per this project's own docs). Every constant/
// threshold here must match cb_common.py bit-for-bit; see selftest.rs /
// cpu_oracle.rs for the cross-check harness that verifies that.

#include <stdint.h>
#include "secp256k1_device.cuh"

// secp256k1_device.cuh's own SHA256_K (round constants for a fixed-size
// pubkey-hashing helper, unrelated to this file's general-purpose
// sha256_transform/sha256_digest below) was renamed SECP_SHA256_K to avoid a
// duplicate-definition error -- the two aren't merged because they have
// different call conventions (word-block vs arbitrary-length byte message)
// and this file's version predates the header; not worth the churn/risk of
// unifying them just to save one small constant table.

// ---------------------------------------------------------------------------
// Fixed sizing. Candidate passphrases (raw form, or the hex digests keystr_forms
// produces) are always well under this in practice -- the 7-fragment creator
// concatenation sweep tops out around 280 bytes.
// ---------------------------------------------------------------------------
#define MAX_CANDIDATE_LEN 512
#define MAX_BLOB_CT_LEN 2432   // PHASE32_SELFTEST (2432) > COSMIC (1328, the largest of the 4 tracked blobs)
#define MAX_BLOBS 4
#define MAX_VARIANTS 60        // 4 KDF kinds x 3 key sizes x 5 cipher modes
#define MAX_PLAINTEXT_LEN MAX_BLOB_CT_LEN

#define KDF_LEGACY_MD5 0
#define KDF_LEGACY_SHA1 1
#define KDF_LEGACY_SHA256 2
#define KDF_PBKDF2_SHA256 3

#define CIPHER_CBC 0
#define CIPHER_ECB 1
#define CIPHER_CFB 2
#define CIPHER_OFB 3
#define CIPHER_CTR 4
#define CIPHER_SEED_CBC 5

// ============================================================================
// MD5 (RFC 1321)
// ============================================================================

__device__ __constant__ uint32_t MD5_S[64] = {
    7,12,17,22, 7,12,17,22, 7,12,17,22, 7,12,17,22,
    5, 9,14,20, 5, 9,14,20, 5, 9,14,20, 5, 9,14,20,
    4,11,16,23, 4,11,16,23, 4,11,16,23, 4,11,16,23,
    6,10,15,21, 6,10,15,21, 6,10,15,21, 6,10,15,21
};

__device__ __constant__ uint32_t MD5_K[64] = {
    0xd76aa478,0xe8c7b756,0x242070db,0xc1bdceee,0xf57c0faf,0x4787c62a,0xa8304613,0xfd469501,
    0x698098d8,0x8b44f7af,0xffff5bb1,0x895cd7be,0x6b901122,0xfd987193,0xa679438e,0x49b40821,
    0xf61e2562,0xc040b340,0x265e5a51,0xe9b6c7aa,0xd62f105d,0x02441453,0xd8a1e681,0xe7d3fbc8,
    0x21e1cde6,0xc33707d6,0xf4d50d87,0x455a14ed,0xa9e3e905,0xfcefa3f8,0x676f02d9,0x8d2a4c8a,
    0xfffa3942,0x8771f681,0x6d9d6122,0xfde5380c,0xa4beea44,0x4bdecfa9,0xf6bb4b60,0xbebfbc70,
    0x289b7ec6,0xeaa127fa,0xd4ef3085,0x04881d05,0xd9d4d039,0xe6db99e5,0x1fa27cf8,0xc4ac5665,
    0xf4292244,0x432aff97,0xab9423a7,0xfc93a039,0x655b59c3,0x8f0ccc92,0xffeff47d,0x85845dd1,
    0x6fa87e4f,0xfe2ce6e0,0xa3014314,0x4e0811a1,0xf7537e82,0xbd3af235,0x2ad7d2bb,0xeb86d391
};

__device__ __forceinline__ uint32_t rotl32(uint32_t x, uint32_t c) {
    return (x << c) | (x >> (32 - c));
}

// General-purpose MD5 over an arbitrary-length message (len <= ~600 bytes for
// our use -- EVP_BytesToKey inputs are digest_prev(<=32) + password(<=512) + salt(8)).
__device__ void md5_digest(const uint8_t* msg, uint32_t len, uint8_t out[16]) {
    uint32_t a0 = 0x67452301, b0 = 0xefcdab89, c0 = 0x98badcfe, d0 = 0x10325476;

    uint8_t buf[1024 + 72];
    uint32_t total = len;
    for (uint32_t i = 0; i < len; i++) buf[i] = msg[i];
    buf[total] = 0x80;
    uint32_t pad_to = ((total + 1 + 8 + 63) / 64) * 64;
    for (uint32_t i = total + 1; i < pad_to; i++) buf[i] = 0;
    uint64_t bit_len = (uint64_t)len * 8;
    for (int i = 0; i < 8; i++) buf[pad_to - 8 + i] = (uint8_t)(bit_len >> (8 * i));
    uint32_t nblocks = pad_to / 64;

    for (uint32_t blk = 0; blk < nblocks; blk++) {
        uint32_t M[16];
        for (int i = 0; i < 16; i++) {
            const uint8_t* p = buf + blk * 64 + i * 4;
            M[i] = (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
        }
        uint32_t A = a0, B = b0, C = c0, D = d0;
        for (int i = 0; i < 64; i++) {
            uint32_t F; int g;
            if (i < 16) { F = (B & C) | (~B & D); g = i; }
            else if (i < 32) { F = (D & B) | (~D & C); g = (5 * i + 1) % 16; }
            else if (i < 48) { F = B ^ C ^ D; g = (3 * i + 5) % 16; }
            else { F = C ^ (B | ~D); g = (7 * i) % 16; }
            F = F + A + MD5_K[i] + M[g];
            A = D; D = C; C = B;
            B = B + rotl32(F, MD5_S[i]);
        }
        a0 += A; b0 += B; c0 += C; d0 += D;
    }
    uint32_t st[4] = {a0, b0, c0, d0};
    for (int i = 0; i < 4; i++) {
        out[i * 4 + 0] = (uint8_t)(st[i]);
        out[i * 4 + 1] = (uint8_t)(st[i] >> 8);
        out[i * 4 + 2] = (uint8_t)(st[i] >> 16);
        out[i * 4 + 3] = (uint8_t)(st[i] >> 24);
    }
}

// ============================================================================
// SHA-1 (RFC 3174)
// ============================================================================

__device__ void sha1_digest(const uint8_t* msg, uint32_t len, uint8_t out[20]) {
    uint32_t h0 = 0x67452301, h1 = 0xEFCDAB89, h2 = 0x98BADCFE, h3 = 0x10325476, h4 = 0xC3D2E1F0;

    uint8_t buf[1024 + 72];
    uint32_t total = len;
    for (uint32_t i = 0; i < len; i++) buf[i] = msg[i];
    buf[total] = 0x80;
    uint32_t pad_to = ((total + 1 + 8 + 63) / 64) * 64;
    for (uint32_t i = total + 1; i < pad_to; i++) buf[i] = 0;
    uint64_t bit_len = (uint64_t)len * 8;
    for (int i = 0; i < 8; i++) buf[pad_to - 1 - i] = (uint8_t)(bit_len >> (8 * i));
    uint32_t nblocks = pad_to / 64;

    for (uint32_t blk = 0; blk < nblocks; blk++) {
        uint32_t w[80];
        for (int i = 0; i < 16; i++) {
            const uint8_t* p = buf + blk * 64 + i * 4;
            w[i] = ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | (uint32_t)p[3];
        }
        for (int i = 16; i < 80; i++) {
            w[i] = rotl32(w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16], 1);
        }
        uint32_t a = h0, b = h1, c = h2, d = h3, e = h4;
        for (int i = 0; i < 80; i++) {
            uint32_t f, k;
            if (i < 20) { f = (b & c) | (~b & d); k = 0x5A827999; }
            else if (i < 40) { f = b ^ c ^ d; k = 0x6ED9EBA1; }
            else if (i < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC; }
            else { f = b ^ c ^ d; k = 0xCA62C1D6; }
            uint32_t temp = rotl32(a, 5) + f + e + k + w[i];
            e = d; d = c; c = rotl32(b, 30); b = a; a = temp;
        }
        h0 += a; h1 += b; h2 += c; h3 += d; h4 += e;
    }
    uint32_t st[5] = {h0, h1, h2, h3, h4};
    for (int i = 0; i < 5; i++) {
        out[i*4+0] = (uint8_t)(st[i] >> 24);
        out[i*4+1] = (uint8_t)(st[i] >> 16);
        out[i*4+2] = (uint8_t)(st[i] >> 8);
        out[i*4+3] = (uint8_t)(st[i]);
    }
}

// ============================================================================
// SHA-256 (FIPS 180-4)
// ============================================================================

__device__ __constant__ uint32_t SHA256_K[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

__device__ __forceinline__ uint32_t rotr32(uint32_t x, uint32_t c) {
    return (x >> c) | (x << (32 - c));
}

// State-based core so pbkdf2/hmac can drive it a block at a time without
// re-padding a temporary buffer for every intermediate call.
__device__ void sha256_init(uint32_t h[8]) {
    h[0]=0x6a09e667; h[1]=0xbb67ae85; h[2]=0x3c6ef372; h[3]=0xa54ff53a;
    h[4]=0x510e527f; h[5]=0x9b05688c; h[6]=0x1f83d9ab; h[7]=0x5be0cd19;
}

__device__ void sha256_transform(uint32_t h[8], const uint8_t block[64]) {
    uint32_t w[64];
    for (int i = 0; i < 16; i++) {
        const uint8_t* p = block + i * 4;
        w[i] = ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | (uint32_t)p[3];
    }
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = rotr32(w[i-15], 7) ^ rotr32(w[i-15], 18) ^ (w[i-15] >> 3);
        uint32_t s1 = rotr32(w[i-2], 17) ^ rotr32(w[i-2], 19) ^ (w[i-2] >> 10);
        w[i] = w[i-16] + s0 + w[i-7] + s1;
    }
    uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
    for (int i = 0; i < 64; i++) {
        uint32_t S1 = rotr32(e,6) ^ rotr32(e,11) ^ rotr32(e,25);
        uint32_t ch = (e & f) ^ (~e & g);
        uint32_t temp1 = hh + S1 + ch + SHA256_K[i] + w[i];
        uint32_t S0 = rotr32(a,2) ^ rotr32(a,13) ^ rotr32(a,22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = S0 + maj;
        hh=g; g=f; f=e; e = d + temp1;
        d=c; c=b; b=a; a = temp1 + temp2;
    }
    h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d; h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=hh;
}

__device__ void sha256_digest(const uint8_t* msg, uint32_t len, uint8_t out[32]) {
    uint32_t h[8];
    sha256_init(h);
    uint8_t buf[1024 + 72];
    for (uint32_t i = 0; i < len; i++) buf[i] = msg[i];
    buf[len] = 0x80;
    uint32_t pad_to = ((len + 1 + 8 + 63) / 64) * 64;
    for (uint32_t i = len + 1; i < pad_to; i++) buf[i] = 0;
    uint64_t bit_len = (uint64_t)len * 8;
    for (int i = 0; i < 8; i++) buf[pad_to - 1 - i] = (uint8_t)(bit_len >> (8 * i));
    uint32_t nblocks = pad_to / 64;
    for (uint32_t blk = 0; blk < nblocks; blk++) sha256_transform(h, buf + blk * 64);
    for (int i = 0; i < 8; i++) {
        out[i*4+0]=(uint8_t)(h[i]>>24); out[i*4+1]=(uint8_t)(h[i]>>16);
        out[i*4+2]=(uint8_t)(h[i]>>8);  out[i*4+3]=(uint8_t)(h[i]);
    }
}

// Lowercase hex encode, matching Python's hashlib .hexdigest().
__device__ void hex_encode(const uint8_t* in, uint32_t len, uint8_t* out) {
    const char* digits = "0123456789abcdef";
    for (uint32_t i = 0; i < len; i++) {
        out[i*2] = digits[in[i] >> 4];
        out[i*2+1] = digits[in[i] & 0xF];
    }
}

// ============================================================================
// HMAC-SHA256 (RFC 2104) + PBKDF2-HMAC-SHA256 (RFC 8018), fixed at this
// project's OpenSSL default of 10,000 iterations.
// ============================================================================

#define SHA256_BLOCK 64
#define SHA256_OUT 32
#define PBKDF2_ITERATIONS 10000

__device__ void hmac_sha256(const uint8_t* key, uint32_t key_len,
                             const uint8_t* msg, uint32_t msg_len,
                             uint8_t out[32]) {
    uint8_t k0[SHA256_BLOCK];
    if (key_len > SHA256_BLOCK) {
        uint8_t hashed[32];
        sha256_digest(key, key_len, hashed);
        for (int i = 0; i < 32; i++) k0[i] = hashed[i];
        for (int i = 32; i < SHA256_BLOCK; i++) k0[i] = 0;
    } else {
        for (uint32_t i = 0; i < key_len; i++) k0[i] = key[i];
        for (uint32_t i = key_len; i < SHA256_BLOCK; i++) k0[i] = 0;
    }

    uint8_t ipad[SHA256_BLOCK], opad[SHA256_BLOCK];
    for (int i = 0; i < SHA256_BLOCK; i++) {
        ipad[i] = k0[i] ^ 0x36;
        opad[i] = k0[i] ^ 0x5c;
    }

    // inner = SHA256(ipad || msg)
    uint8_t inner_buf[SHA256_BLOCK + 4 + 32]; // msg here is always salt(<=8)||INT32BE(4) = <=12 bytes for PBKDF2 use
    for (int i = 0; i < SHA256_BLOCK; i++) inner_buf[i] = ipad[i];
    for (uint32_t i = 0; i < msg_len; i++) inner_buf[SHA256_BLOCK + i] = msg[i];
    uint8_t inner_hash[32];
    sha256_digest(inner_buf, SHA256_BLOCK + msg_len, inner_hash);

    // out = SHA256(opad || inner_hash)
    uint8_t outer_buf[SHA256_BLOCK + 32];
    for (int i = 0; i < SHA256_BLOCK; i++) outer_buf[i] = opad[i];
    for (int i = 0; i < 32; i++) outer_buf[SHA256_BLOCK + i] = inner_hash[i];
    sha256_digest(outer_buf, SHA256_BLOCK + 32, out);
}

// HMAC where the *message* can be large (used for the innermost PBKDF2 F()
// calls the message is always tiny -- salt+counter -- but subsequent
// iterations rehash a 32-byte value, still small). Kept separate from the
// general hmac_sha256 above only via the shared sha256_digest primitive.
__device__ void hmac_sha256_smallmsg(const uint8_t* key, uint32_t key_len,
                                      const uint8_t* msg, uint32_t msg_len,
                                      uint8_t out[32]) {
    hmac_sha256(key, key_len, msg, msg_len, out);
}

// PBKDF2-HMAC-SHA256, `out_len` <= 64 (we only ever need up to 32+16=48 bytes
// here). Fixed 10,000 iterations matching OpenSSL's -pbkdf2 default used
// throughout this project (cb_common.pbkdf2_bytes_to_key).
__device__ void pbkdf2_hmac_sha256(const uint8_t* password, uint32_t pass_len,
                                    const uint8_t* salt, uint32_t salt_len,
                                    uint8_t* out, uint32_t out_len) {
    uint32_t nblocks = (out_len + SHA256_OUT - 1) / SHA256_OUT;
    for (uint32_t blk = 1; blk <= nblocks; blk++) {
        uint8_t salt_ctr[16 + 4];
        for (uint32_t i = 0; i < salt_len; i++) salt_ctr[i] = salt[i];
        salt_ctr[salt_len + 0] = (uint8_t)(blk >> 24);
        salt_ctr[salt_len + 1] = (uint8_t)(blk >> 16);
        salt_ctr[salt_len + 2] = (uint8_t)(blk >> 8);
        salt_ctr[salt_len + 3] = (uint8_t)(blk);

        uint8_t u[32];
        hmac_sha256_smallmsg(password, pass_len, salt_ctr, salt_len + 4, u);
        uint8_t t[32];
        for (int i = 0; i < 32; i++) t[i] = u[i];

        for (uint32_t iter = 1; iter < PBKDF2_ITERATIONS; iter++) {
            uint8_t u_next[32];
            hmac_sha256_smallmsg(password, pass_len, u, 32, u_next);
            for (int i = 0; i < 32; i++) { u[i] = u_next[i]; t[i] ^= u[i]; }
        }

        uint32_t offset = (blk - 1) * SHA256_OUT;
        uint32_t chunk = (offset + SHA256_OUT <= out_len) ? SHA256_OUT : (out_len - offset);
        for (uint32_t i = 0; i < chunk; i++) out[offset + i] = t[i];
    }
}

// ============================================================================
// Legacy OpenSSL EVP_BytesToKey (single-round iterated digest, NOT PBKDF2).
// D_1 = H(passwd||salt); D_i = H(D_{i-1}||passwd||salt); concat until enough.
// ============================================================================

__device__ void evp_bytes_to_key(int digest_kind, const uint8_t* passwd, uint32_t passwd_len,
                                  const uint8_t salt[8], uint8_t* out, uint32_t out_len) {
    uint32_t digest_size = (digest_kind == KDF_LEGACY_MD5) ? 16 : (digest_kind == KDF_LEGACY_SHA1) ? 20 : 32;
    uint8_t prev[32];
    uint32_t prev_len = 0;
    uint32_t produced = 0;

    while (produced < out_len) {
        uint8_t buf[32 + MAX_CANDIDATE_LEN + 8];
        uint32_t p = 0;
        for (uint32_t i = 0; i < prev_len; i++) buf[p++] = prev[i];
        for (uint32_t i = 0; i < passwd_len; i++) buf[p++] = passwd[i];
        for (int i = 0; i < 8; i++) buf[p++] = salt[i];

        uint8_t digest[32];
        if (digest_kind == KDF_LEGACY_MD5) md5_digest(buf, p, digest);
        else if (digest_kind == KDF_LEGACY_SHA1) sha1_digest(buf, p, digest);
        else sha256_digest(buf, p, digest);

        for (uint32_t i = 0; i < digest_size; i++) prev[i] = digest[i];
        prev_len = digest_size;

        uint32_t take = (produced + digest_size <= out_len) ? digest_size : (out_len - produced);
        for (uint32_t i = 0; i < take; i++) out[produced + i] = digest[i];
        produced += take;
    }
}

// ============================================================================
// AES-128/192/256 decrypt (FIPS-197 InvCipher), key schedule, CBC chaining.
// ============================================================================

__device__ __constant__ uint8_t AES_SBOX[256] = {
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
};

__device__ __constant__ uint8_t AES_INV_SBOX[256] = {
    0x52,0x09,0x6a,0xd5,0x30,0x36,0xa5,0x38,0xbf,0x40,0xa3,0x9e,0x81,0xf3,0xd7,0xfb,
    0x7c,0xe3,0x39,0x82,0x9b,0x2f,0xff,0x87,0x34,0x8e,0x43,0x44,0xc4,0xde,0xe9,0xcb,
    0x54,0x7b,0x94,0x32,0xa6,0xc2,0x23,0x3d,0xee,0x4c,0x95,0x0b,0x42,0xfa,0xc3,0x4e,
    0x08,0x2e,0xa1,0x66,0x28,0xd9,0x24,0xb2,0x76,0x5b,0xa2,0x49,0x6d,0x8b,0xd1,0x25,
    0x72,0xf8,0xf6,0x64,0x86,0x68,0x98,0x16,0xd4,0xa4,0x5c,0xcc,0x5d,0x65,0xb6,0x92,
    0x6c,0x70,0x48,0x50,0xfd,0xed,0xb9,0xda,0x5e,0x15,0x46,0x57,0xa7,0x8d,0x9d,0x84,
    0x90,0xd8,0xab,0x00,0x8c,0xbc,0xd3,0x0a,0xf7,0xe4,0x58,0x05,0xb8,0xb3,0x45,0x06,
    0xd0,0x2c,0x1e,0x8f,0xca,0x3f,0x0f,0x02,0xc1,0xaf,0xbd,0x03,0x01,0x13,0x8a,0x6b,
    0x3a,0x91,0x11,0x41,0x4f,0x67,0xdc,0xea,0x97,0xf2,0xcf,0xce,0xf0,0xb4,0xe6,0x73,
    0x96,0xac,0x74,0x22,0xe7,0xad,0x35,0x85,0xe2,0xf9,0x37,0xe8,0x1c,0x75,0xdf,0x6e,
    0x47,0xf1,0x1a,0x71,0x1d,0x29,0xc5,0x89,0x6f,0xb7,0x62,0x0e,0xaa,0x18,0xbe,0x1b,
    0xfc,0x56,0x3e,0x4b,0xc6,0xd2,0x79,0x20,0x9a,0xdb,0xc0,0xfe,0x78,0xcd,0x5a,0xf4,
    0x1f,0xdd,0xa8,0x33,0x88,0x07,0xc7,0x31,0xb1,0x12,0x10,0x59,0x27,0x80,0xec,0x5f,
    0x60,0x51,0x7f,0xa9,0x19,0xb5,0x4a,0x0d,0x2d,0xe5,0x7a,0x9f,0x93,0xc9,0x9c,0xef,
    0xa0,0xe0,0x3b,0x4d,0xae,0x2a,0xf5,0xb0,0xc8,0xeb,0xbb,0x3c,0x83,0x53,0x99,0x61,
    0x17,0x2b,0x04,0x7e,0xba,0x77,0xd6,0x26,0xe1,0x69,0x14,0x63,0x55,0x21,0x0c,0x7d
};

__device__ __constant__ uint8_t AES_RCON[11] = {
    0x00,0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36
};

// key_len_words: Nk (4/6/8 for AES-128/192/256). round_keys holds (Nr+1)*4 words.
__device__ void aes_key_expansion(const uint8_t* key, int Nk, uint32_t* round_keys, int* Nr_out) {
    int Nr = Nk + 6; // 10/12/14
    *Nr_out = Nr;
    int total_words = 4 * (Nr + 1);

    for (int i = 0; i < Nk; i++) {
        round_keys[i] = ((uint32_t)key[4*i] << 24) | ((uint32_t)key[4*i+1] << 16) |
                         ((uint32_t)key[4*i+2] << 8) | (uint32_t)key[4*i+3];
    }
    for (int i = Nk; i < total_words; i++) {
        uint32_t temp = round_keys[i-1];
        if (i % Nk == 0) {
            // RotWord + SubWord + Rcon
            uint32_t rot = (temp << 8) | (temp >> 24);
            uint8_t b0 = AES_SBOX[(rot >> 24) & 0xFF];
            uint8_t b1 = AES_SBOX[(rot >> 16) & 0xFF];
            uint8_t b2 = AES_SBOX[(rot >> 8) & 0xFF];
            uint8_t b3 = AES_SBOX[rot & 0xFF];
            temp = ((uint32_t)b0 << 24) | ((uint32_t)b1 << 16) | ((uint32_t)b2 << 8) | b3;
            temp ^= ((uint32_t)AES_RCON[i / Nk] << 24);
        } else if (Nk > 6 && i % Nk == 4) {
            uint8_t b0 = AES_SBOX[(temp >> 24) & 0xFF];
            uint8_t b1 = AES_SBOX[(temp >> 16) & 0xFF];
            uint8_t b2 = AES_SBOX[(temp >> 8) & 0xFF];
            uint8_t b3 = AES_SBOX[temp & 0xFF];
            temp = ((uint32_t)b0 << 24) | ((uint32_t)b1 << 16) | ((uint32_t)b2 << 8) | b3;
        }
        round_keys[i] = round_keys[i - Nk] ^ temp;
    }
}

__device__ __forceinline__ uint8_t gmul(uint8_t a, uint8_t b) {
    uint8_t p = 0;
    for (int i = 0; i < 8; i++) {
        if (b & 1) p ^= a;
        uint8_t hi = a & 0x80;
        a <<= 1;
        if (hi) a ^= 0x1b;
        b >>= 1;
    }
    return p;
}

__device__ void aes_add_round_key(uint8_t state[16], const uint32_t* round_keys, int round) {
    for (int c = 0; c < 4; c++) {
        uint32_t w = round_keys[round * 4 + c];
        state[c*4+0] ^= (uint8_t)(w >> 24);
        state[c*4+1] ^= (uint8_t)(w >> 16);
        state[c*4+2] ^= (uint8_t)(w >> 8);
        state[c*4+3] ^= (uint8_t)(w);
    }
}

__device__ void aes_inv_sub_bytes(uint8_t state[16]) {
    for (int i = 0; i < 16; i++) state[i] = AES_INV_SBOX[state[i]];
}

// State laid out column-major (state[c*4+r]), matching aes_add_round_key above.
__device__ void aes_inv_shift_rows(uint8_t state[16]) {
    uint8_t tmp[16];
    for (int c = 0; c < 4; c++)
        for (int r = 0; r < 4; r++)
            tmp[((c + r) % 4) * 4 + r] = state[c*4+r];
    for (int i = 0; i < 16; i++) state[i] = tmp[i];
}

__device__ void aes_inv_mix_columns(uint8_t state[16]) {
    for (int c = 0; c < 4; c++) {
        uint8_t a0 = state[c*4+0], a1 = state[c*4+1], a2 = state[c*4+2], a3 = state[c*4+3];
        state[c*4+0] = gmul(a0,0x0e) ^ gmul(a1,0x0b) ^ gmul(a2,0x0d) ^ gmul(a3,0x09);
        state[c*4+1] = gmul(a0,0x09) ^ gmul(a1,0x0e) ^ gmul(a2,0x0b) ^ gmul(a3,0x0d);
        state[c*4+2] = gmul(a0,0x0d) ^ gmul(a1,0x09) ^ gmul(a2,0x0e) ^ gmul(a3,0x0b);
        state[c*4+3] = gmul(a0,0x0b) ^ gmul(a1,0x0d) ^ gmul(a2,0x09) ^ gmul(a3,0x0e);
    }
}

__device__ void aes_decrypt_block(const uint32_t* round_keys, int Nr, const uint8_t in[16], uint8_t out[16]) {
    uint8_t state[16];
    for (int i = 0; i < 16; i++) state[i] = in[i]; // column-major load == row bytes since 4x4 square

    aes_add_round_key(state, round_keys, Nr);
    for (int round = Nr - 1; round >= 1; round--) {
        aes_inv_shift_rows(state);
        aes_inv_sub_bytes(state);
        aes_add_round_key(state, round_keys, round);
        aes_inv_mix_columns(state);
    }
    aes_inv_shift_rows(state);
    aes_inv_sub_bytes(state);
    aes_add_round_key(state, round_keys, 0);

    for (int i = 0; i < 16; i++) out[i] = state[i];
}

// Decrypts ct_len bytes (must be a multiple of 16) from `ct` using CBC with
// the given IV, writing plaintext into `out` (same length as ct).
__device__ void aes_cbc_decrypt(const uint32_t* round_keys, int Nr, const uint8_t iv[16],
                                 const uint8_t* ct, uint32_t ct_len, uint8_t* out) {
    uint8_t prev[16];
    for (int i = 0; i < 16; i++) prev[i] = iv[i];
    uint32_t nblocks = ct_len / 16;
    for (uint32_t b = 0; b < nblocks; b++) {
        const uint8_t* block = ct + b * 16;
        uint8_t dec[16];
        aes_decrypt_block(round_keys, Nr, block, dec);
        for (int i = 0; i < 16; i++) out[b*16+i] = dec[i] ^ prev[i];
        for (int i = 0; i < 16; i++) prev[i] = block[i];
    }
}

// Decrypts ct_len bytes (must be a multiple of 16) block-by-block, no
// chaining, no IV -- matches cb_common.py's aes_try_open_ecb_bytes.
__device__ void aes_ecb_decrypt(const uint32_t* round_keys, int Nr,
                                 const uint8_t* ct, uint32_t ct_len, uint8_t* out) {
    uint32_t nblocks = ct_len / 16;
    for (uint32_t b = 0; b < nblocks; b++) {
        aes_decrypt_block(round_keys, Nr, ct + b * 16, out + b * 16);
    }
}

// ============================================================================
// SEED block cipher (KISA/RFC 4269), Phase 253's thematically-motivated,
// opt-in CBC-only cipher family (gsmg.io/theseedisplanted, DBBI's
// IZLKESEEDQPPEN). Ported from OpenSSL's crypto/seed/{seed_local.h,seed.c}
// (Apache-2.0), the exact same source used for src/seed_cipher.rs's CPU
// reference -- correctness of that Rust port is independently pinned against
// all four RFC 4269 Appendix B known-answer vectors; this device-side port
// is validated by GPU/CPU cross-check (selftest.rs) against that reference,
// same discipline as the AES port above. Decrypt-only: the oracle never
// needs SEED_encrypt.
// ============================================================================

__device__ __constant__ uint32_t SEED_SS[4][256] = {
    {
        0x2989a1a8u, 0x05858184u, 0x16c6d2d4u, 0x13c3d3d0u, 0x14445054u, 0x1d0d111cu, 0x2c8ca0acu, 0x25052124u,
        0x1d4d515cu, 0x03434340u, 0x18081018u, 0x1e0e121cu, 0x11415150u, 0x3cccf0fcu, 0x0acac2c8u, 0x23436360u,
        0x28082028u, 0x04444044u, 0x20002020u, 0x1d8d919cu, 0x20c0e0e0u, 0x22c2e2e0u, 0x08c8c0c8u, 0x17071314u,
        0x2585a1a4u, 0x0f8f838cu, 0x03030300u, 0x3b4b7378u, 0x3b8bb3b8u, 0x13031310u, 0x12c2d2d0u, 0x2ecee2ecu,
        0x30407070u, 0x0c8c808cu, 0x3f0f333cu, 0x2888a0a8u, 0x32023230u, 0x1dcdd1dcu, 0x36c6f2f4u, 0x34447074u,
        0x2ccce0ecu, 0x15859194u, 0x0b0b0308u, 0x17475354u, 0x1c4c505cu, 0x1b4b5358u, 0x3d8db1bcu, 0x01010100u,
        0x24042024u, 0x1c0c101cu, 0x33437370u, 0x18889098u, 0x10001010u, 0x0cccc0ccu, 0x32c2f2f0u, 0x19c9d1d8u,
        0x2c0c202cu, 0x27c7e3e4u, 0x32427270u, 0x03838380u, 0x1b8b9398u, 0x11c1d1d0u, 0x06868284u, 0x09c9c1c8u,
        0x20406060u, 0x10405050u, 0x2383a3a0u, 0x2bcbe3e8u, 0x0d0d010cu, 0x3686b2b4u, 0x1e8e929cu, 0x0f4f434cu,
        0x3787b3b4u, 0x1a4a5258u, 0x06c6c2c4u, 0x38487078u, 0x2686a2a4u, 0x12021210u, 0x2f8fa3acu, 0x15c5d1d4u,
        0x21416160u, 0x03c3c3c0u, 0x3484b0b4u, 0x01414140u, 0x12425250u, 0x3d4d717cu, 0x0d8d818cu, 0x08080008u,
        0x1f0f131cu, 0x19899198u, 0x00000000u, 0x19091118u, 0x04040004u, 0x13435350u, 0x37c7f3f4u, 0x21c1e1e0u,
        0x3dcdf1fcu, 0x36467274u, 0x2f0f232cu, 0x27072324u, 0x3080b0b0u, 0x0b8b8388u, 0x0e0e020cu, 0x2b8ba3a8u,
        0x2282a2a0u, 0x2e4e626cu, 0x13839390u, 0x0d4d414cu, 0x29496168u, 0x3c4c707cu, 0x09090108u, 0x0a0a0208u,
        0x3f8fb3bcu, 0x2fcfe3ecu, 0x33c3f3f0u, 0x05c5c1c4u, 0x07878384u, 0x14041014u, 0x3ecef2fcu, 0x24446064u,
        0x1eced2dcu, 0x2e0e222cu, 0x0b4b4348u, 0x1a0a1218u, 0x06060204u, 0x21012120u, 0x2b4b6368u, 0x26466264u,
        0x02020200u, 0x35c5f1f4u, 0x12829290u, 0x0a8a8288u, 0x0c0c000cu, 0x3383b3b0u, 0x3e4e727cu, 0x10c0d0d0u,
        0x3a4a7278u, 0x07474344u, 0x16869294u, 0x25c5e1e4u, 0x26062224u, 0x00808080u, 0x2d8da1acu, 0x1fcfd3dcu,
        0x2181a1a0u, 0x30003030u, 0x37073334u, 0x2e8ea2acu, 0x36063234u, 0x15051114u, 0x22022220u, 0x38083038u,
        0x34c4f0f4u, 0x2787a3a4u, 0x05454144u, 0x0c4c404cu, 0x01818180u, 0x29c9e1e8u, 0x04848084u, 0x17879394u,
        0x35053134u, 0x0bcbc3c8u, 0x0ecec2ccu, 0x3c0c303cu, 0x31417170u, 0x11011110u, 0x07c7c3c4u, 0x09898188u,
        0x35457174u, 0x3bcbf3f8u, 0x1acad2d8u, 0x38c8f0f8u, 0x14849094u, 0x19495158u, 0x02828280u, 0x04c4c0c4u,
        0x3fcff3fcu, 0x09494148u, 0x39093138u, 0x27476364u, 0x00c0c0c0u, 0x0fcfc3ccu, 0x17c7d3d4u, 0x3888b0b8u,
        0x0f0f030cu, 0x0e8e828cu, 0x02424240u, 0x23032320u, 0x11819190u, 0x2c4c606cu, 0x1bcbd3d8u, 0x2484a0a4u,
        0x34043034u, 0x31c1f1f0u, 0x08484048u, 0x02c2c2c0u, 0x2f4f636cu, 0x3d0d313cu, 0x2d0d212cu, 0x00404040u,
        0x3e8eb2bcu, 0x3e0e323cu, 0x3c8cb0bcu, 0x01c1c1c0u, 0x2a8aa2a8u, 0x3a8ab2b8u, 0x0e4e424cu, 0x15455154u,
        0x3b0b3338u, 0x1cccd0dcu, 0x28486068u, 0x3f4f737cu, 0x1c8c909cu, 0x18c8d0d8u, 0x0a4a4248u, 0x16465254u,
        0x37477374u, 0x2080a0a0u, 0x2dcde1ecu, 0x06464244u, 0x3585b1b4u, 0x2b0b2328u, 0x25456164u, 0x3acaf2f8u,
        0x23c3e3e0u, 0x3989b1b8u, 0x3181b1b0u, 0x1f8f939cu, 0x1e4e525cu, 0x39c9f1f8u, 0x26c6e2e4u, 0x3282b2b0u,
        0x31013130u, 0x2acae2e8u, 0x2d4d616cu, 0x1f4f535cu, 0x24c4e0e4u, 0x30c0f0f0u, 0x0dcdc1ccu, 0x08888088u,
        0x16061214u, 0x3a0a3238u, 0x18485058u, 0x14c4d0d4u, 0x22426260u, 0x29092128u, 0x07070304u, 0x33033330u,
        0x28c8e0e8u, 0x1b0b1318u, 0x05050104u, 0x39497178u, 0x10809090u, 0x2a4a6268u, 0x2a0a2228u, 0x1a8a9298u,
    },
    {
        0x38380830u, 0xe828c8e0u, 0x2c2d0d21u, 0xa42686a2u, 0xcc0fcfc3u, 0xdc1eced2u, 0xb03383b3u, 0xb83888b0u,
        0xac2f8fa3u, 0x60204060u, 0x54154551u, 0xc407c7c3u, 0x44044440u, 0x6c2f4f63u, 0x682b4b63u, 0x581b4b53u,
        0xc003c3c3u, 0x60224262u, 0x30330333u, 0xb43585b1u, 0x28290921u, 0xa02080a0u, 0xe022c2e2u, 0xa42787a3u,
        0xd013c3d3u, 0x90118191u, 0x10110111u, 0x04060602u, 0x1c1c0c10u, 0xbc3c8cb0u, 0x34360632u, 0x480b4b43u,
        0xec2fcfe3u, 0x88088880u, 0x6c2c4c60u, 0xa82888a0u, 0x14170713u, 0xc404c4c0u, 0x14160612u, 0xf434c4f0u,
        0xc002c2c2u, 0x44054541u, 0xe021c1e1u, 0xd416c6d2u, 0x3c3f0f33u, 0x3c3d0d31u, 0x8c0e8e82u, 0x98188890u,
        0x28280820u, 0x4c0e4e42u, 0xf436c6f2u, 0x3c3e0e32u, 0xa42585a1u, 0xf839c9f1u, 0x0c0d0d01u, 0xdc1fcfd3u,
        0xd818c8d0u, 0x282b0b23u, 0x64264662u, 0x783a4a72u, 0x24270723u, 0x2c2f0f23u, 0xf031c1f1u, 0x70324272u,
        0x40024242u, 0xd414c4d0u, 0x40014141u, 0xc000c0c0u, 0x70334373u, 0x64274763u, 0xac2c8ca0u, 0x880b8b83u,
        0xf437c7f3u, 0xac2d8da1u, 0x80008080u, 0x1c1f0f13u, 0xc80acac2u, 0x2c2c0c20u, 0xa82a8aa2u, 0x34340430u,
        0xd012c2d2u, 0x080b0b03u, 0xec2ecee2u, 0xe829c9e1u, 0x5c1d4d51u, 0x94148490u, 0x18180810u, 0xf838c8f0u,
        0x54174753u, 0xac2e8ea2u, 0x08080800u, 0xc405c5c1u, 0x10130313u, 0xcc0dcdc1u, 0x84068682u, 0xb83989b1u,
        0xfc3fcff3u, 0x7c3d4d71u, 0xc001c1c1u, 0x30310131u, 0xf435c5f1u, 0x880a8a82u, 0x682a4a62u, 0xb03181b1u,
        0xd011c1d1u, 0x20200020u, 0xd417c7d3u, 0x00020202u, 0x20220222u, 0x04040400u, 0x68284860u, 0x70314171u,
        0x04070703u, 0xd81bcbd3u, 0x9c1d8d91u, 0x98198991u, 0x60214161u, 0xbc3e8eb2u, 0xe426c6e2u, 0x58194951u,
        0xdc1dcdd1u, 0x50114151u, 0x90108090u, 0xdc1cccd0u, 0x981a8a92u, 0xa02383a3u, 0xa82b8ba3u, 0xd010c0d0u,
        0x80018181u, 0x0c0f0f03u, 0x44074743u, 0x181a0a12u, 0xe023c3e3u, 0xec2ccce0u, 0x8c0d8d81u, 0xbc3f8fb3u,
        0x94168692u, 0x783b4b73u, 0x5c1c4c50u, 0xa02282a2u, 0xa02181a1u, 0x60234363u, 0x20230323u, 0x4c0d4d41u,
        0xc808c8c0u, 0x9c1e8e92u, 0x9c1c8c90u, 0x383a0a32u, 0x0c0c0c00u, 0x2c2e0e22u, 0xb83a8ab2u, 0x6c2e4e62u,
        0x9c1f8f93u, 0x581a4a52u, 0xf032c2f2u, 0x90128292u, 0xf033c3f3u, 0x48094941u, 0x78384870u, 0xcc0cccc0u,
        0x14150511u, 0xf83bcbf3u, 0x70304070u, 0x74354571u, 0x7c3f4f73u, 0x34350531u, 0x10100010u, 0x00030303u,
        0x64244460u, 0x6c2d4d61u, 0xc406c6c2u, 0x74344470u, 0xd415c5d1u, 0xb43484b0u, 0xe82acae2u, 0x08090901u,
        0x74364672u, 0x18190911u, 0xfc3ecef2u, 0x40004040u, 0x10120212u, 0xe020c0e0u, 0xbc3d8db1u, 0x04050501u,
        0xf83acaf2u, 0x00010101u, 0xf030c0f0u, 0x282a0a22u, 0x5c1e4e52u, 0xa82989a1u, 0x54164652u, 0x40034343u,
        0x84058581u, 0x14140410u, 0x88098981u, 0x981b8b93u, 0xb03080b0u, 0xe425c5e1u, 0x48084840u, 0x78394971u,
        0x94178793u, 0xfc3cccf0u, 0x1c1e0e12u, 0x80028282u, 0x20210121u, 0x8c0c8c80u, 0x181b0b13u, 0x5c1f4f53u,
        0x74374773u, 0x54144450u, 0xb03282b2u, 0x1c1d0d11u, 0x24250521u, 0x4c0f4f43u, 0x00000000u, 0x44064642u,
        0xec2dcde1u, 0x58184850u, 0x50124252u, 0xe82bcbe3u, 0x7c3e4e72u, 0xd81acad2u, 0xc809c9c1u, 0xfc3dcdf1u,
        0x30300030u, 0x94158591u, 0x64254561u, 0x3c3c0c30u, 0xb43686b2u, 0xe424c4e0u, 0xb83b8bb3u, 0x7c3c4c70u,
        0x0c0e0e02u, 0x50104050u, 0x38390931u, 0x24260622u, 0x30320232u, 0x84048480u, 0x68294961u, 0x90138393u,
        0x34370733u, 0xe427c7e3u, 0x24240420u, 0xa42484a0u, 0xc80bcbc3u, 0x50134353u, 0x080a0a02u, 0x84078783u,
        0xd819c9d1u, 0x4c0c4c40u, 0x80038383u, 0x8c0f8f83u, 0xcc0ecec2u, 0x383b0b33u, 0x480a4a42u, 0xb43787b3u,
    },
    {
        0xa1a82989u, 0x81840585u, 0xd2d416c6u, 0xd3d013c3u, 0x50541444u, 0x111c1d0du, 0xa0ac2c8cu, 0x21242505u,
        0x515c1d4du, 0x43400343u, 0x10181808u, 0x121c1e0eu, 0x51501141u, 0xf0fc3cccu, 0xc2c80acau, 0x63602343u,
        0x20282808u, 0x40440444u, 0x20202000u, 0x919c1d8du, 0xe0e020c0u, 0xe2e022c2u, 0xc0c808c8u, 0x13141707u,
        0xa1a42585u, 0x838c0f8fu, 0x03000303u, 0x73783b4bu, 0xb3b83b8bu, 0x13101303u, 0xd2d012c2u, 0xe2ec2eceu,
        0x70703040u, 0x808c0c8cu, 0x333c3f0fu, 0xa0a82888u, 0x32303202u, 0xd1dc1dcdu, 0xf2f436c6u, 0x70743444u,
        0xe0ec2cccu, 0x91941585u, 0x03080b0bu, 0x53541747u, 0x505c1c4cu, 0x53581b4bu, 0xb1bc3d8du, 0x01000101u,
        0x20242404u, 0x101c1c0cu, 0x73703343u, 0x90981888u, 0x10101000u, 0xc0cc0cccu, 0xf2f032c2u, 0xd1d819c9u,
        0x202c2c0cu, 0xe3e427c7u, 0x72703242u, 0x83800383u, 0x93981b8bu, 0xd1d011c1u, 0x82840686u, 0xc1c809c9u,
        0x60602040u, 0x50501040u, 0xa3a02383u, 0xe3e82bcbu, 0x010c0d0du, 0xb2b43686u, 0x929c1e8eu, 0x434c0f4fu,
        0xb3b43787u, 0x52581a4au, 0xc2c406c6u, 0x70783848u, 0xa2a42686u, 0x12101202u, 0xa3ac2f8fu, 0xd1d415c5u,
        0x61602141u, 0xc3c003c3u, 0xb0b43484u, 0x41400141u, 0x52501242u, 0x717c3d4du, 0x818c0d8du, 0x00080808u,
        0x131c1f0fu, 0x91981989u, 0x00000000u, 0x11181909u, 0x00040404u, 0x53501343u, 0xf3f437c7u, 0xe1e021c1u,
        0xf1fc3dcdu, 0x72743646u, 0x232c2f0fu, 0x23242707u, 0xb0b03080u, 0x83880b8bu, 0x020c0e0eu, 0xa3a82b8bu,
        0xa2a02282u, 0x626c2e4eu, 0x93901383u, 0x414c0d4du, 0x61682949u, 0x707c3c4cu, 0x01080909u, 0x02080a0au,
        0xb3bc3f8fu, 0xe3ec2fcfu, 0xf3f033c3u, 0xc1c405c5u, 0x83840787u, 0x10141404u, 0xf2fc3eceu, 0x60642444u,
        0xd2dc1eceu, 0x222c2e0eu, 0x43480b4bu, 0x12181a0au, 0x02040606u, 0x21202101u, 0x63682b4bu, 0x62642646u,
        0x02000202u, 0xf1f435c5u, 0x92901282u, 0x82880a8au, 0x000c0c0cu, 0xb3b03383u, 0x727c3e4eu, 0xd0d010c0u,
        0x72783a4au, 0x43440747u, 0x92941686u, 0xe1e425c5u, 0x22242606u, 0x80800080u, 0xa1ac2d8du, 0xd3dc1fcfu,
        0xa1a02181u, 0x30303000u, 0x33343707u, 0xa2ac2e8eu, 0x32343606u, 0x11141505u, 0x22202202u, 0x30383808u,
        0xf0f434c4u, 0xa3a42787u, 0x41440545u, 0x404c0c4cu, 0x81800181u, 0xe1e829c9u, 0x80840484u, 0x93941787u,
        0x31343505u, 0xc3c80bcbu, 0xc2cc0eceu, 0x303c3c0cu, 0x71703141u, 0x11101101u, 0xc3c407c7u, 0x81880989u,
        0x71743545u, 0xf3f83bcbu, 0xd2d81acau, 0xf0f838c8u, 0x90941484u, 0x51581949u, 0x82800282u, 0xc0c404c4u,
        0xf3fc3fcfu, 0x41480949u, 0x31383909u, 0x63642747u, 0xc0c000c0u, 0xc3cc0fcfu, 0xd3d417c7u, 0xb0b83888u,
        0x030c0f0fu, 0x828c0e8eu, 0x42400242u, 0x23202303u, 0x91901181u, 0x606c2c4cu, 0xd3d81bcbu, 0xa0a42484u,
        0x30343404u, 0xf1f031c1u, 0x40480848u, 0xc2c002c2u, 0x636c2f4fu, 0x313c3d0du, 0x212c2d0du, 0x40400040u,
        0xb2bc3e8eu, 0x323c3e0eu, 0xb0bc3c8cu, 0xc1c001c1u, 0xa2a82a8au, 0xb2b83a8au, 0x424c0e4eu, 0x51541545u,
        0x33383b0bu, 0xd0dc1cccu, 0x60682848u, 0x737c3f4fu, 0x909c1c8cu, 0xd0d818c8u, 0x42480a4au, 0x52541646u,
        0x73743747u, 0xa0a02080u, 0xe1ec2dcdu, 0x42440646u, 0xb1b43585u, 0x23282b0bu, 0x61642545u, 0xf2f83acau,
        0xe3e023c3u, 0xb1b83989u, 0xb1b03181u, 0x939c1f8fu, 0x525c1e4eu, 0xf1f839c9u, 0xe2e426c6u, 0xb2b03282u,
        0x31303101u, 0xe2e82acau, 0x616c2d4du, 0x535c1f4fu, 0xe0e424c4u, 0xf0f030c0u, 0xc1cc0dcdu, 0x80880888u,
        0x12141606u, 0x32383a0au, 0x50581848u, 0xd0d414c4u, 0x62602242u, 0x21282909u, 0x03040707u, 0x33303303u,
        0xe0e828c8u, 0x13181b0bu, 0x01040505u, 0x71783949u, 0x90901080u, 0x62682a4au, 0x22282a0au, 0x92981a8au,
    },
    {
        0x08303838u, 0xc8e0e828u, 0x0d212c2du, 0x86a2a426u, 0xcfc3cc0fu, 0xced2dc1eu, 0x83b3b033u, 0x88b0b838u,
        0x8fa3ac2fu, 0x40606020u, 0x45515415u, 0xc7c3c407u, 0x44404404u, 0x4f636c2fu, 0x4b63682bu, 0x4b53581bu,
        0xc3c3c003u, 0x42626022u, 0x03333033u, 0x85b1b435u, 0x09212829u, 0x80a0a020u, 0xc2e2e022u, 0x87a3a427u,
        0xc3d3d013u, 0x81919011u, 0x01111011u, 0x06020406u, 0x0c101c1cu, 0x8cb0bc3cu, 0x06323436u, 0x4b43480bu,
        0xcfe3ec2fu, 0x88808808u, 0x4c606c2cu, 0x88a0a828u, 0x07131417u, 0xc4c0c404u, 0x06121416u, 0xc4f0f434u,
        0xc2c2c002u, 0x45414405u, 0xc1e1e021u, 0xc6d2d416u, 0x0f333c3fu, 0x0d313c3du, 0x8e828c0eu, 0x88909818u,
        0x08202828u, 0x4e424c0eu, 0xc6f2f436u, 0x0e323c3eu, 0x85a1a425u, 0xc9f1f839u, 0x0d010c0du, 0xcfd3dc1fu,
        0xc8d0d818u, 0x0b23282bu, 0x46626426u, 0x4a72783au, 0x07232427u, 0x0f232c2fu, 0xc1f1f031u, 0x42727032u,
        0x42424002u, 0xc4d0d414u, 0x41414001u, 0xc0c0c000u, 0x43737033u, 0x47636427u, 0x8ca0ac2cu, 0x8b83880bu,
        0xc7f3f437u, 0x8da1ac2du, 0x80808000u, 0x0f131c1fu, 0xcac2c80au, 0x0c202c2cu, 0x8aa2a82au, 0x04303434u,
        0xc2d2d012u, 0x0b03080bu, 0xcee2ec2eu, 0xc9e1e829u, 0x4d515c1du, 0x84909414u, 0x08101818u, 0xc8f0f838u,
        0x47535417u, 0x8ea2ac2eu, 0x08000808u, 0xc5c1c405u, 0x03131013u, 0xcdc1cc0du, 0x86828406u, 0x89b1b839u,
        0xcff3fc3fu, 0x4d717c3du, 0xc1c1c001u, 0x01313031u, 0xc5f1f435u, 0x8a82880au, 0x4a62682au, 0x81b1b031u,
        0xc1d1d011u, 0x00202020u, 0xc7d3d417u, 0x02020002u, 0x02222022u, 0x04000404u, 0x48606828u, 0x41717031u,
        0x07030407u, 0xcbd3d81bu, 0x8d919c1du, 0x89919819u, 0x41616021u, 0x8eb2bc3eu, 0xc6e2e426u, 0x49515819u,
        0xcdd1dc1du, 0x41515011u, 0x80909010u, 0xccd0dc1cu, 0x8a92981au, 0x83a3a023u, 0x8ba3a82bu, 0xc0d0d010u,
        0x81818001u, 0x0f030c0fu, 0x47434407u, 0x0a12181au, 0xc3e3e023u, 0xcce0ec2cu, 0x8d818c0du, 0x8fb3bc3fu,
        0x86929416u, 0x4b73783bu, 0x4c505c1cu, 0x82a2a022u, 0x81a1a021u, 0x43636023u, 0x03232023u, 0x4d414c0du,
        0xc8c0c808u, 0x8e929c1eu, 0x8c909c1cu, 0x0a32383au, 0x0c000c0cu, 0x0e222c2eu, 0x8ab2b83au, 0x4e626c2eu,
        0x8f939c1fu, 0x4a52581au, 0xc2f2f032u, 0x82929012u, 0xc3f3f033u, 0x49414809u, 0x48707838u, 0xccc0cc0cu,
        0x05111415u, 0xcbf3f83bu, 0x40707030u, 0x45717435u, 0x4f737c3fu, 0x05313435u, 0x00101010u, 0x03030003u,
        0x44606424u, 0x4d616c2du, 0xc6c2c406u, 0x44707434u, 0xc5d1d415u, 0x84b0b434u, 0xcae2e82au, 0x09010809u,
        0x46727436u, 0x09111819u, 0xcef2fc3eu, 0x40404000u, 0x02121012u, 0xc0e0e020u, 0x8db1bc3du, 0x05010405u,
        0xcaf2f83au, 0x01010001u, 0xc0f0f030u, 0x0a22282au, 0x4e525c1eu, 0x89a1a829u, 0x46525416u, 0x43434003u,
        0x85818405u, 0x04101414u, 0x89818809u, 0x8b93981bu, 0x80b0b030u, 0xc5e1e425u, 0x48404808u, 0x49717839u,
        0x87939417u, 0xccf0fc3cu, 0x0e121c1eu, 0x82828002u, 0x01212021u, 0x8c808c0cu, 0x0b13181bu, 0x4f535c1fu,
        0x47737437u, 0x44505414u, 0x82b2b032u, 0x0d111c1du, 0x05212425u, 0x4f434c0fu, 0x00000000u, 0x46424406u,
        0xcde1ec2du, 0x48505818u, 0x42525012u, 0xcbe3e82bu, 0x4e727c3eu, 0xcad2d81au, 0xc9c1c809u, 0xcdf1fc3du,
        0x00303030u, 0x85919415u, 0x45616425u, 0x0c303c3cu, 0x86b2b436u, 0xc4e0e424u, 0x8bb3b83bu, 0x4c707c3cu,
        0x0e020c0eu, 0x40505010u, 0x09313839u, 0x06222426u, 0x02323032u, 0x84808404u, 0x49616829u, 0x83939013u,
        0x07333437u, 0xc7e3e427u, 0x04202424u, 0x84a0a424u, 0xcbc3c80bu, 0x43535013u, 0x0a02080au, 0x87838407u,
        0xc9d1d819u, 0x4c404c0cu, 0x83838003u, 0x8f838c0fu, 0xcec2cc0eu, 0x0b33383bu, 0x4a42480au, 0x87b3b437u,
    },
};

__device__ __constant__ uint32_t SEED_KC[16] = {
    0x9e3779b9u, 0x3c6ef373u, 0x78dde6e6u, 0xf1bbcdccu, 0xe3779b99u, 0xc6ef3733u, 0x8dde6e67u, 0x1bbcdccfu,
    0x3779b99eu, 0x6ef3733cu, 0xdde6e678u, 0xbbcdccf1u, 0x779b99e3u, 0xef3733c6u, 0xde6e678du, 0xbcdccf1bu
};

__device__ __forceinline__ uint32_t seed_g(uint32_t v) {
    return SEED_SS[0][v & 0xffu] ^ SEED_SS[1][(v >> 8) & 0xffu] ^ SEED_SS[2][(v >> 16) & 0xffu] ^ SEED_SS[3][(v >> 24) & 0xffu];
}

__device__ __forceinline__ uint32_t seed_char2word(const uint8_t* c) {
    return (((uint32_t)c[0]) << 24) | (((uint32_t)c[1]) << 16) | (((uint32_t)c[2]) << 8) | ((uint32_t)c[3]);
}

__device__ __forceinline__ void seed_word2char(uint32_t w, uint8_t* out) {
    out[0] = (uint8_t)(w >> 24);
    out[1] = (uint8_t)(w >> 16);
    out[2] = (uint8_t)(w >> 8);
    out[3] = (uint8_t)w;
}

// 16-byte raw key -> 32-word round-key schedule (SEED_set_key).
__device__ void seed_set_key(const uint8_t key[16], uint32_t ks[32]) {
    uint32_t x1 = seed_char2word(key);
    uint32_t x2 = seed_char2word(key + 4);
    uint32_t x3 = seed_char2word(key + 8);
    uint32_t x4 = seed_char2word(key + 12);
    uint32_t t0, t1;

    t0 = x1 + x3 - SEED_KC[0];
    t1 = x2 - x4 + SEED_KC[0];
    ks[0] = seed_g(t0);
    ks[1] = seed_g(t1);

    // KEYSCHEDULE_UPDATE1 with KC1
    t0 = x1;
    x1 = (x1 >> 8) ^ (x2 << 24);
    x2 = (x2 >> 8) ^ (t0 << 24);
    t0 = x1 + x3 - SEED_KC[1];
    t1 = x2 + SEED_KC[1] - x4;
    ks[2] = seed_g(t0);
    ks[3] = seed_g(t1);

    #pragma unroll
    for (int i = 2; i < 16; i += 2) {
        // KEYSCHEDULE_UPDATE0 with KC[i]
        t0 = x3;
        x3 = (x3 << 8) ^ (x4 >> 24);
        x4 = (x4 << 8) ^ (t0 >> 24);
        t0 = x1 + x3 - SEED_KC[i];
        t1 = x2 + SEED_KC[i] - x4;
        ks[i * 2] = seed_g(t0);
        ks[i * 2 + 1] = seed_g(t1);

        // KEYSCHEDULE_UPDATE1 with KC[i+1]
        t0 = x1;
        x1 = (x1 >> 8) ^ (x2 << 24);
        x2 = (x2 >> 8) ^ (t0 << 24);
        t0 = x1 + x3 - SEED_KC[i + 1];
        t1 = x2 + SEED_KC[i + 1] - x4;
        ks[i * 2 + 2] = seed_g(t0);
        ks[i * 2 + 3] = seed_g(t1);
    }
}

__device__ __forceinline__ void seed_e(const uint32_t* ks, int rbase, uint32_t* x1, uint32_t* x2, uint32_t x3, uint32_t x4) {
    uint32_t t0 = x3 ^ ks[rbase];
    uint32_t t1 = x4 ^ ks[rbase + 1];
    t1 ^= t0;
    t1 = seed_g(t1);
    t0 = t0 + t1;
    t0 = seed_g(t0);
    t1 = t1 + t0;
    t1 = seed_g(t1);
    t0 = t0 + t1;
    *x1 ^= t0;
    *x2 ^= t1;
}

__device__ void seed_decrypt_block(const uint32_t ks[32], const uint8_t in[16], uint8_t out[16]) {
    uint32_t x1 = seed_char2word(in);
    uint32_t x2 = seed_char2word(in + 4);
    uint32_t x3 = seed_char2word(in + 8);
    uint32_t x4 = seed_char2word(in + 12);

    int rbase = 30;
    #pragma unroll
    for (int round = 0; round < 8; round++) {
        seed_e(ks, rbase, &x1, &x2, x3, x4);
        rbase -= 2;
        seed_e(ks, rbase, &x3, &x4, x1, x2);
        rbase -= 2;
    }

    seed_word2char(x3, out);
    seed_word2char(x4, out + 4);
    seed_word2char(x1, out + 8);
    seed_word2char(x2, out + 12);
}

// SEED-CBC decrypt: same P_i = D(C_i) XOR C_{i-1} chaining as aes_cbc_decrypt.
__device__ void seed_cbc_decrypt(const uint32_t ks[32], const uint8_t iv[16],
                                  const uint8_t* ct, uint32_t ct_len, uint8_t* out) {
    uint8_t prev[16];
    for (int i = 0; i < 16; i++) prev[i] = iv[i];
    uint32_t nblocks = ct_len / 16;
    for (uint32_t b = 0; b < nblocks; b++) {
        const uint8_t* block = ct + b * 16;
        uint8_t dec[16];
        seed_decrypt_block(ks, block, dec);
        for (int i = 0; i < 16; i++) out[b*16+i] = dec[i] ^ prev[i];
        for (int i = 0; i < 16; i++) prev[i] = block[i];
    }
}

// ============================================================================
// AES-128/192/256 forward cipher (FIPS-197 Cipher) -- needed only to generate
// the E(K, .) keystream blocks that drive CFB/OFB/CTR. Uses the same forward
// round-key schedule (`aes_key_expansion`) already used by the InvCipher path
// above; no separate key schedule required.
// ============================================================================

__device__ void aes_sub_bytes(uint8_t state[16]) {
    for (int i = 0; i < 16; i++) state[i] = AES_SBOX[state[i]];
}

__device__ void aes_shift_rows(uint8_t state[16]) {
    uint8_t tmp[16];
    for (int c = 0; c < 4; c++)
        for (int r = 0; r < 4; r++)
            tmp[c*4+r] = state[((c + r) % 4) * 4 + r];
    for (int i = 0; i < 16; i++) state[i] = tmp[i];
}

__device__ void aes_mix_columns(uint8_t state[16]) {
    for (int c = 0; c < 4; c++) {
        uint8_t a0 = state[c*4+0], a1 = state[c*4+1], a2 = state[c*4+2], a3 = state[c*4+3];
        state[c*4+0] = gmul(a0,0x02) ^ gmul(a1,0x03) ^ a2 ^ a3;
        state[c*4+1] = a0 ^ gmul(a1,0x02) ^ gmul(a2,0x03) ^ a3;
        state[c*4+2] = a0 ^ a1 ^ gmul(a2,0x02) ^ gmul(a3,0x03);
        state[c*4+3] = gmul(a0,0x03) ^ a1 ^ a2 ^ gmul(a3,0x02);
    }
}

__device__ void aes_encrypt_block(const uint32_t* round_keys, int Nr, const uint8_t in[16], uint8_t out[16]) {
    uint8_t state[16];
    for (int i = 0; i < 16; i++) state[i] = in[i];

    aes_add_round_key(state, round_keys, 0);
    for (int round = 1; round < Nr; round++) {
        aes_sub_bytes(state);
        aes_shift_rows(state);
        aes_mix_columns(state);
        aes_add_round_key(state, round_keys, round);
    }
    aes_sub_bytes(state);
    aes_shift_rows(state);
    aes_add_round_key(state, round_keys, Nr);

    for (int i = 0; i < 16; i++) out[i] = state[i];
}

// CFB/OFB/CTR keystream-XOR decrypt, arbitrary ct_len (no padding in these
// modes -- matches cb_common.py's aes_try_open_stream_bytes, which passes
// the whole decrypted body straight to the printable gate). `mode` is one of
// CIPHER_CFB/CIPHER_OFB/CIPHER_CTR.
__device__ void aes_stream_decrypt(const uint32_t* round_keys, int Nr, const uint8_t iv[16], int mode,
                                    const uint8_t* ct, uint32_t ct_len, uint8_t* out) {
    uint8_t reg[16];
    for (int i = 0; i < 16; i++) reg[i] = iv[i];

    uint32_t nblocks = (ct_len + 15) / 16;
    for (uint32_t b = 0; b < nblocks; b++) {
        uint8_t keystream[16];
        aes_encrypt_block(round_keys, Nr, reg, keystream);

        uint32_t offset = b * 16;
        uint32_t take = (offset + 16 <= ct_len) ? 16 : (ct_len - offset);
        const uint8_t* cblock = ct + offset;
        for (uint32_t i = 0; i < take; i++) out[offset + i] = cblock[i] ^ keystream[i];

        if (mode == CIPHER_CFB) {
            // Full-block ciphertext feedback (CFB128). Only matters when
            // there's a next block, i.e. take == 16.
            for (int i = 0; i < 16; i++) reg[i] = cblock[i];
        } else if (mode == CIPHER_OFB) {
            for (int i = 0; i < 16; i++) reg[i] = keystream[i];
        } else if (mode == CIPHER_CTR) {
            // 128-bit big-endian counter increment, matching the `cryptography`
            // library's default CTR mode (IV used directly as the initial
            // full-width counter block).
            for (int i = 15; i >= 0; i--) {
                if (++reg[i] != 0) break;
            }
        }
    }
}

// ============================================================================
// PKCS7 validity + printable z-score gate (must match cb_common.py exactly).
// ============================================================================

#define PRINTABLE_NUM 98
#define PRINTABLE_DEN 256.0f
#define PRINTABLE_Z_WEAK 5.0f
#define PRINTABLE_Z_STRONG 8.0f

// Returns 1 and sets *body_len if PKCS7-valid, else 0.
__device__ int pkcs7_check(const uint8_t* pt, uint32_t pt_len, uint32_t* body_len) {
    if (pt_len == 0) return 0;
    uint8_t pad = pt[pt_len - 1];
    if (pad < 1 || pad > 16 || pad > pt_len) return 0;
    for (uint32_t i = 0; i < pad; i++) {
        if (pt[pt_len - 1 - i] != pad) return 0;
    }
    *body_len = pt_len - pad;
    return 1;
}

__device__ float printable_z_score(const uint8_t* body, uint32_t n) {
    if (n == 0) return 0.0f;
    uint32_t count = 0;
    for (uint32_t i = 0; i < n; i++) {
        uint8_t c = body[i];
        if ((c >= 32 && c < 127) || c == 9 || c == 10 || c == 13) count++;
    }
    float p0 = PRINTABLE_NUM / PRINTABLE_DEN;
    float mean = n * p0;
    float var = n * p0 * (1.0f - p0);
    if (var <= 0.0f) return 0.0f;
    return (count - mean) / sqrtf(var);
}

// Full dummy PKCS7 block (pad == block size): 256^-16 = 2^-128 chance a wrong
// password's decrypt reproduces sixteen 0x10 bytes by accident, independent
// of body_len -- which is fully determined by this blob's fixed ciphertext
// length once pad is known, so it adds no further specificity. Originally
// also required body_len == 64 (mirrors cb_common.py's
// is_structural_binary_plaintext, written when only the two 80-byte blobs
// SALPH/P32TRAILING were swept), which silently excluded URLBLOB (body_len
// 80) and COSMIC (body_len 1312) from ever reporting this signal -- see the
// matching comment in cpu_oracle.rs::try_open. body_len is kept as a
// parameter for host-side struct/logging symmetry, not used in the gate.
__device__ int is_structural_binary_plaintext(uint32_t pad, uint32_t body_len) {
    (void)body_len;
    return pad == 16;
}

// ============================================================================
// Hit record (host layout must match gpu.rs's #[repr(C)] DecryptHit exactly).
// ============================================================================

struct DecryptHit {
    uint32_t candidate_idx;
    uint32_t variant_idx;
    uint32_t blob_idx;
    uint32_t hit_kind;   // 1 = weak (logged), 2 = strong, 3 = structural bypass
    float z_score;
    uint8_t _pad[12];    // keep struct size a clean 32 bytes for alignment
};

// Host layout must match gpu.rs's #[repr(C)] StreamKeyHit exactly. Emitted
// only for a CFB/OFB/CTR candidate whose decrypted half/better_half chunk's
// derived hash160 (compressed or uncompressed) is a Bloom-filter hit -- see
// aes_kdf_scan's stream-mode branch below and stream_key_check.rs, which is
// what a Bloom hit here is still Bloom-only for: the host does the mandatory
// live API confirmation before treating anything here as real, same as
// every other Bloom hit in this project (keyshape::record_precomputed_hit).
struct StreamKeyHit {
    uint32_t candidate_idx;
    uint32_t variant_idx;
    uint32_t blob_idx;
    uint32_t chunk_index;    // 0 = half, 1 = better_half
    uint32_t address_type;   // 0 = compressed, 1 = uncompressed
    uint8_t  private_key[32];
    uint8_t  hash160[20];
    uint8_t  _pad[8];        // pad to a clean 72-byte, 8-aligned struct
};

// Variant table: kdf_kind (KDF_LEGACY_* / KDF_PBKDF2_SHA256), key_len bytes
// (16/24/32), cipher_mode (CIPHER_CBC/ECB/CFB/OFB/CTR). Uploaded once via
// variant_init(); a fixed MAX_VARIANTS-sized __device__ array.
__device__ int g_variant_kdf[MAX_VARIANTS];
__device__ int g_variant_keylen[MAX_VARIANTS];
__device__ int g_variant_mode[MAX_VARIANTS];
__device__ uint32_t g_variant_count;

extern "C" __global__ void variant_init(const int* kdf_kinds, const int* key_lens, const int* modes, uint32_t count) {
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        for (uint32_t i = 0; i < count; i++) {
            g_variant_kdf[i] = kdf_kinds[i];
            g_variant_keylen[i] = key_lens[i];
            g_variant_mode[i] = modes[i];
        }
        g_variant_count = count;
    }
}

// Blob table: salt[8] + ciphertext (padded to MAX_BLOB_CT_LEN) + actual length.
__device__ uint8_t g_blob_salt[MAX_BLOBS][8];
__device__ uint8_t g_blob_ct[MAX_BLOBS][MAX_BLOB_CT_LEN];
__device__ uint32_t g_blob_ct_len[MAX_BLOBS];
__device__ uint32_t g_blob_count;

extern "C" __global__ void blob_init(const uint8_t* salts, const uint8_t* cts,
                                      const uint32_t* ct_lens, uint32_t count) {
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        for (uint32_t b = 0; b < count; b++) {
            for (int i = 0; i < 8; i++) g_blob_salt[b][i] = salts[b*8+i];
            uint32_t len = ct_lens[b];
            for (uint32_t i = 0; i < len; i++) g_blob_ct[b][i] = cts[b*MAX_BLOB_CT_LEN+i];
            g_blob_ct_len[b] = len;
        }
        g_blob_count = count;
    }
}

// Bloom-checks the first two 32-byte chunks (half/better_half) of a
// decrypted buffer as raw private-key material, regardless of what the
// printable/structural gate made of it -- a wrong-looking (non-printable,
// non-full-dummy-pad) body can still happen to BE a real key. Shared by the
// CBC/ECB/SEED_CBC branch (weak/strong/no-hit bodies -- structural hits are
// excluded by the caller, see below) and the stream-mode branch, so there is
// exactly one on-device "raw bytes -> hash160 -> Bloom" code path.
__device__ __forceinline__ void bloom_check_key_chunks(
    const uint8_t* plaintext, uint32_t buf_len, uint32_t idx, uint32_t v, uint32_t b,
    const uint64_t* bloom_bits, uint64_t bloom_m, uint32_t bloom_k,
    StreamKeyHit* stream_hits, uint32_t* stream_hit_count, uint32_t stream_hit_capacity) {
    if (bloom_m == 0) return;
    uint32_t chunk_bound = buf_len < 64u ? buf_len : 64u;
    for (uint32_t chunk_index = 0; chunk_index * 32u + 32u <= chunk_bound; chunk_index++) {
        uint8_t compressed[20], uncompressed[20];
        derive_hash160_both(plaintext + chunk_index * 32u, compressed, uncompressed);
        for (int at = 0; at < 2; at++) {
            const uint8_t* h160 = (at == 0) ? compressed : uncompressed;
            if (bloom_check(bloom_bits, bloom_m, bloom_k, h160)) {
                uint32_t slot = atomicAdd(stream_hit_count, 1);
                if (slot < stream_hit_capacity) {
                    stream_hits[slot].candidate_idx = idx;
                    stream_hits[slot].variant_idx = v;
                    stream_hits[slot].blob_idx = b;
                    stream_hits[slot].chunk_index = chunk_index;
                    stream_hits[slot].address_type = (uint32_t)at;
                    for (int bi = 0; bi < 32; bi++) {
                        stream_hits[slot].private_key[bi] = plaintext[chunk_index * 32u + bi];
                    }
                    for (int bi = 0; bi < 20; bi++) stream_hits[slot].hash160[bi] = h160[bi];
                }
            }
        }
    }
}

// ============================================================================
// Main kernel: one thread per candidate keystring; loops over every
// (variant, blob) pair, exactly mirroring aes_try_open_bytes()'s inner loop.
// ============================================================================

extern "C" __global__ void aes_kdf_scan(
    const uint8_t* candidates,      // flat buffer, MAX_CANDIDATE_LEN bytes per candidate
    const uint32_t* candidate_lens, // actual length of each candidate
    uint32_t candidate_count,
    DecryptHit* hits,
    uint32_t* hit_count,
    uint32_t hit_capacity,
    // Stream-mode (CFB/OFB/CTR) Bloom/API key-shape check -- see
    // secp256k1_device.cuh's derive_hash160_both/bloom_check and the branch
    // below. bloom_m == 0 disables the check entirely (host's
    // --no-bloom-verify or a missing Bloom cache file), matching the
    // structural-hit path's "still derived, never checked" behavior.
    const uint64_t* bloom_bits,
    uint64_t bloom_m,
    uint32_t bloom_k,
    StreamKeyHit* stream_hits,
    uint32_t* stream_hit_count,
    uint32_t stream_hit_capacity
) {
    uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= candidate_count) return;

    const uint8_t* cand = candidates + (size_t)idx * MAX_CANDIDATE_LEN;
    uint32_t cand_len = candidate_lens[idx];
    if (cand_len > MAX_CANDIDATE_LEN) return; // host must guarantee this never happens

    for (uint32_t v = 0; v < g_variant_count; v++) {
        int kdf_kind = g_variant_kdf[v];
        int key_len = g_variant_keylen[v];
        int mode = g_variant_mode[v];
        uint32_t iv_len = (mode == CIPHER_ECB) ? 0 : 16;
        uint32_t material_len = (uint32_t)key_len + iv_len;

        for (uint32_t b = 0; b < g_blob_count; b++) {
            uint8_t material[32 + 16];
            const uint8_t* salt = g_blob_salt[b];

            if (kdf_kind == KDF_PBKDF2_SHA256) {
                pbkdf2_hmac_sha256(cand, cand_len, salt, 8, material, material_len);
            } else {
                evp_bytes_to_key(kdf_kind, cand, cand_len, salt, material, material_len);
            }

            uint8_t key[32];
            uint8_t iv[16];
            for (int i = 0; i < key_len; i++) key[i] = material[i];
            for (uint32_t i = 0; i < iv_len; i++) iv[i] = material[key_len + i];

            int Nk = key_len / 4;
            uint32_t round_keys[60];
            int Nr = 0;
            uint32_t seed_ks[32];
            if (mode == CIPHER_SEED_CBC) {
                seed_set_key(key, seed_ks);
            } else {
                aes_key_expansion(key, Nk, round_keys, &Nr);
            }

            uint32_t ct_len = g_blob_ct_len[b];
            if (ct_len == 0 || ct_len > MAX_BLOB_CT_LEN) continue;

            uint32_t hit_kind = 0;
            float z = 0.0f;

            if (mode == CIPHER_CBC || mode == CIPHER_ECB || mode == CIPHER_SEED_CBC) {
                if (ct_len % 16 != 0) continue;
                uint8_t plaintext[MAX_PLAINTEXT_LEN];
                if (mode == CIPHER_CBC) {
                    aes_cbc_decrypt(round_keys, Nr, iv, g_blob_ct[b], ct_len, plaintext);
                } else if (mode == CIPHER_SEED_CBC) {
                    seed_cbc_decrypt(seed_ks, iv, g_blob_ct[b], ct_len, plaintext);
                } else {
                    aes_ecb_decrypt(round_keys, Nr, g_blob_ct[b], ct_len, plaintext);
                }

                uint32_t body_len;
                if (!pkcs7_check(plaintext, ct_len, &body_len)) continue;
                uint32_t pad = ct_len - body_len;

                if (is_structural_binary_plaintext(pad, body_len)) {
                    hit_kind = 3;
                } else {
                    z = printable_z_score(plaintext, body_len);
                    if (z >= PRINTABLE_Z_STRONG) hit_kind = 2;
                    else if (z >= PRINTABLE_Z_WEAK) hit_kind = 1;

                    // Independent of hit_kind above (including hit_kind==0,
                    // "not even weak"): a PKCS7-valid-but-non-printable,
                    // non-full-dummy-pad body still might BE real key bytes
                    // in the first two 32-byte chunks -- same Bloom check
                    // stream-mode candidates already get unconditionally.
                    // Structural hits (pad==16, hit_kind==3, handled in the
                    // branch above) are deliberately excluded here: they
                    // already get Bloom/API-checked host-side over their
                    // FULL body via keyshape::process_structural_hit, so
                    // this would just be a redundant duplicate check.
                    bloom_check_key_chunks(plaintext, ct_len, idx, v, b, bloom_bits, bloom_m, bloom_k,
                                            stream_hits, stream_hit_count, stream_hit_capacity);
                }
            } else {
                // CFB/OFB/CTR: no padding, whole body goes straight to the
                // printable gate -- matches aes_try_open_stream_bytes exactly
                // (no structural bypass for these modes).
                uint8_t plaintext[MAX_PLAINTEXT_LEN];
                aes_stream_decrypt(round_keys, Nr, iv, mode, g_blob_ct[b], ct_len, plaintext);
                z = printable_z_score(plaintext, ct_len);
                if (z >= PRINTABLE_Z_STRONG) hit_kind = 2;
                else if (z >= PRINTABLE_Z_WEAK) hit_kind = 1;

                // Independent of hit_kind above: raw binary key material
                // will essentially never pass the printable gate, so there's
                // no shared signal between "looks like text" and "looks like
                // a key" -- check the first two 32-byte chunks
                // (half/better_half) against the Bloom filter directly,
                // regardless of what z came out to. A candidate can be BOTH
                // a z-score None and a stream-key Bloom hit at once.
                bloom_check_key_chunks(plaintext, ct_len, idx, v, b, bloom_bits, bloom_m, bloom_k,
                                        stream_hits, stream_hit_count, stream_hit_capacity);
            }

            if (hit_kind != 0) {
                uint32_t slot = atomicAdd(hit_count, 1);
                if (slot < hit_capacity) {
                    hits[slot].candidate_idx = idx;
                    hits[slot].variant_idx = v;
                    hits[slot].blob_idx = b;
                    hits[slot].hit_kind = hit_kind;
                    hits[slot].z_score = z;
                }
            }
        }
    }
}
