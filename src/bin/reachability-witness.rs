//! Fixed authored P01f panel. No generator, search, repair or retry path.
use causal_alife::{
    analysis,
    core::*,
    environment::{self, Environment},
    environment_analysis,
    runtime::{self, Matcher},
};
use serde_json::{Value, json};
use std::io::{self, Write};

fn measure(initial: &Environment, horizon: u64, matcher: Matcher) -> Result<Value> {
    initial.validate()?;
    let mut state = initial.clone();
    let mut frames = vec![];
    let mut failures = vec![];
    for attempt in 0..horizon {
        let before = state.clone();
        // Retain applicable candidates even when whole-epoch publication fails.
        let candidates = match runtime::enumerate(&before.native, matcher) {
            Ok(value) => json!(value),
            Err(error) => json!({"enumeration_error":error}),
        };
        match environment::step(&mut state, matcher) {
            Ok(frame) => frames.push(frame),
            Err(error) => {
                failures.push(json!({"attempt":attempt,"error":error,
                    "before":before,"after":state,"candidates":candidates}));
                break;
            }
        }
    }
    // Frozen observers replay the recorded prefix; these are validation replays,
    // not additional sampled worlds or independent experimental cases.
    let detection = match environment_analysis::analyze_environment(initial, &frames) {
        Ok(value) => json!(value),
        Err(error) => json!({"observer_error":error}),
    };
    let mut activities = vec![];
    for frame in &frames {
        let activity = match analysis::event_activity(
            &frame.prepared,
            std::slice::from_ref(&frame.native_frame),
        ) {
            Ok(value) => json!(value.into_iter().next()),
            Err(error) => json!({"observer_error":error}),
        };
        activities.push(activity);
    }
    Ok(
        json!({"frames":frames,"failures":failures,"final_state":state,
        "detection":detection,"activities":activities}),
    )
}

fn run() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        return Err("usage: reachability-witness PROTOCOL.json REGISTRY.json".into());
    }
    let read = |p: &str| -> Result<Value> {
        serde_json::from_slice(&std::fs::read(p).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())
    };
    let protocol = read(&args[1])?;
    let registry = read(&args[2])?;
    if protocol["schema"] != "p01f-reachability-registration-v1"
        || registry["schema"] != "p01f-reachability-witnesses-v1"
        || protocol["scheduler_seeds"] != json!([0, 1, 2, 3])
        || protocol["denominator"] != 48
    {
        return Err("invalid_registration".into());
    }
    let families = registry["families"].as_array().ok_or("families")?;
    if families.len() != 12 {
        return Err("family_census".into());
    }
    let mut stdout = io::stdout().lock();
    let mut slot = 0;
    for (index, family) in families.iter().enumerate() {
        if family["id"] != protocol["family_order"][index] {
            return Err("family_order".into());
        }
        let horizon = family["attempted_epochs"].as_u64().ok_or("horizon")?;
        if !(1..=8).contains(&horizon) {
            return Err("horizon".into());
        }
        for seed in 0..4 {
            let mut initial: Environment =
                serde_json::from_value(family["initial"].clone()).map_err(|e| e.to_string())?;
            initial.native.seed = seed;
            // Unexpected matcher/observer errors remain in their slot. Continue the
            // fixed denominator without substituting cases or suppressing failures.
            let mut results = serde_json::Map::new();
            for (name, matcher) in [
                ("Reference", Matcher::Reference),
                ("Indexed", Matcher::Indexed),
            ] {
                let value = match measure(&initial, horizon, matcher) {
                    Ok(value) => value,
                    Err(error) => json!({"runner_error":error}),
                };
                results.insert(name.into(), value);
            }
            let row = json!({"schema":"p01f-witness-slot-v1","slot":slot,
                "family":family["id"],"seed":seed,"initial":initial,"results":results});
            stdout
                .write_all(&canonical(&row))
                .map_err(|e| e.to_string())?;
            stdout.write_all(b"\n").map_err(|e| e.to_string())?;
            stdout.flush().map_err(|e| e.to_string())?;
            slot += 1;
        }
    }
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
