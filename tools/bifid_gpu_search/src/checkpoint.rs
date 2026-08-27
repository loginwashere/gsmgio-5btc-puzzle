use serde::{Deserialize, Serialize};
use std::fs;
use std::io;
use std::path::PathBuf;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Fingerprint {
    pub version: u32,
    pub family: String,
    pub range_end_exclusive: u64,
    pub faed_sha256: String,
    pub decoded_cells_sha256: String,
    pub quadgram_sha256: String,
    pub kernel_sha256: String,
    pub driver_sha256: String,
    pub cuda_arch: String,
    pub score: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Winner {
    pub rank: u64,
    pub score_total: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct State {
    pub fingerprint: Fingerprint,
    pub next_rank: u64,
    pub block_winners: Vec<Winner>,
}

pub struct Checkpoint {
    path: PathBuf,
}

impl Checkpoint {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self { path: path.into() }
    }

    pub fn load(&self, expected: &Fingerprint) -> io::Result<Option<State>> {
        if !self.path.exists() {
            return Ok(None);
        }
        let raw = fs::read(&self.path)?;
        let state: State = serde_json::from_slice(&raw)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
        if &state.fingerprint != expected {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                format!(
                    "checkpoint fingerprint mismatch; refusing resume\nstored: {:?}\nexpected: {:?}",
                    state.fingerprint, expected
                ),
            ));
        }
        Ok(Some(state))
    }

    pub fn save(&self, state: &State) -> io::Result<()> {
        if let Some(parent) = self.path.parent() {
            if !parent.as_os_str().is_empty() {
                fs::create_dir_all(parent)?;
            }
        }
        let temporary = self.path.with_extension("tmp");
        let bytes = serde_json::to_vec_pretty(state)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
        fs::write(&temporary, bytes)?;
        fs::rename(&temporary, &self.path)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fingerprint(label: &str) -> Fingerprint {
        Fingerprint {
            version: 1,
            family: label.into(),
            range_end_exclusive: 10,
            faed_sha256: "a".into(),
            decoded_cells_sha256: "b".into(),
            quadgram_sha256: "c".into(),
            kernel_sha256: "d".into(),
            driver_sha256: "e".into(),
            cuda_arch: "sm_120".into(),
            score: "quadgram".into(),
        }
    }

    #[test]
    fn atomic_roundtrip_and_mismatch_gate() {
        let directory = tempfile::tempdir().unwrap();
        let checkpoint = Checkpoint::new(directory.path().join("state.json"));
        let state = State {
            fingerprint: fingerprint("one"),
            next_rank: 7,
            block_winners: vec![],
        };
        checkpoint.save(&state).unwrap();
        assert_eq!(
            checkpoint
                .load(&state.fingerprint)
                .unwrap()
                .unwrap()
                .next_rank,
            7
        );
        assert!(checkpoint.load(&fingerprint("two")).is_err());
        assert!(!checkpoint.path.with_extension("tmp").exists());
    }
}
