use causal_alife::{
    environment::{self, Action, Channel},
    environment_fixtures as fixtures,
    runtime::{self, Matcher},
};
#[test]
fn registered_controls_and_exact_ledgers() {
    let suite = fixtures::suite().unwrap();
    assert_eq!(suite.cases.len(), 64);
    for case in suite.cases {
        let e = &case.epochs.last().unwrap().state;
        let n: usize = case
            .epochs
            .iter()
            .map(|f| f.native_frame.events.len())
            .sum();
        assert_eq!(
            n,
            match case.mode.as_str() {
                "driven" => 8,
                "local_transport" => 2,
                _ => 0,
            }
        );
        assert_eq!(e.native.world.nodes[&3].activation, 0);
        assert_eq!(e.native.world.nodes[&3].state, 0);
        assert_eq!(
            e.injected,
            if ["driven", "blocked"].contains(&case.mode.as_str()) {
                16
            } else {
                0
            }
        );
        assert_eq!(e.extracted, if case.mode == "driven" { 8 } else { 0 });
        assert_eq!(
            e.native.world.nodes[&2].matter,
            if ["driven", "local_transport"].contains(&case.mode.as_str()) {
                3
            } else {
                0
            }
        );
    }
}
#[test]
fn closed_wrapper_preserves_native_trace_and_storage_order_does_not_matter() {
    let mut a = fixtures::fixture("closed", 0).unwrap();
    let mut b = a.native.clone();
    for _ in 0..8 {
        assert_eq!(
            environment::step(&mut a, Matcher::Indexed)
                .unwrap()
                .native_frame,
            runtime::step(&mut b, Matcher::Reference).unwrap()
        );
    }
    let mut a = fixtures::fixture("driven", 1).unwrap();
    let mut b = a.clone();
    b.channels.reverse();
    for _ in 0..8 {
        let x = environment::step(&mut a, Matcher::Indexed).unwrap();
        let y = environment::step(&mut b, Matcher::Reference).unwrap();
        assert_eq!(x.native_frame, y.native_frame);
        assert_eq!(a.native, b.native);
        assert_eq!(a.injected, b.injected);
    }
}
#[test]
fn errors_after_environment_work_roll_back_entire_epoch() {
    let mut e = fixtures::fixture("driven", 0).unwrap();
    e.native.limits.max_bindings = 0;
    let old = e.clone();
    assert!(environment::step(&mut e, Matcher::Indexed).is_err());
    assert_eq!(e, old);
    let mut e = fixtures::fixture("driven", 0).unwrap();
    e.native.world.next_event = u64::MAX;
    let old = e.clone();
    assert!(environment::step(&mut e, Matcher::Indexed).is_err());
    assert_eq!(e, old);
    let mut e = fixtures::fixture("driven", 0).unwrap();
    e.channels[0].action = Action::Supply {
        node: 0,
        amount: u64::MAX,
    };
    let old = e.clone();
    assert!(environment::step(&mut e, Matcher::Indexed).is_err());
    assert_eq!(e, old);
}
#[test]
fn local_geometry_schedule_and_ledger_validation() {
    for bad in 0..5 {
        let mut e = fixtures::fixture("driven", 0).unwrap();
        match bad {
            0 => e.channels[0].period = 0,
            1 => e.channels[0].end = Some(0),
            2 => e.channels[0].id = 20,
            3 => e.injected = 1,
            _ => {
                e.channels[1].action = Action::Transport {
                    edge: 0,
                    from: 1,
                    to: 0,
                    matter: 0,
                    activation: 1,
                }
            }
        }
        let old = e.clone();
        assert!(environment::step(&mut e, Matcher::Indexed).is_err());
        assert_eq!(e, old);
    }
}
#[test]
fn unavailable_attempts_do_not_spend_or_allocate_events_and_provenance_is_explicit() {
    let mut e = fixtures::fixture("closed", 0).unwrap();
    e.channels.push(Channel {
        id: 0,
        start: 0,
        end: None,
        period: 1,
        action: Action::Extract { node: 1, amount: 1 },
    });
    let f = environment::step(&mut e, Matcher::Indexed).unwrap();
    assert_eq!(f.environment_events[0].status, "insufficient_resource");
    assert_eq!(f.environment_events[0].event_id, None);
    assert_eq!(e.native.world.next_event, 0);
    let mut e = fixtures::fixture("driven", 0).unwrap();
    let f = environment::step(&mut e, Matcher::Indexed).unwrap();
    assert_eq!(f.environment_events[1].parents, vec![0]);
    assert_eq!(f.environment_events[2].parents, vec![1]);
    assert_eq!(f.native_frame.events[0].parents, vec![2]);
}
