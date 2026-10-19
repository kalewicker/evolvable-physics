use causal_alife::{
    analysis, environment, environment_analysis, environment_fixtures, experiments,
    integration_fixtures as fixtures,
    runtime::{self, Matcher, TraceMode},
};
#[test]
fn logging_modes_preserve_atomic_failures_and_entire_state() {
    for matcher in [Matcher::Reference, Matcher::Indexed] {
        for cap in ["matches", "bindings", "nodes", "edges", "epoch"] {
            let mut source = experiments::fixture("growth_recycling", 0).unwrap();
            match cap {
                "matches" => source.limits.max_candidates = 0,
                "bindings" => source.limits.max_bindings = 0,
                "nodes" => source.limits.max_nodes = 3,
                "edges" => source.limits.max_edges = 2,
                _ => source.world.epoch = u64::MAX,
            }
            let mut full = source.clone();
            let mut disabled = source.clone();
            let a = runtime::step_with_logging(&mut full, matcher, TraceMode::Full);
            let b = runtime::step_with_logging(&mut disabled, matcher, TraceMode::Disabled);
            assert!(a.is_err());
            assert_eq!(a, b);
            assert_eq!(full, source);
            assert_eq!(disabled, source);
        }
    }
    for failure in ["budget", "overflow", "counter"] {
        let mut source = fixtures::initial("driven_pair", 0).unwrap();
        match failure {
            "budget" => source.native.limits.max_bindings = 0,
            "overflow" => source.native.world.next_event = u64::MAX,
            _ => source.native.world.epoch = u64::MAX,
        }
        let mut full = source.clone();
        let mut disabled = source.clone();
        let a = environment::step_with_logging(&mut full, Matcher::Indexed, TraceMode::Full);
        let b =
            environment::step_with_logging(&mut disabled, Matcher::Indexed, TraceMode::Disabled);
        assert!(a.is_err());
        assert_eq!(a, b);
        assert_eq!(full, source);
        assert_eq!(disabled, source);
    }
}
#[test]
fn environment_activity_is_native_only_and_controls_are_registered() {
    for family in fixtures::protocol().families.keys() {
        let source = fixtures::initial(family, 0).unwrap();
        let mut e = source.clone();
        let mut quiet = source.clone();
        let mut epochs = vec![];
        for _ in 0..12 {
            epochs.push(environment::step(&mut e, Matcher::Indexed).unwrap());
            assert!(
                environment::step_with_logging(&mut quiet, Matcher::Indexed, TraceMode::Disabled)
                    .unwrap()
                    .is_none()
            );
            assert_eq!(e, quiet);
        }
        let d = environment_analysis::analyze_environment(&source, &epochs).unwrap();
        assert_eq!(
            d.active_persistence,
            fixtures::protocol().families[family].expected_ap,
            "{family}"
        );
        let count: usize = epochs.iter().map(|e| e.native_frame.events.len()).sum();
        assert_eq!(
            count,
            fixtures::protocol().families[family].expected_native_events
        );
        if ["external_flux", "no_op_pair"].contains(&family.as_str()) {
            assert!(
                d.connected
                    .tracks
                    .iter()
                    .all(|t| t.active_members.is_empty())
            );
            assert!(d.interaction.tracks.is_empty());
        }
        if family == "mixed_islands" {
            assert!(
                d.connected
                    .tracks
                    .iter()
                    .filter(|t| t.members.contains(&5))
                    .all(|t| !t.active_persistence && t.active_members.is_empty())
            );
        }
        let mut corrupt = epochs.clone();
        corrupt[0]
            .prepared
            .world
            .nodes
            .values_mut()
            .next()
            .unwrap()
            .state = 100;
        assert_eq!(
            environment_analysis::analyze_environment(&source, &corrupt).unwrap_err(),
            "analysis_environment_trace_mismatch"
        );
        let mut corrupt = epochs.clone();
        corrupt[0].environment_events.clear();
        assert_eq!(
            environment_analysis::analyze_environment(&source, &corrupt).unwrap_err(),
            "analysis_environment_trace_mismatch"
        );
    }
}
#[test]
fn new_observation_engine_matches_frozen_native_detector() {
    for family in [
        "active_pair",
        "renewal",
        "passive_turnover",
        "attached_inert",
    ] {
        let source = causal_alife::detector_fixtures::initial(family, 3).unwrap();
        let mut e = source.clone();
        let mut frames = vec![];
        for _ in 0..12 {
            frames.push(runtime::step(&mut e, Matcher::Indexed).unwrap());
        }
        assert_eq!(
            environment_analysis::analyze_native(&source, &frames).unwrap(),
            analysis::analyze(&source, &frames).unwrap()
        );
    }
    assert_eq!(
        environment_analysis::observations(&[], &[]).unwrap_err(),
        "analysis_observation_length"
    );
}
#[test]
fn disabled_mode_continuation_can_resume_full_logging() {
    let mut full = environment_fixtures::fixture("driven", 4).unwrap();
    let mut quiet = full.clone();
    for _ in 0..5 {
        environment::step(&mut full, Matcher::Indexed).unwrap();
        environment::step_with_logging(&mut quiet, Matcher::Indexed, TraceMode::Disabled).unwrap();
    }
    assert_eq!(full, quiet);
    for _ in 0..5 {
        assert_eq!(
            environment::step(&mut full, Matcher::Indexed).unwrap(),
            environment::step(&mut quiet, Matcher::Reference).unwrap()
        );
    }
}
