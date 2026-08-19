//! secp256k1 scalar -> P2PKH address/hash160, ported from
//! ../../../key-seeker's src/crypto/mod.rs (same crate versions: secp256k1,
//! ripemd, bs58) rather than reimplemented, so this project has exactly one
//! Rust implementation of "private key -> Bitcoin address" to trust.
//!
//! Extends key-seeker's compressed-only `privkey_to_address` with the
//! uncompressed form too: `binary_key_material_backfill.py`'s Python
//! reference implementation always derives and Bloom-checks both, and a
//! structural GPU hit's real key could be meant either way.

use ripemd::Ripemd160;
use secp256k1::{PublicKey, Secp256k1, SecretKey};
use sha2::{Digest, Sha256};

pub struct Addresses {
    pub compressed_hash160: [u8; 20],
    pub compressed_address: String,
    pub uncompressed_hash160: [u8; 20],
    pub uncompressed_address: String,
}

pub fn pubkey_to_hash160(pubkey: &PublicKey) -> [u8; 20] {
    let serialized = pubkey.serialize(); // compressed, 33 bytes
    let sha = Sha256::digest(serialized);
    Ripemd160::digest(sha).into()
}

pub fn pubkey_to_hash160_uncompressed(pubkey: &PublicKey) -> [u8; 20] {
    let serialized = pubkey.serialize_uncompressed(); // uncompressed, 65 bytes
    let sha = Sha256::digest(serialized);
    Ripemd160::digest(sha).into()
}

/// hash160 -> Base58Check P2PKH address (mainnet, prefix 0x00)
pub fn hash160_to_address(hash160: &[u8; 20]) -> String {
    let mut payload = [0u8; 25];
    payload[0] = 0x00;
    payload[1..21].copy_from_slice(hash160);
    let first = Sha256::digest(&payload[..21]);
    let second = Sha256::digest(first);
    payload[21..25].copy_from_slice(&second[..4]);
    bs58::encode(payload).into_string()
}

/// Full pipeline: raw 32-byte private key -> both P2PKH address forms.
/// `None` iff `key_bytes` is not a valid secp256k1 scalar (0 or >= curve
/// order) -- the same validity gate `key_shape_classifier.py`'s scalar range
/// check and `private_key_details()` use.
pub fn privkey_to_addresses(secp: &Secp256k1<secp256k1::All>, key_bytes: &[u8; 32]) -> Option<Addresses> {
    let secret = SecretKey::from_slice(key_bytes).ok()?;
    let pubkey = PublicKey::from_secret_key(secp, &secret);
    let compressed_hash160 = pubkey_to_hash160(&pubkey);
    let uncompressed_hash160 = pubkey_to_hash160_uncompressed(&pubkey);
    Some(Addresses {
        compressed_address: hash160_to_address(&compressed_hash160),
        compressed_hash160,
        uncompressed_address: hash160_to_address(&uncompressed_hash160),
        uncompressed_hash160,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn key(n: u128) -> [u8; 32] {
        let mut k = [0u8; 32];
        k[16..32].copy_from_slice(&n.to_be_bytes());
        k
    }

    /// Same known vectors this project's Python side already asserts
    /// (`binary_key_material_backfill.self_test`, `first_hint_hash_audit.self_test`)
    /// and key-seeker's own crypto tests -- three independent implementations
    /// of the same math now agree.
    #[test]
    fn privkey_1_known_addresses() {
        let secp = Secp256k1::new();
        let addrs = privkey_to_addresses(&secp, &key(1)).unwrap();
        assert_eq!(addrs.compressed_address, "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH");
        assert_eq!(addrs.uncompressed_address, "1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm");
    }

    #[test]
    fn privkey_2_known_compressed_address() {
        let secp = Secp256k1::new();
        let addrs = privkey_to_addresses(&secp, &key(2)).unwrap();
        assert_eq!(addrs.compressed_address, "1cMh228HTCiwS8ZsaakH8A8wze1JR5ZsP");
    }

    #[test]
    fn zero_key_is_invalid() {
        let secp = Secp256k1::new();
        assert!(privkey_to_addresses(&secp, &[0u8; 32]).is_none());
    }

    #[test]
    fn hash160_address_roundtrip() {
        let secp = Secp256k1::new();
        let addrs = privkey_to_addresses(&secp, &key(1)).unwrap();
        let decoded = bs58::decode(&addrs.compressed_address).into_vec().unwrap();
        assert_eq!(decoded.len(), 25);
        assert_eq!(decoded[0], 0x00);
        let recovered: [u8; 20] = decoded[1..21].try_into().unwrap();
        assert_eq!(addrs.compressed_hash160, recovered);
    }

    #[test]
    fn hash160_to_address_changes_with_input() {
        let mut h1 = [0u8; 20];
        h1[0] = 0x01;
        let mut h2 = [0u8; 20];
        h2[0] = 0x02;
        assert_ne!(hash160_to_address(&h1), hash160_to_address(&h2));
    }
}
