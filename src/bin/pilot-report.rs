//! Offline P01 reporting, separate from frozen P00/P01a implementation.
use causal_alife::{
    core::*,
    environment::{Environment, Epoch},
    environment_analysis,
    pilot::{self, Request},
};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct WorkerResult {
    schema: String,
    status: String,
    epochs: u64,
    events: u64,
    native_events: usize,
    applicable_candidates: usize,
    trace_bytes: u64,
    step_ns: u64,
    serialize_ns: u64,
    write_ns: u64,
    final_state: Environment,
}
fn report(request: &Request, raw: &[u8], summary: &WorkerResult) -> Result<serde_json::Value> {
    if request.schema != "p01-worker-request-v1"
        || request.epochs > 1000
        || summary.schema != "p01-worker-result-v1"
    {
        return Err("report_schema_mismatch".into());
    }
    request.initial.validate()?;
    if !raw.is_empty() && !raw.ends_with(b"\n") {
        return Err("report_partial_record".into());
    }
    let mut frames = Vec::new();
    for line in raw.split_inclusive(|b| *b == b'\n') {
        let frame: Epoch = serde_json::from_slice(line).map_err(|e| e.to_string())?;
        let mut canonical_line = canonical(&frame);
        canonical_line.push(b'\n');
        if canonical_line != line {
            return Err("report_noncanonical_record".into());
        }
        frames.push(frame);
    }
    let current = frames.last().map(|f| &f.state).unwrap_or(&request.initial);
    let native_events: usize = frames.iter().map(|f| f.native_frame.events.len()).sum();
    let candidates: usize = frames.iter().map(|f| f.native_frame.candidates.len()).sum();
    let events = current
        .native
        .world
        .next_event
        .checked_sub(request.initial.native.world.next_event)
        .ok_or("report_event_counter_regressed")?;
    if frames.len() as u64 != summary.epochs
        || frames.len() as u64 > request.epochs
        || events != summary.events
        || events > request.max_events
        || native_events != summary.native_events
        || candidates != summary.applicable_candidates
        || raw.len() as u64 != summary.trace_bytes
        || raw.len() as u64 > request.max_trace_bytes
        || *current != summary.final_state
    {
        return Err("report_accounting_mismatch".into());
    }
    let complete = summary.status == "complete";
    if complete {
        if summary.epochs != request.epochs {
            return Err("report_incomplete_horizon".into());
        }
    } else {
        if summary.epochs >= request.epochs {
            return Err("report_cap_after_horizon".into());
        }
        let mut next = current.clone();
        let actual_stop = match pilot::bounded_step(
            &mut next,
            request.initial.native.world.next_event,
            request.max_events,
        ) {
            Err(reason) => reason,
            Ok(frame) => {
                if canonical(&frame).len() as u64 + 1
                    > request.max_trace_bytes - summary.trace_bytes
                {
                    "trace_budget_exceeded".into()
                } else {
                    return Err("report_unjustified_stop".into());
                }
            }
        };
        if actual_stop != summary.status {
            return Err("report_stop_reason_mismatch".into());
        }
        if ![
            "event_budget_exceeded",
            "trace_budget_exceeded",
            "binding_budget_exceeded",
            "match_budget_exceeded",
            "world_size_exceeded",
        ]
        .contains(&actual_stop.as_str())
        {
            return Err("report_unrecognized_cap".into());
        }
    }
    let detection = environment_analysis::analyze_environment(&request.initial, &frames)?;
    let endpoint = if complete {
        Some(detection.active_persistence.clone())
    } else {
        None
    };
    Ok(serde_json::json!({"schema":"p01-detector-report-v1",
        "request_digest":digest(request),"worker_result_digest":digest(summary),
        "trace_bytes":summary.trace_bytes,"worker_status":summary.status,
        "requested_epochs":request.epochs,"observed_epochs":summary.epochs,
        "coverage":if complete {"complete"} else {"censored_prefix"},
        "full_horizon_ap":endpoint,"prefix_detection":detection,
        "maintenance_status":"not_assessed","scientific_status":"untested"}))
}
fn run() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        return Err("usage: pilot-report REQUEST.json RUN_DIRECTORY".into());
    }
    let request: Request =
        serde_json::from_slice(&std::fs::read(&args[1]).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    let directory = Path::new(&args[2]);
    let raw = std::fs::read(directory.join("trace.jsonl")).map_err(|e| e.to_string())?;
    let summary: WorkerResult = serde_json::from_slice(
        &std::fs::read(directory.join("worker.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    println!(
        "{}",
        String::from_utf8(canonical(&report(&request, &raw, &summary)?)).unwrap()
    );
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
