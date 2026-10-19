//! Positive-prefix censoring regression using an already registered driven fixture.
use causal_alife::{core::*, environment, integration_fixtures, pilot::Request, runtime::Matcher};
use std::{
    fs,
    process::{Command, Stdio},
    time::{SystemTime, UNIX_EPOCH},
};

#[test]
fn supported_cap_prefix_never_becomes_a_full_horizon_endpoint() {
    let initial = integration_fixtures::initial("driven_pair", 0).unwrap();
    let mut expected = initial.clone();
    for _ in 0..12 {
        environment::step(&mut expected, Matcher::Reference).unwrap();
    }
    let request = Request {
        schema: "p01-worker-request-v1".into(),
        initial: initial.clone(),
        epochs: 13,
        max_events: expected.native.world.next_event - initial.native.world.next_event,
        max_trace_bytes: 32 * 1024 * 1024,
    };
    let unique = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!(
        "p01-positive-prefix-{}-{unique}",
        std::process::id()
    ));
    fs::create_dir(&dir).unwrap();
    let path = dir.join("request.json");
    fs::write(&path, canonical(&request)).unwrap();
    let status = Command::new(env!("CARGO_BIN_EXE_pilot-worker"))
        .arg("run")
        .arg(&path)
        .stdout(Stdio::from(
            fs::File::create(dir.join("trace.jsonl")).unwrap(),
        ))
        .stderr(Stdio::from(
            fs::File::create(dir.join("worker.json")).unwrap(),
        ))
        .status()
        .unwrap();
    assert!(status.success());
    let output = Command::new(env!("CARGO_BIN_EXE_pilot-report"))
        .arg(path)
        .arg(&dir)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["worker_status"], "event_budget_exceeded");
    assert_eq!(report["observed_epochs"], 12);
    assert_eq!(
        report["prefix_detection"]["active_persistence"],
        "supported"
    );
    assert_eq!(report["coverage"], "censored_prefix");
    assert!(report["full_horizon_ap"].is_null());
    fs::remove_dir_all(dir).unwrap();
}
