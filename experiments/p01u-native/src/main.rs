use causal_alife::{core::{canonical, digest}, pilot::Request};
use sha2::{Digest, Sha256};
use std::io::{self, Read, Write};

fn validate_bytes(bytes: &[u8]) -> serde_json::Value {
    let input_sha256 = format!("{:x}", Sha256::digest(bytes));
    let request: Request = match serde_json::from_slice(bytes) {
        Ok(value) => value,
        Err(error) => return serde_json::json!({
            "schema": "p01u-validation-result-v1", "accepted": false,
            "rejection_stage": "parse", "error": error.to_string(),
            "input_sha256": input_sha256, "roundtrip_request": null,
            "request_before_sha256": null, "request_after_sha256": null,
            "world_before_sha256": null, "world_after_sha256": null
        }),
    };
    let request_before = digest(&request);
    let world_before = digest(&request.initial.native.world);
    let (stage, error) = if request.schema != "p01-worker-request-v1" || request.epochs > 1000 {
        (Some("worker_prefix"), Some("invalid_request".to_string()))
    } else {
        match request.initial.validate() {
            Ok(()) => (None, None),
            Err(error) => (Some("initial_validate"), Some(error)),
        }
    };
    serde_json::json!({
        "schema": "p01u-validation-result-v1", "accepted": stage.is_none(),
        "rejection_stage": stage, "error": error, "input_sha256": input_sha256,
        "roundtrip_request": request,
        "request_before_sha256": request_before, "request_after_sha256": digest(&request),
        "world_before_sha256": world_before,
        "world_after_sha256": digest(&request.initial.native.world)
    })
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut bytes = Vec::new();
    io::stdin().lock().take(524288).read_to_end(&mut bytes)?;
    if bytes.len() >= 524288 {
        return Err("input_limit".into());
    }
    let mut output = canonical(&validate_bytes(&bytes));
    output.push(b'\n');
    io::stdout().lock().write_all(&output)?;
    Ok(())
}
