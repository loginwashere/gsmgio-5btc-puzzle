//! Ported verbatim from ../../../key-seeker's src/gpu/gtable.rs -- computes
//! the same 256-entry doubling-of-G table `kernels/secp256k1_brainwallet.cu`'s
//! `gtable_init` kernel expects (see that file's header comment for why the
//! whole secp256k1 kernel was copied rather than hand-ported).

use secp256k1::{PublicKey, Scalar, Secp256k1, SecretKey};

/// Convert a 32-byte big-endian field element to the `[u32; 8]` little-endian word
/// format used by the CUDA kernel's `uint256` (v[0] = least significant word).
pub fn be_bytes_to_words(bytes: &[u8; 32]) -> [u32; 8] {
    let mut words = [0u32; 8];
    for j in 0..8usize {
        // words[0] = LSW = bytes[28..32]; words[7] = MSW = bytes[0..4]
        let b = &bytes[(7 - j) * 4..(7 - j + 1) * 4];
        words[j] = u32::from_be_bytes([b[0], b[1], b[2], b[3]]);
    }
    words
}

/// Compute T[i] = 2^i × G (affine) for i = 0..256.
///
/// Returns `(gtable_x, gtable_y)` as flat `Vec<u32>` of length 256×8 each, in the
/// little-endian word order expected by the CUDA `uint256` type (GTABLE_X[i][j]).
pub fn compute_gtable() -> (Vec<u32>, Vec<u32>) {
    let secp = Secp256k1::new();

    // Scalar 2 for repeated doubling: T[0]=G, T[1]=2G, T[2]=4G, ...
    let mut two_bytes = [0u8; 32];
    two_bytes[31] = 2;
    let two = Scalar::from_be_bytes(two_bytes).expect("2 is a valid scalar");

    // T[0] = G = public key of private key 1
    let mut one = [0u8; 32];
    one[31] = 1;
    let sk = SecretKey::from_slice(&one).expect("key=1 is valid");
    let mut current = PublicKey::from_secret_key(&secp, &sk);

    let mut gtable_x = Vec::with_capacity(256 * 8);
    let mut gtable_y = Vec::with_capacity(256 * 8);

    for _ in 0..256 {
        // serialize_uncompressed: [0x04 | x_be_32 | y_be_32]
        let raw = current.serialize_uncompressed();
        let x_bytes: [u8; 32] = raw[1..33].try_into().unwrap();
        let y_bytes: [u8; 32] = raw[33..65].try_into().unwrap();

        gtable_x.extend_from_slice(&be_bytes_to_words(&x_bytes));
        gtable_y.extend_from_slice(&be_bytes_to_words(&y_bytes));

        // Double: next = 2 × current
        current = current.mul_tweak(&secp, &two).expect("2^i × G is never zero for i < 256");
    }

    (gtable_x, gtable_y)
}

#[cfg(test)]
mod tests {
    use super::*;
    use secp256k1::{PublicKey, Scalar, Secp256k1, SecretKey};

    /// Compute 2^i × G using the secp256k1 library and convert to the CUDA
    /// little-endian word format, so we can cross-check against compute_gtable().
    fn reference_entry(i: usize) -> ([u32; 8], [u32; 8]) {
        let secp = Secp256k1::new();
        let mut one = [0u8; 32];
        one[31] = 1;
        let mut pt = PublicKey::from_secret_key(&secp, &SecretKey::from_slice(&one).unwrap());
        let mut two_bytes = [0u8; 32];
        two_bytes[31] = 2;
        let two = Scalar::from_be_bytes(two_bytes).unwrap();
        for _ in 0..i {
            pt = pt.mul_tweak(&secp, &two).unwrap();
        }
        let raw = pt.serialize_uncompressed();
        let x: [u8; 32] = raw[1..33].try_into().unwrap();
        let y: [u8; 32] = raw[33..65].try_into().unwrap();
        (be_bytes_to_words(&x), be_bytes_to_words(&y))
    }

    #[test]
    fn gtable_entry_0_matches_gx_gy() {
        // CUDA kernel constants (little-endian word order):
        // GX = { 0x16F81798, 0x59F2815B, 0x2DCE28D9, 0x029BFCDB,
        //        0xCE870B07, 0x55A06295, 0xF9DCBBAC, 0x79BE667E }
        // GY = { 0xFB10D4B8, 0x9C47D08F, 0xA6855419, 0xFD17B448,
        //        0x0E1108A8, 0x5DA4FBFC, 0x26A3C465, 0x483ADA77 }
        let (tx, ty) = compute_gtable();
        let gx: [u32; 8] = [
            0x16F81798, 0x59F2815B, 0x2DCE28D9, 0x029BFCDB,
            0xCE870B07, 0x55A06295, 0xF9DCBBAC, 0x79BE667E,
        ];
        let gy: [u32; 8] = [
            0xFB10D4B8, 0x9C47D08F, 0xA6855419, 0xFD17B448,
            0x0E1108A8, 0x5DA4FBFC, 0x26A3C465, 0x483ADA77,
        ];
        assert_eq!(&tx[..8], &gx, "T[0].x should equal G.x");
        assert_eq!(&ty[..8], &gy, "T[0].y should equal G.y");
    }

    #[test]
    fn gtable_has_correct_length() {
        let (tx, ty) = compute_gtable();
        assert_eq!(tx.len(), 256 * 8);
        assert_eq!(ty.len(), 256 * 8);
    }

    /// T3.2 — entries 1 and 2 must be 2G and 4G respectively.
    /// Catches off-by-one errors in the doubling loop: if the loop starts by
    /// doubling before saving, entry 0 would be 2G instead of G, etc.
    #[test]
    fn gtable_entries_1_and_2_are_2g_and_4g() {
        let (tx, ty) = compute_gtable();

        let (ref2g_x, ref2g_y) = reference_entry(1);
        assert_eq!(&tx[8..16], &ref2g_x, "entry 1: x should be 2G.x");
        assert_eq!(&ty[8..16], &ref2g_y, "entry 1: y should be 2G.y");

        let (ref4g_x, ref4g_y) = reference_entry(2);
        assert_eq!(&tx[16..24], &ref4g_x, "entry 2: x should be 4G.x");
        assert_eq!(&ty[16..24], &ref4g_y, "entry 2: y should be 4G.y");
    }
}
