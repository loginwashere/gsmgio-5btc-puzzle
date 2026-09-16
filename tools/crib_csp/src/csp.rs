//! Faithful port of `phase512d_length_pattern_csp.py`'s MRV/forward-checking
//! exact-crib CSP: `length_patterns`, `build_constraints`,
//! `compatible_assignment`, `solve_length_pattern`, and
//! `search_lengths_at_start`. Every branching decision, tie-break, and node
//! count mirrors the Python reference so outputs can be diffed field-by-field
//! (see `tools/gsmg/phase512i_rust_parity.py`).

use crate::geometry::accepts_token_boundary;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Category {
    Escape,
    NonEscape,
    Any,
}

/// One length pattern: a bitmask over the crib's sorted distinct letters
/// (bit `di` set means `letters[di]` is single-coded). Mirrors Python's
/// `frozenset(values)` from `itertools.combinations(letters, count)`.
pub type PatternMask = u32;

pub struct CribShape {
    pub letters: Vec<char>,          // sorted distinct crib letters
    pub crib_letter_idx: Vec<usize>, // per crib character -> index into `letters`
    pub k: usize,
}

/// One column's constraint list: (row, variable id, category).
type ColumnConstraints = Vec<(usize, usize, Category)>;
/// One candidate assignment for a column: (chunk index, newly-determined (var id, symbol) updates).
type ColumnCandidate = (usize, Vec<(usize, u8)>);

pub fn crib_shape(crib: &str) -> CribShape {
    let mut letters: Vec<char> = crib.chars().collect();
    letters.sort_unstable();
    letters.dedup();
    let k = letters.len();
    let mut lookup = [usize::MAX; 26];
    for (idx, &letter) in letters.iter().enumerate() {
        lookup[(letter as u8 - b'A') as usize] = idx;
    }
    let crib_letter_idx = crib
        .chars()
        .map(|c| lookup[(c as u8 - b'A') as usize])
        .collect();
    CribShape {
        letters,
        crib_letter_idx,
        k,
    }
}

/// Combinations of `0..k` choose `count`, in the same lexicographic index
/// order as Python's `itertools.combinations`, packed as bitmasks.
fn combinations_bitmasks(k: usize, count: usize) -> Vec<PatternMask> {
    let mut result = Vec::new();
    if count == 0 {
        result.push(0);
        return result;
    }
    if count > k {
        return result;
    }
    let mut combo = vec![0usize; count];
    fn rec(
        start: usize,
        k: usize,
        need: usize,
        filled: usize,
        combo: &mut [usize],
        result: &mut Vec<PatternMask>,
    ) {
        if filled == need {
            let mut mask: PatternMask = 0;
            for &idx in combo.iter() {
                mask |= 1 << idx;
            }
            result.push(mask);
            return;
        }
        for idx in start..k {
            combo[filled] = idx;
            rec(idx + 1, k, need, filled + 1, combo, result);
        }
    }
    rec(0, k, count, 0, &mut combo, &mut result);
    result
}

/// Mirrors `phase512d.length_patterns`: counts ordered by closeness to the
/// expected single-code ratio (7/25), combinations within each count in
/// itertools lexicographic order.
pub fn length_patterns(k: usize) -> Vec<PatternMask> {
    let minimum_singles = k.saturating_sub(18);
    let maximum_singles = k.min(7);
    let expected = k as f64 * 7.0 / 25.0;
    let mut counts: Vec<usize> = (minimum_singles..=maximum_singles).collect();
    counts.sort_by(|&a, &b| {
        let da = (a as f64 - expected).abs();
        let db = (b as f64 - expected).abs();
        da.partial_cmp(&db).unwrap().then_with(|| a.cmp(&b))
    });
    let mut patterns = Vec::new();
    for count in counts {
        patterns.extend(combinations_bitmasks(k, count));
    }
    patterns
}

pub fn single_letters_string(mask: PatternMask, letters: &[char]) -> String {
    letters
        .iter()
        .enumerate()
        .filter(|(idx, _)| mask & (1 << idx) != 0)
        .map(|(_, &c)| c)
        .collect()
}

struct VarLayout {
    var_base: Vec<usize>, // len k
    is_single: Vec<bool>, // len k
    var_count: usize,
}

fn var_layout(k: usize, mask: PatternMask) -> VarLayout {
    let mut var_base = vec![0usize; k];
    let mut is_single = vec![false; k];
    let mut next_var = 0usize;
    for di in 0..k {
        let single = mask & (1 << di) != 0;
        is_single[di] = single;
        var_base[di] = next_var;
        next_var += if single { 1 } else { 2 };
    }
    VarLayout {
        var_base,
        is_single,
        var_count: next_var,
    }
}

/// Mirrors `build_constraints`: returns `None` if the pattern's raw span runs
/// past `raw_length` from `raw_start`.
fn build_constraints(
    shape: &CribShape,
    layout: &VarLayout,
    raw_start: usize,
    width: usize,
    raw_length: usize,
) -> Option<(Vec<ColumnConstraints>, usize)> {
    let mut by_column: Vec<ColumnConstraints> = vec![Vec::new(); width];
    let mut position = raw_start;
    for &di in &shape.crib_letter_idx {
        let comps: &[(usize, Category)] = if layout.is_single[di] {
            &[(0, Category::NonEscape)]
        } else {
            &[(0, Category::Escape), (1, Category::Any)]
        };
        for &(component, category) in comps {
            if position >= raw_length {
                return None;
            }
            let column = position % width;
            let row = position / width;
            let var_id = layout.var_base[di] + component;
            by_column[column].push((row, var_id, category));
            position += 1;
        }
    }
    Some((by_column, position))
}

fn completed_all_distinct(assignments: &[i8], layout: &VarLayout, k: usize) -> bool {
    let mut codes: Vec<u16> = Vec::with_capacity(k);
    for di in 0..k {
        let base = layout.var_base[di];
        if layout.is_single[di] {
            if assignments[base] < 0 {
                return false;
            }
            codes.push(assignments[base] as u16);
        } else {
            if assignments[base] < 0 || assignments[base + 1] < 0 {
                return false;
            }
            codes.push(16 + (assignments[base] as u16) * 9 + assignments[base + 1] as u16);
        }
    }
    let mut sorted = codes.clone();
    sorted.sort_unstable();
    !sorted.windows(2).any(|w| w[0] == w[1])
}

fn compatible_assignment(
    constraints: &[(usize, usize, Category)],
    block: &[u8],
    escapes: (u8, u8),
    assignments: &[i8],
    layout: &VarLayout,
    k: usize,
) -> Option<Vec<(usize, u8)>> {
    let mut updates: Vec<(usize, u8)> = Vec::with_capacity(constraints.len());
    for &(row, var_id, category) in constraints {
        let symbol = block[row];
        match category {
            Category::Escape => {
                if symbol != escapes.0 && symbol != escapes.1 {
                    return None;
                }
            }
            Category::NonEscape => {
                if symbol == escapes.0 || symbol == escapes.1 {
                    return None;
                }
            }
            Category::Any => {}
        }
        let existing = updates
            .iter()
            .find(|&&(v, _)| v == var_id)
            .map(|&(_, s)| s)
            .or_else(|| {
                if assignments[var_id] >= 0 {
                    Some(assignments[var_id] as u8)
                } else {
                    None
                }
            });
        match existing {
            Some(e) if e != symbol => return None,
            Some(_) => {}
            None => updates.push((var_id, symbol)),
        }
    }
    let mut probe = assignments.to_vec();
    for &(v, s) in &updates {
        probe[v] = s as i8;
    }
    if !injective_partial(&probe, layout, k) {
        return None;
    }
    Some(updates)
}

fn injective_partial(assignments: &[i8], layout: &VarLayout, k: usize) -> bool {
    let mut codes: Vec<u16> = Vec::with_capacity(k);
    for di in 0..k {
        let base = layout.var_base[di];
        if layout.is_single[di] {
            if assignments[base] >= 0 {
                codes.push(assignments[base] as u16);
            }
        } else if assignments[base] >= 0 && assignments[base + 1] >= 0 {
            codes.push(16 + (assignments[base] as u16) * 9 + assignments[base + 1] as u16);
        }
    }
    let mut sorted = codes.clone();
    sorted.sort_unstable();
    !sorted.windows(2).any(|w| w[0] == w[1])
}

pub struct PatternResult {
    pub nodes: u64,
    pub node_limit_reached: bool,
    pub solution: Option<Vec<i64>>,
}

struct Solver<'a> {
    by_column: Vec<ColumnConstraints>,
    blocks: &'a [Vec<u8>],
    width: usize,
    rows: usize,
    escapes: (u8, u8),
    layout: VarLayout,
    k: usize,
    raw_start: usize,
    node_limit: u64,
    solution_limit: usize,
    assignments: Vec<i8>,
    used: Vec<bool>,
    column_to_chunk: Vec<i64>,
    solutions: Vec<Vec<i64>>,
    nodes: u64,
    limit_reached: bool,
}

impl<'a> Solver<'a> {
    fn candidates_for_column(&self, col: usize) -> Vec<ColumnCandidate> {
        let mut out = Vec::new();
        for chunk in 0..self.width {
            if self.used[chunk] {
                continue;
            }
            if let Some(updates) = compatible_assignment(
                &self.by_column[col],
                &self.blocks[chunk],
                self.escapes,
                &self.assignments,
                &self.layout,
                self.k,
            ) {
                out.push((chunk, updates));
            }
        }
        out
    }

    fn visit(&mut self, remaining: &[usize]) {
        if self.solutions.len() >= self.solution_limit || self.limit_reached {
            return;
        }
        self.nodes += 1;
        if self.nodes > self.node_limit {
            self.limit_reached = true;
            return;
        }
        if remaining.is_empty() {
            if completed_all_distinct(&self.assignments, &self.layout, self.k) {
                let accepted = accepts_token_boundary(
                    &self.column_to_chunk,
                    self.blocks,
                    self.width,
                    self.rows,
                    self.raw_start,
                    self.escapes,
                );
                if accepted {
                    self.solutions.push(self.column_to_chunk.clone());
                }
            }
            return;
        }
        let mut best: Option<(usize, isize, usize, Vec<ColumnCandidate>)> = None;
        for &col in remaining {
            let options = self.candidates_for_column(col);
            if options.is_empty() {
                return;
            }
            let key = (options.len(), -(self.by_column[col].len() as isize), col);
            let better = match &best {
                None => true,
                Some((bl, bneg, bcol, _)) => (key.0, key.1, key.2) < (*bl, *bneg, *bcol),
            };
            if better {
                best = Some((key.0, key.1, key.2, options));
            }
        }
        let (_, _, col, options) = best.expect("remaining is non-empty");
        let next_remaining: Vec<usize> = remaining.iter().copied().filter(|&c| c != col).collect();
        for (chunk, updates) in options {
            let added: Vec<usize> = updates
                .iter()
                .filter(|&&(v, _)| self.assignments[v] < 0)
                .map(|&(v, _)| v)
                .collect();
            for &(v, s) in &updates {
                self.assignments[v] = s as i8;
            }
            self.used[chunk] = true;
            self.column_to_chunk[col] = chunk as i64;
            self.visit(&next_remaining);
            self.column_to_chunk[col] = -1;
            self.used[chunk] = false;
            for &v in &added {
                self.assignments[v] = -1;
            }
            if self.solutions.len() >= self.solution_limit || self.limit_reached {
                return;
            }
        }
    }
}

/// Mirrors `solve_length_pattern` with `solution_limit=1` and the
/// `accepts_token_boundary` acceptor baked in (the only configuration
/// `search_lengths_at_start` ever uses).
#[allow(clippy::too_many_arguments)]
pub fn solve_length_pattern(
    shape: &CribShape,
    mask: PatternMask,
    blocks: &[Vec<u8>],
    width: usize,
    rows: usize,
    escapes: (u8, u8),
    raw_start: usize,
    raw_length: usize,
    node_limit: u64,
) -> PatternResult {
    let layout = var_layout(shape.k, mask);
    let built = build_constraints(shape, &layout, raw_start, width, raw_length);
    let Some((by_column, _raw_end)) = built else {
        return PatternResult {
            nodes: 0,
            node_limit_reached: false,
            solution: None,
        };
    };
    let constrained_columns: Vec<usize> =
        (0..width).filter(|&c| !by_column[c].is_empty()).collect();
    let var_count = layout.var_count.max(1);
    let mut solver = Solver {
        by_column,
        blocks,
        width,
        rows,
        escapes,
        k: shape.k,
        layout,
        raw_start,
        node_limit,
        solution_limit: 1,
        assignments: vec![-1i8; var_count],
        used: vec![false; width],
        column_to_chunk: vec![-1i64; width],
        solutions: Vec::new(),
        nodes: 0,
        limit_reached: false,
    };
    solver.visit(&constrained_columns);
    PatternResult {
        nodes: solver.nodes,
        node_limit_reached: solver.limit_reached,
        solution: solver.solutions.into_iter().next(),
    }
}

pub struct Hit {
    pub pattern_index: usize,
    pub single_letters: String,
    pub column_to_chunk: Vec<i64>,
    pub exact_truth: Option<bool>,
    pub nodes_for_pattern: u64,
}

pub struct CellResult {
    pub legal_length_pattern_count: usize,
    pub patterns_tested: usize,
    pub total_nodes: u64,
    pub node_limit_reached: bool,
    pub search_complete: bool,
    pub hits: Vec<Hit>,
}

/// Mirrors `search_lengths_at_start`: iterate every length pattern, spending
/// the remaining global node budget on each, stopping at the first accepted
/// hit or when the budget is exhausted.
#[allow(clippy::too_many_arguments)]
pub fn search_lengths_at_start(
    shape: &CribShape,
    patterns: &[PatternMask],
    blocks: &[Vec<u8>],
    width: usize,
    rows: usize,
    escapes: (u8, u8),
    raw_start: usize,
    raw_length: usize,
    global_node_limit: u64,
    truth_column_to_chunk: Option<&[i64]>,
) -> CellResult {
    let mut patterns_tested = 0usize;
    let mut total_nodes = 0u64;
    let mut node_limit_reached = false;
    let mut hits = Vec::new();

    for (pattern_index, &mask) in patterns.iter().enumerate() {
        let remaining = global_node_limit.saturating_sub(total_nodes);
        if remaining == 0 {
            node_limit_reached = true;
            break;
        }
        let result = solve_length_pattern(
            shape, mask, blocks, width, rows, escapes, raw_start, raw_length, remaining,
        );
        patterns_tested += 1;
        total_nodes += result.nodes;
        if let Some(solution) = result.solution {
            let exact_truth = truth_column_to_chunk.map(|truth| truth == solution.as_slice());
            hits.push(Hit {
                pattern_index,
                single_letters: single_letters_string(mask, &shape.letters),
                column_to_chunk: solution,
                exact_truth,
                nodes_for_pattern: result.nodes,
            });
            break;
        }
        if result.node_limit_reached {
            node_limit_reached = true;
            break;
        }
    }
    let search_complete = !hits.is_empty() || patterns_tested == patterns.len();
    CellResult {
        legal_length_pattern_count: patterns.len(),
        patterns_tested,
        total_nodes,
        node_limit_reached,
        search_complete,
        hits,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Pure combinatorics, independent of the Python reference: the three
    /// Phase-512 cribs' distinct-letter counts (16/21/22) give
    /// `sum_{i=minimum..=maximum} C(k, i)`, which is exactly the
    /// `legal_length_pattern_count` documented in Phase 512A/G/I
    /// (26,333 / 198,208 / 278,806).
    #[test]
    fn length_patterns_count_matches_known_cribs() {
        assert_eq!(
            length_patterns(16).len(),
            26_333,
            "phase1_credential (k=16)"
        );
        assert_eq!(
            length_patterns(21).len(),
            198_208,
            "phase322_validation_answer (k=21)"
        );
        assert_eq!(
            length_patterns(22).len(),
            278_806,
            "creator_macro_message (k=22)"
        );
    }

    #[test]
    fn length_patterns_orders_counts_by_closeness_to_expected_ratio() {
        // k=16: expected = 16*7/25 = 4.48, so count 4 (|0.48|) must be
        // enumerated strictly before count 0 (|4.48|, the farthest count).
        let patterns = length_patterns(16);
        let first_popcount = patterns[0].count_ones();
        let last_popcount = patterns.last().unwrap().count_ones();
        assert_eq!(first_popcount, 4);
        assert_eq!(last_popcount, 0);
    }

    #[test]
    fn combinations_bitmasks_match_itertools_lexicographic_order() {
        // itertools.combinations(range(4), 2) -> (0,1),(0,2),(0,3),(1,2),(1,3),(2,3)
        let expected: Vec<u32> = vec![0b0011, 0b0101, 0b1001, 0b0110, 0b1010, 0b1100];
        assert_eq!(combinations_bitmasks(4, 2), expected);
    }

    #[test]
    fn combinations_bitmasks_count_zero_yields_empty_mask() {
        assert_eq!(combinations_bitmasks(5, 0), vec![0u32]);
    }

    #[test]
    fn single_letters_string_is_sorted_by_construction() {
        let letters = vec!['A', 'C', 'E', 'F'];
        // bits 0 and 2 set -> 'A' and 'E'
        assert_eq!(single_letters_string(0b0101, &letters), "AE");
    }

    #[test]
    fn crib_shape_maps_repeated_letters_to_the_same_index() {
        let shape = crib_shape("ABA");
        assert_eq!(shape.letters, vec!['A', 'B']);
        assert_eq!(shape.crib_letter_idx, vec![0, 1, 0]);
        assert_eq!(shape.k, 2);
    }
}
