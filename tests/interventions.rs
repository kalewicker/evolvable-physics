use causal_alife::{
    experiments, intervention_fixtures as fixtures,
    interventions::*,
    runtime::{self, Matcher},
};

#[test]
fn empty_branch_is_exact_and_sham_has_explicit_provenance() {
    let mut source = experiments::fixture("oscillator", 0).unwrap();
    runtime::step(&mut source, Matcher::Indexed).unwrap();
    let before = source.clone();
    let empty = branch(&source, &Request::new(&source, vec![])).unwrap();
    assert_eq!(empty.experiment, source);
    assert_eq!(empty.receipt.event_id, None);
    let sham = branch(
        &source,
        &Request::new(
            &source,
            vec![Intervention::SetState {
                node: 0,
                expected: 1,
                value: 1,
            }],
        ),
    )
    .unwrap();
    assert_eq!(sham.experiment.world.nodes, source.world.nodes);
    assert_eq!(sham.receipt.parents, vec![0]);
    assert_eq!(sham.receipt.event_id, Some(2));
    let mut out = sham.experiment;
    let frame = runtime::step(&mut out, Matcher::Indexed).unwrap();
    let event = frame
        .events
        .iter()
        .find(|e| e.candidate.binding == vec![0])
        .unwrap();
    assert_eq!(event.parents, vec![2]);
    assert_eq!(source, before);
}
#[test]
fn stale_source_and_invalid_requests_reject_without_changing_source() {
    let source = experiments::fixture("oscillator", 0).unwrap();
    let original = source.clone();
    let valid = Intervention::SetState {
        node: 0,
        expected: 0,
        value: 5,
    };
    let bad = [
        Intervention::SetState {
            node: 99,
            expected: 0,
            value: 1,
        },
        Intervention::SetState {
            node: 0,
            expected: 1,
            value: 9,
        },
        Intervention::MoveResources {
            from: 0,
            to: 0,
            matter: 0,
            activation: 0,
        },
        Intervention::MoveResources {
            from: 0,
            to: 1,
            matter: u64::MAX,
            activation: 0,
        },
        Intervention::MoveResources {
            from: 0,
            to: 99,
            matter: 1,
            activation: 0,
        },
    ];
    for op in bad {
        let req = Request::new(&source, vec![valid.clone(), op]);
        assert!(branch(&source, &req).is_err());
        assert_eq!(source, original);
    }
    let mut req = Request::new(&source, vec![]);
    req.schema = "unknown".into();
    assert_eq!(
        branch(&source, &req).unwrap_err(),
        "unknown_intervention_schema"
    );
    req.schema = SCHEMA.into();
    req.expected_source = "wrong".into();
    assert_eq!(
        branch(&source, &req).unwrap_err(),
        "stale_intervention_source"
    );
    let req = Request::new(&source, vec![valid; 9]);
    assert_eq!(
        branch(&source, &req).unwrap_err(),
        "intervention_operation_limit"
    );
    let request = Request::new(&source, vec![]);
    let mut advanced = source.clone();
    runtime::step(&mut advanced, Matcher::Indexed).unwrap();
    assert_eq!(
        branch(&advanced, &request).unwrap_err(),
        "stale_intervention_source"
    );
    let mut other_laws = source.clone();
    other_laws.rules[0].id = 99;
    assert_eq!(
        branch(&other_laws, &request).unwrap_err(),
        "stale_intervention_source"
    );
}
#[test]
fn resource_moves_conserve_both_ledgers_and_rescue_restores_inventory() {
    let source = experiments::fixture("oscillator", 0).unwrap();
    let b = branch(
        &source,
        &Request::new(
            &source,
            vec![Intervention::MoveResources {
                from: 0,
                to: 1,
                matter: 3,
                activation: 7,
            }],
        ),
    )
    .unwrap();
    b.experiment.validate().unwrap();
    assert_eq!(b.experiment.world.nodes[&0].matter, 5);
    assert_eq!(b.experiment.world.nodes[&1].activation, 15);
    let rescue = branch(
        &b.experiment,
        &Request::new(
            &b.experiment,
            vec![Intervention::MoveResources {
                from: 1,
                to: 0,
                matter: 3,
                activation: 7,
            }],
        ),
    )
    .unwrap();
    assert_eq!(rescue.experiment.world.nodes, source.world.nodes);
    assert_eq!(rescue.receipt.parents, vec![0]);
    assert_eq!(rescue.experiment.world.next_event, 2);
    assert_eq!(rescue.experiment.rules, source.rules);
    assert_eq!(rescue.experiment.world.epoch, source.world.epoch);
    assert_eq!(rescue.experiment.world.next_node, source.world.next_node);
}
#[test]
fn event_overflow_and_unknown_json_fields_are_rejected() {
    let mut source = experiments::fixture("oscillator", 0).unwrap();
    source.world.next_event = u64::MAX;
    let before = source.clone();
    let req = Request::new(
        &source,
        vec![Intervention::SetState {
            node: 0,
            expected: 0,
            value: 1,
        }],
    );
    assert_eq!(branch(&source, &req).unwrap_err(), "intervention_overflow");
    assert_eq!(source, before);
    assert!(branch(&source, &Request::new(&source, vec![])).is_ok());
    let mut json = serde_json::to_value(&req).unwrap();
    json["unexpected"] = 1.into();
    assert!(serde_json::from_value::<Request>(json).is_err());
}
#[test]
fn matched_arms_have_expected_effects_and_rescue_dynamics() {
    let suite = fixtures::suite().unwrap();
    assert_eq!(suite.cases.len(), 32);
    for c in suite.cases {
        assert_eq!(c.arms.len(), 5);
        assert_eq!(c.source.world.nodes[&0], c.source.world.nodes[&2]);
        let baseline = &c.arms[0];
        let full = if c.family == "state_arrest" { 8 } else { 6 };
        for arm in &c.arms {
            let count = |id| {
                arm.frames
                    .iter()
                    .flat_map(|f| &f.events)
                    .filter(|e| e.candidate.binding == vec![id])
                    .count()
            };
            assert_eq!(count(0), if arm.name == "target" { 0 } else { full });
            assert_eq!(count(2), if arm.name == "unrelated" { 0 } else { full });
            if ["sham", "rescue"].contains(&arm.name.as_str()) {
                for (actual, base) in arm.frames.iter().zip(&baseline.frames) {
                    assert_eq!(actual.world.nodes, base.world.nodes);
                    assert_eq!(actual.world.edges, base.world.edges);
                    assert_eq!(actual.world.dissipated, base.world.dissipated);
                    assert_eq!(actual.candidates, base.candidates);
                }
            }
        }
    }
}
