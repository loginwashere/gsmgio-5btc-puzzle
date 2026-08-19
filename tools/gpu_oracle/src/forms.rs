//! Bit-for-bit port of cb_common.py's `answer_forms()` / `keystr_forms()`.

use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

/// answer_forms(s): {s, s.upper(), s.lower(), alpha_only, alpha_only.upper(), alpha_only.lower()}
/// Python's `re.sub(r"[^A-Za-z]", "", s)` -- keep only ASCII letters.
pub fn answer_forms(s: &str) -> BTreeSet<String> {
    let alpha: String = s.chars().filter(|c| c.is_ascii_alphabetic()).collect();
    let mut out = BTreeSet::new();
    out.insert(s.to_string());
    out.insert(s.to_uppercase());
    out.insert(s.to_lowercase());
    out.insert(alpha.clone());
    out.insert(alpha.to_uppercase());
    out.insert(alpha.to_lowercase());
    out
}

fn sha256_hex(s: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(s.as_bytes());
    hex::encode(hasher.finalize())
}

/// keystr_forms(form, newline_variants, whitespace_variants): for each base
/// (form, optionally +"\n", +"\r\n", +" "), emits (base, sha256_hex(base),
/// sha256_hex(sha256_hex(base))) -- the second hash is over the *hex string*
/// of the first, not the raw digest bytes.
pub fn keystr_forms(form: &str, newline_variants: bool, whitespace_variants: bool) -> Vec<String> {
    let mut bases = vec![form.to_string()];
    if newline_variants {
        bases.push(format!("{form}\n"));
        bases.push(format!("{form}\r\n"));
    }
    if whitespace_variants {
        bases.push(format!("{form} "));
    }

    let mut out = Vec::with_capacity(bases.len() * 3);
    for b in bases {
        let h1 = sha256_hex(&b);
        let h2 = sha256_hex(&h1);
        out.push(b);
        out.push(h1);
        out.push(h2);
    }
    out
}

/// Full expansion of one base candidate string into the passphrase forms
/// actually fed to the KDF, matching this project's default sweep behavior
/// (answer_forms x keystr_forms). Deduplicates across answer_forms entries.
pub fn expand_candidate(base: &str, newline_variants: bool, whitespace_variants: bool) -> Vec<String> {
    let mut seen = BTreeSet::new();
    let mut out = Vec::new();
    for form in answer_forms(base) {
        for keystr in keystr_forms(&form, newline_variants, whitespace_variants) {
            if seen.insert(keystr.clone()) {
                out.push(keystr);
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn answer_forms_dedupes_alpha_only_input() {
        // "matrixsumlist" is already pure lowercase alpha, so alpha == s and
        // the set collapses to {s, S_upper} = 2 entries, not 6.
        let f = answer_forms("matrixsumlist");
        assert_eq!(f.len(), 2);
        assert!(f.contains("matrixsumlist"));
        assert!(f.contains("MATRIXSUMLIST"));
    }

    #[test]
    fn keystr_forms_default_is_three() {
        let k = keystr_forms("promised", false, false);
        assert_eq!(k.len(), 3);
        assert_eq!(k[0], "promised");
        assert_eq!(k[1], sha256_hex("promised"));
        assert_eq!(k[2], sha256_hex(&sha256_hex("promised")));
    }

    #[test]
    fn keystr_forms_newline_variants_is_nine() {
        let k = keystr_forms("promised", true, false);
        assert_eq!(k.len(), 9);
    }

    #[test]
    fn keystr_forms_both_flags_is_twelve() {
        let k = keystr_forms("promised", true, true);
        assert_eq!(k.len(), 12);
    }

    #[test]
    fn double_sha256_hashes_the_hex_string_not_raw_bytes() {
        // Regression guard for the documented subtlety: h2 = sha256(h1_hex.encode()),
        // NOT sha256(sha256(base).digest()).
        let base = "x";
        let h1 = sha256_hex(base);
        let h2_correct = sha256_hex(&h1);

        let mut hasher = Sha256::new();
        hasher.update(base.as_bytes());
        let raw1 = hasher.finalize();
        let mut hasher2 = Sha256::new();
        hasher2.update(&raw1[..]);
        let h2_wrong = hex::encode(hasher2.finalize());

        assert_ne!(h2_correct, h2_wrong, "double-hash must be over the hex string");
    }
}
