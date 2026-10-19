use causal_alife::{
    core::digest,
    environment::{self, Action},
    environment_branch_fixtures as fixtures,
    environment_branches::{self, Request},
    interventions::Intervention,
    runtime::Matcher,
};
#[test]
fn full_wrapper_identity_rejects_changed_schedule_with_identical_native_state() {
    let source = fixtures::initial(0).unwrap();
    let request = Request::new(&source, vec![]);
    let mut changed = source.clone();
    changed.channels[0].period = 2;
    assert_eq!(changed.native, source.native);
    assert_eq!(
        environment_branches::branch(&changed, &request).unwrap_err(),
        "stale_environment_intervention_source"
    );
    assert_eq!(
        source,
        environment_branches::branch(&source, &request)
            .unwrap()
            .environment
    );
    let mut changed = source.clone();
    changed.initial_activation += 1;
    changed.extracted += 1;
    changed.validate().unwrap();
    assert!(environment_branches::branch(&changed, &request).is_err());
}
#[test]
fn compound_failure_is_atomic_and_configuration_stays_fixed() {
    let source = fixtures::initial(0).unwrap();
    let before = digest(&source);
    let req = Request::new(
        &source,
        vec![
            Intervention::SetState {
                node: 1,
                expected: 0,
                value: 9,
            },
            Intervention::MoveResources {
                from: 0,
                to: 2,
                matter: u64::MAX,
                activation: 0,
            },
        ],
    );
    assert!(environment_branches::branch(&source, &req).is_err());
    assert_eq!(digest(&source), before);
    let req = Request::new(
        &source,
        vec![Intervention::SetState {
            node: 1,
            expected: 0,
            value: 9,
        }],
    );
    let b = environment_branches::branch(&source, &req).unwrap();
    assert_eq!(b.environment.channels, source.channels);
    assert_eq!(b.environment.injected, source.injected);
    assert_eq!(b.environment.native.rules, source.native.rules);
}
#[test]
fn integrated_controls_preserve_expected_null_and_arrest_results() {
    let suite = fixtures::suite().unwrap();
    assert_eq!(suite.cases.len(), 32);
    for c in suite.cases {
        for a in &c.arms {
            let count = |node| {
                a.epochs
                    .iter()
                    .flat_map(|e| &e.native_frame.events)
                    .filter(|e| e.candidate.binding == vec![node])
                    .count()
            };
            assert_eq!(
                count(1),
                if c.family == "state_arrest" && a.name == "target" {
                    0
                } else {
                    6
                }
            );
            assert_eq!(
                count(4),
                if c.family == "state_arrest" && a.name == "unrelated" {
                    0
                } else {
                    6
                }
            );
            assert_eq!(a.epochs.last().unwrap().state.injected, 32);
            if ["sham", "rescue"].contains(&a.name.as_str()) {
                for (x, y) in a.epochs.iter().zip(&c.arms[0].epochs) {
                    assert_eq!(x.state.native.world.nodes, y.state.native.world.nodes);
                    assert_eq!(x.state.channels, y.state.channels);
                    assert_eq!(x.state.extracted, y.state.extracted);
                }
            }
        }
    }
}
#[test]
fn branch_precedes_environment_phase_without_consuming_it() {
    let source = fixtures::initial(0).unwrap();
    let req = Request::new(
        &source,
        vec![Intervention::SetState {
            node: 0,
            expected: 0,
            value: 0,
        }],
    );
    let b = environment_branches::branch(&source, &req).unwrap();
    assert_eq!(b.environment.native.world.epoch, 0);
    let mut e = b.environment;
    let f = environment::step(&mut e, Matcher::Indexed).unwrap();
    assert!(matches!(source.channels[0].action, Action::Supply { .. }));
    assert_eq!(f.environment_events[0].parents, vec![0]);
    assert_eq!(e.injected, 4);
}
