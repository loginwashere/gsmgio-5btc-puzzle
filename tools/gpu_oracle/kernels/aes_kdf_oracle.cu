// GSMG.IO puzzle AES/KDF oracle -- CUDA port of tools/gsmg/cb_common.py's
// aes_try_open_bytes() (legacy EVP_BytesToKey + PBKDF2-HMAC-SHA256 KDFs,
// AES-128/192/256-CBC decrypt, PKCS7 + printable-z-score gate).
//
// Phase 1 scope only: AES-CBC across {legacy-MD5, legacy-SHA1, legacy-SHA256,
// PBKDF2-SHA256/10000} x {128,192,256}-bit keys. ECB/CFB/OFB/CTR, 3DES/
// Blowfish/Camellia/SEED, and AES Key-Wrap are deliberately out of scope --
// see doc/ plan notes. Every constant/threshold here must match cb_common.py
// bit-for-bit; see selftest.rs / cpu_oracle.rs for the cross-check harness
// that verifies that.

#include <stdint.h>

// ---------------------------------------------------------------------------
// Fixed sizing. Candidate passphrases (raw form, or the hex digests keystr_forms
// produces) are always well under this in practice -- the 7-fragment creator
// concatenation sweep tops out around 280 bytes.
// ---------------------------------------------------------------------------
#define MAX_CANDIDATE_LEN 512
#define MAX_BLOB_CT_LEN 2432   // PHASE32_SELFTEST (2432) > COSMIC (1328, the largest of the 4 tracked blobs)
#define MAX_BLOBS 4
#define MAX_VARIANTS 12        // 4 KDF kinds x 3 key sizes (Phase 1 scope)
#define MAX_PLAINTEXT_LEN MAX_BLOB_CT_LEN

#define KDF_LEGACY_MD5 0
#define KDF_LEGACY_SHA1 1
#define KDF_LEGACY_SHA256 2
#define KDF_PBKDF2_SHA256 3

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

// SALPH/P32TRAILING's known structural-hit shape: aes/block16/pad16/body64.
__device__ int is_structural_binary_plaintext(uint32_t pad, uint32_t body_len) {
    return pad == 16 && body_len == 64;
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

// Variant table: kdf_kind (KDF_LEGACY_* / KDF_PBKDF2_SHA256), key_len bytes (16/24/32).
// Uploaded once via variant_init(); a fixed MAX_VARIANTS-sized __device__ array.
__device__ int g_variant_kdf[MAX_VARIANTS];
__device__ int g_variant_keylen[MAX_VARIANTS];
__device__ uint32_t g_variant_count;

extern "C" __global__ void variant_init(const int* kdf_kinds, const int* key_lens, uint32_t count) {
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        for (uint32_t i = 0; i < count; i++) {
            g_variant_kdf[i] = kdf_kinds[i];
            g_variant_keylen[i] = key_lens[i];
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
    uint32_t hit_capacity
) {
    uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= candidate_count) return;

    const uint8_t* cand = candidates + (size_t)idx * MAX_CANDIDATE_LEN;
    uint32_t cand_len = candidate_lens[idx];
    if (cand_len > MAX_CANDIDATE_LEN) return; // host must guarantee this never happens

    for (uint32_t v = 0; v < g_variant_count; v++) {
        int kdf_kind = g_variant_kdf[v];
        int key_len = g_variant_keylen[v];
        uint32_t material_len = (uint32_t)key_len + 16; // + IV (AES block size)

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
            for (int i = 0; i < 16; i++) iv[i] = material[key_len + i];

            int Nk = key_len / 4;
            uint32_t round_keys[60];
            int Nr;
            aes_key_expansion(key, Nk, round_keys, &Nr);

            uint32_t ct_len = g_blob_ct_len[b];
            if (ct_len == 0 || ct_len % 16 != 0 || ct_len > MAX_BLOB_CT_LEN) continue;

            uint8_t plaintext[MAX_PLAINTEXT_LEN];
            aes_cbc_decrypt(round_keys, Nr, iv, g_blob_ct[b], ct_len, plaintext);

            uint32_t body_len;
            if (!pkcs7_check(plaintext, ct_len, &body_len)) continue;
            uint32_t pad = ct_len - body_len;

            uint32_t hit_kind = 0;
            float z = 0.0f;
            if (is_structural_binary_plaintext(pad, body_len)) {
                hit_kind = 3;
            } else {
                z = printable_z_score(plaintext, body_len);
                if (z >= PRINTABLE_Z_STRONG) hit_kind = 2;
                else if (z >= PRINTABLE_Z_WEAK) hit_kind = 1;
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
