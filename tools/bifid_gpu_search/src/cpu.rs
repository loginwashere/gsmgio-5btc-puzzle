use sha2::{Digest, Sha256};

pub const ALPHABET: &[u8; 25] = b"ABCDEFGHIKLMNOPQRSTUVWXYZ";
pub const BASE_SQUARE: &[u8; 25] = b"DBIFHCEGAKLMNOPQRSTUVWXYZ";
pub const FREE_SYMBOLS: &[u8; 14] = b"KLMNOPQRUVWXYZ";
pub const FREE_POSITIONS: [u8; 14] = [9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24];
pub const TARGET_PREFIX: &str = "BTCSEED";
pub const FACTORIAL_14: u64 = 87_178_291_200;
pub const EXPECTED_DECODED_SHA256: &str =
    "0c5d984f90e9baefc09f1d3888e62acbd101f9b0194887e2ae88fc6c9967745e";
pub const QUADGRAM_SHA256: &str =
    "b461953d6ad3b5e1f0f07c133102b7656a205529cb8697a8ecda8d45311f7a55";

pub const FAED: &str = concat!(
    "FAEDGGEEDFCBDABHHGGCADCFEDD GFDGBGIGAAEDGGIAFAECGHGGCDAIHEHAHBAHIGCEIFGBFGEFGAIFABIFAGAEGEACGBBEAGFGGEEGGAFBACGFCDBEIFFAAFCIDAHGDEEFGHHCGGAEGDEBHHEGEGHCEGADFBDIAGEFCICGGIFDCGAAGGFBIGAICFBHECAECBCEIAICEBGBGIECDEGGFGEGAEDGGFIICIIIFIFHGGCGFGDCDGGEFCBEEIGEFIBGIBGGGHHFBCGIFDEHEDFDAGICDBHICGAIEDAEHAHGHHCIHDGHF HBIICECBIICHIHIIIGIDDGEHHDFDCHCBAFGFBHAHEAGEGECAFEHGCFGGGGCAGFHHGHBAIHIDIEHHFDEGGDGCIHGGGGGHADAHIGIGBGECGEDFCDGGACCDEHIICIGFBFFH GGAEIDBBEIBBEIIFDGFDHIEEEIEEECIFDGD AHDIGGFHEGFIAFFIGGBCBCEHCEABFBEDBIIBFBFDEDE EHGIGFAAIGGAGBEIICHIEDIFBEHGBCCAHHBIIBIBBIBDCBAHAIDHFAHIIHIC"
);

const QUADGRAM_TEXT: &str = include_str!("../../gsmg/data_files/english_quadgrams.txt");

pub fn normalized_faed() -> Vec<u8> {
    FAED.bytes().filter(|b| b.is_ascii_alphabetic()).collect()
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

pub fn symbol_index(ch: u8) -> Option<u8> {
    ALPHABET
        .iter()
        .position(|&candidate| candidate == ch)
        .map(|i| i as u8)
}

pub fn quad_index(a: u8, b: u8, c: u8, d: u8) -> usize {
    (((a as usize * 25 + b as usize) * 25 + c as usize) * 25) + d as usize
}

#[derive(Clone)]
pub struct QuadgramModel {
    pub logs: Vec<f32>,
    pub floor: f32,
    pub source_sha256: String,
}

impl QuadgramModel {
    pub fn load_embedded() -> Self {
        let source_sha256 = sha256_hex(QUADGRAM_TEXT.as_bytes());
        assert_eq!(
            source_sha256, QUADGRAM_SHA256,
            "quadgram source hash changed"
        );
        let mut parsed = Vec::new();
        let mut total: u64 = 0;
        for line in QUADGRAM_TEXT.lines() {
            let mut parts = line.split_whitespace();
            let gram = parts.next().expect("quadgram missing");
            let count: u64 = parts
                .next()
                .expect("quadgram count missing")
                .parse()
                .expect("bad quadgram count");
            assert!(parts.next().is_none(), "unexpected quadgram columns");
            parsed.push((gram.as_bytes().to_vec(), count));
            total += count;
        }
        let floor = (0.01f64 / total as f64).log10() as f32;
        let mut logs = vec![floor; 25usize.pow(4)];
        for (gram, count) in parsed {
            if gram.len() != 4 {
                continue;
            }
            let Some(a) = symbol_index(gram[0]) else {
                continue;
            };
            let Some(b) = symbol_index(gram[1]) else {
                continue;
            };
            let Some(c) = symbol_index(gram[2]) else {
                continue;
            };
            let Some(d) = symbol_index(gram[3]) else {
                continue;
            };
            logs[quad_index(a, b, c, d)] = (count as f64 / total as f64).log10() as f32;
        }
        Self {
            logs,
            floor,
            source_sha256,
        }
    }
}

pub fn factorials() -> [u64; 15] {
    let mut result = [1u64; 15];
    for i in 1..=14 {
        result[i] = result[i - 1] * i as u64;
    }
    result
}

pub fn unrank_permutation(mut rank: u64) -> [u8; 14] {
    assert!(rank < FACTORIAL_14, "permutation rank out of range");
    let facts = factorials();
    let mut available = [0u8; 14];
    for (i, slot) in available.iter_mut().enumerate() {
        *slot = i as u8;
    }
    let mut available_len = 14usize;
    let mut permutation = [0u8; 14];
    for (position, output) in permutation.iter_mut().enumerate() {
        let remaining = 13 - position;
        let factor = facts[remaining];
        let selected = (rank / factor) as usize;
        rank %= factor;
        assert!(selected < available_len);
        *output = available[selected];
        for i in selected..available_len - 1 {
            available[i] = available[i + 1];
        }
        available_len -= 1;
    }
    permutation
}

pub fn square_for_rank(rank: u64) -> [u8; 25] {
    let permutation = unrank_permutation(rank);
    let mut square = *BASE_SQUARE;
    for i in 0..14 {
        square[FREE_POSITIONS[i] as usize] = FREE_SYMBOLS[permutation[i] as usize];
    }
    square
}

pub fn decoded_cells() -> Vec<u8> {
    let faed = normalized_faed();
    assert_eq!(faed.len(), 570, "FAED length regression");
    let mut positions = [u8::MAX; 25];
    for (cell, &ch) in BASE_SQUARE.iter().enumerate() {
        positions[symbol_index(ch).expect("square contains non-alphabet symbol") as usize] =
            cell as u8;
    }
    let mut coords = Vec::with_capacity(faed.len() * 2);
    for ch in faed {
        let symbol = symbol_index(ch).expect("FAED contains non-Bifid symbol");
        let cell = positions[symbol as usize];
        coords.push(cell / 5);
        coords.push(cell % 5);
    }
    let n = coords.len() / 2;
    (0..n).map(|i| coords[i] * 5 + coords[n + i]).collect()
}

pub fn decode_rank(rank: u64) -> String {
    let square = square_for_rank(rank);
    decoded_cells()
        .into_iter()
        .map(|cell| square[cell as usize] as char)
        .collect()
}

pub fn score_tail(rank: u64, model: &QuadgramModel, tail_cells: &[u8]) -> f32 {
    let square = square_for_rank(rank);
    let mut symbols = Vec::with_capacity(tail_cells.len());
    for &cell in tail_cells {
        symbols.push(symbol_index(square[cell as usize]).expect("square symbol missing"));
    }
    let mut total = 0.0f32;
    for window in symbols.windows(4) {
        total += model.logs[quad_index(window[0], window[1], window[2], window[3])];
    }
    total
}

pub fn score_mean(total: f32, tail_len: usize) -> f64 {
    total as f64 / (tail_len - 3) as f64
}

pub fn validate_contract() {
    let decoded = decode_rank(0);
    assert_eq!(decoded.len(), 570);
    assert!(decoded.starts_with(TARGET_PREFIX));
    assert_eq!(sha256_hex(decoded.as_bytes()), EXPECTED_DECODED_SHA256);
    let cells = decoded_cells();
    assert_eq!(cells.len(), 570);
    for rank in [0, 1, 2, 12_345, FACTORIAL_14 - 1] {
        assert!(
            decode_rank(rank).starts_with(TARGET_PREFIX),
            "rank {rank} broke sealed prefix"
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn contract_reproduces_phase386() {
        validate_contract();
    }

    #[test]
    fn rank_endpoints_are_lexicographic() {
        assert_eq!(
            unrank_permutation(0),
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        );
        assert_eq!(
            unrank_permutation(FACTORIAL_14 - 1),
            [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        );
    }

    #[test]
    fn quadgram_model_is_pinned() {
        let model = QuadgramModel::load_embedded();
        assert_eq!(model.logs.len(), 390_625);
        assert!(model.floor < -8.0);
    }
}
