//! Ported from ../../../key-seeker's src/checker/api.rs. Same Blockstream.info
//! REST endpoint the Python `binary_key_material_backfill.verify_pending_queue`
//! already uses (`https://blockstream.info/api/address/{address}`), same
//! funded-txo-sum-over-spent-txo-sum "has balance" rule.

use super::{CheckResult, Checker};
use crate::crypto::hash160_to_address;
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};

const MIN_REQUEST_INTERVAL: Duration = Duration::from_millis(350);
const RATE_LIMIT_BACKOFF: Duration = Duration::from_secs(10);
const MAX_RETRIES: u32 = 3;

/// Checks addresses against the Blockstream.info public API. Thread-safe via
/// an internal mutex on the rate limiter -- ~3 req/sec, meant for verifying
/// the rare Bloom hit, never for scanning candidates directly.
pub struct ApiChecker {
    base_url: String,
    last_request: Mutex<Instant>,
}

impl ApiChecker {
    pub fn new() -> Self {
        Self::new_with_base_url("https://blockstream.info/api/address")
    }

    pub fn new_with_base_url(base_url: &str) -> Self {
        Self {
            base_url: base_url.to_string(),
            last_request: Mutex::new(Instant::now() - MIN_REQUEST_INTERVAL),
        }
    }

    fn rate_limit(&self) {
        let mut last = self.last_request.lock().unwrap();
        let elapsed = last.elapsed();
        if elapsed < MIN_REQUEST_INTERVAL {
            thread::sleep(MIN_REQUEST_INTERVAL - elapsed);
        }
        *last = Instant::now();
    }

    fn has_balance(&self, address: &str) -> Result<bool, String> {
        for attempt in 0..MAX_RETRIES {
            self.rate_limit();

            let url = format!("{}/{address}", self.base_url);
            let resp = ureq::get(&url).timeout(Duration::from_secs(10)).call();

            match resp {
                Ok(r) => {
                    let json: serde_json::Value =
                        r.into_json().map_err(|e| format!("JSON parse error: {e}"))?;

                    let funded = json["chain_stats"]["funded_txo_sum"].as_u64().unwrap_or(0);
                    let spent = json["chain_stats"]["spent_txo_sum"].as_u64().unwrap_or(0);

                    return Ok(funded > spent);
                }
                Err(ureq::Error::Status(429, _)) => {
                    eprintln!("[api] Rate limited, backing off {RATE_LIMIT_BACKOFF:?}...");
                    thread::sleep(RATE_LIMIT_BACKOFF);
                }
                Err(ureq::Error::Status(code, _)) => {
                    return Err(format!("HTTP {code}"));
                }
                Err(e) => {
                    if attempt + 1 < MAX_RETRIES {
                        eprintln!("[api] Network error (attempt {}/{MAX_RETRIES}): {e}", attempt + 1);
                        thread::sleep(Duration::from_secs(2));
                    } else {
                        return Err(format!("Network error: {e}"));
                    }
                }
            }
        }
        Err("Max retries exceeded".into())
    }
}

impl Default for ApiChecker {
    fn default() -> Self {
        Self::new()
    }
}

impl Checker for ApiChecker {
    fn check(&self, hash160: &[u8; 20]) -> CheckResult {
        let address = hash160_to_address(hash160);
        match self.has_balance(&address) {
            Ok(true) => {
                eprintln!("[api] HIT: {address}");
                CheckResult::Hit
            }
            Ok(false) => CheckResult::Miss,
            Err(e) => {
                eprintln!("[api] Error checking {address}: {e}");
                CheckResult::Miss
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockito::Server;

    fn blockstream_json(funded: u64, spent: u64) -> String {
        format!(r#"{{"chain_stats":{{"funded_txo_sum":{funded},"spent_txo_sum":{spent}}}}}"#)
    }

    #[test]
    fn has_balance_true_when_funded() {
        let mut server = Server::new();
        let mock = server
            .mock("GET", "/1TestAddr")
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(blockstream_json(100, 0))
            .create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        let result = checker.has_balance("1TestAddr");
        assert!(result.unwrap(), "funded_txo_sum > spent_txo_sum must return true");
        mock.assert();
    }

    #[test]
    fn has_balance_false_when_zero_net_balance() {
        let mut server = Server::new();
        server
            .mock("GET", "/1TestAddr")
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(blockstream_json(50, 50))
            .create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        assert!(!checker.has_balance("1TestAddr").unwrap());
    }

    #[test]
    fn has_balance_false_when_overspent() {
        let mut server = Server::new();
        server
            .mock("GET", "/1TestAddr")
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(blockstream_json(10, 100))
            .create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        assert!(!checker.has_balance("1TestAddr").unwrap());
    }

    #[test]
    fn has_balance_err_on_http_error() {
        let mut server = Server::new();
        server.mock("GET", "/1TestAddr").with_status(404).create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        let result = checker.has_balance("1TestAddr");
        assert!(result.is_err(), "HTTP 404 must return Err");
        assert!(result.unwrap_err().contains("404"));
    }

    #[test]
    fn check_returns_hit_for_funded_address() {
        let mut server = Server::new();
        server
            .mock("GET", mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(blockstream_json(999, 0))
            .create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        assert!(matches!(checker.check(&[0x42u8; 20]), CheckResult::Hit));
    }

    #[test]
    fn check_returns_miss_for_unfunded_address() {
        let mut server = Server::new();
        server
            .mock("GET", mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(blockstream_json(0, 0))
            .create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        assert!(matches!(checker.check(&[0x43u8; 20]), CheckResult::Miss));
    }

    #[test]
    fn check_returns_miss_on_error() {
        let mut server = Server::new();
        server.mock("GET", mockito::Matcher::Any).with_status(500).create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        assert!(matches!(checker.check(&[0x44u8; 20]), CheckResult::Miss));
    }

    #[test]
    fn two_rapid_requests_trigger_rate_limit_sleep() {
        let mut server = Server::new();
        server
            .mock("GET", mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(blockstream_json(0, 0))
            .expect(2)
            .create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        let _ = checker.has_balance("1AddrA");
        let _ = checker.has_balance("1AddrB");
    }

    #[test]
    #[ignore = "sleeps RATE_LIMIT_BACKOFF (10 s) -- run manually"]
    fn rate_limit_429_retries_and_succeeds() {
        let mut server = Server::new();
        server.mock("GET", mockito::Matcher::Any).with_status(429).create();
        server
            .mock("GET", mockito::Matcher::Any)
            .with_status(200)
            .with_header("content-type", "application/json")
            .with_body(blockstream_json(500, 0))
            .create();

        let checker = ApiChecker::new_with_base_url(&server.url());
        let result = checker.has_balance("1TestAddr");
        assert!(result.unwrap(), "funded after 429 retry must return true");
    }
}
