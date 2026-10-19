use causal_alife::{
    core::*,
    pilot::{self, Request},
};
use std::{
    io::{self, Write},
    time::Instant,
};
fn run() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.get(1).map(String::as_str) == Some("generate") && args.len() == 4 {
        let p = args[2].parse().map_err(|_| "invalid_proposal")?;
        let i = args[3].parse().map_err(|_| "invalid_initial")?;
        println!(
            "{}",
            String::from_utf8(canonical(&pilot::generate(p, i)?)).unwrap()
        );
        return Ok(());
    }
    if args.get(1).map(String::as_str) != Some("run") || args.len() != 3 {
        return Err("usage: pilot-worker generate PROPOSAL INITIAL | run REQUEST.json".into());
    }
    let request: Request =
        serde_json::from_slice(&std::fs::read(&args[2]).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    if request.schema != "p01-worker-request-v1" || request.epochs > 1000 {
        return Err("invalid_request".into());
    }
    request.initial.validate()?;
    let mut state = request.initial;
    let start_event = state.native.world.next_event;
    let mut bytes = 0;
    let mut epochs = 0;
    let mut candidates = 0;
    let mut native_events = 0;
    let mut step_ns = 0;
    let mut serialize_ns = 0;
    let mut write_ns = 0;
    let mut status = "complete".to_string();
    let mut stdout = io::stdout().lock();
    for _ in 0..request.epochs {
        let mut staged = state.clone();
        let clock = Instant::now();
        let outcome = pilot::bounded_step(&mut staged, start_event, request.max_events);
        step_ns += clock.elapsed().as_nanos();
        let frame = match outcome {
            Ok(f) => f,
            Err(e) => {
                status = e;
                break;
            }
        };
        let clock = Instant::now();
        let mut record = canonical(&frame);
        record.push(b'\n');
        serialize_ns += clock.elapsed().as_nanos();
        if record.len() as u64 > request.max_trace_bytes.saturating_sub(bytes) {
            status = "trace_budget_exceeded".into();
            break;
        }
        let clock = Instant::now();
        stdout.write_all(&record).map_err(|e| e.to_string())?;
        stdout.flush().map_err(|e| e.to_string())?;
        write_ns += clock.elapsed().as_nanos();
        bytes += record.len() as u64;
        epochs += 1;
        candidates += frame.native_frame.candidates.len();
        native_events += frame.native_frame.events.len();
        state = staged;
    }
    // Summary goes to a different stream; capped or killed traces are never presented as complete.
    let summary = serde_json::json!({"schema":"p01-worker-result-v1", "status":status,
        "epochs":epochs,"events":state.native.world.next_event-start_event,"native_events":native_events,
        "applicable_candidates":candidates,"trace_bytes":bytes,"step_ns":step_ns,
        "serialize_ns":serialize_ns,"write_ns":write_ns,"final_state":state});
    eprintln!("{}", String::from_utf8(canonical(&summary)).unwrap());
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
