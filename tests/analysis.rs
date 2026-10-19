use causal_alife::{
    analysis, detector_fixtures,
    runtime::{self, Matcher},
};
use std::collections::BTreeSet;
#[test]
fn registered_detector_outcomes_and_maintenance_controls() {
    let suite = detector_fixtures::suite().unwrap();
    assert_eq!(suite.cases.len(), 144);
    for c in suite.cases {
        let expected = &suite.protocol.expected[&c.family];
        assert_eq!(
            &c.detection.active_persistence, &expected[0],
            "{} seed{}",
            c.family, c.initial.seed
        );
        assert_eq!(
            &c.maintenance_status, &expected[1],
            "{} seed{}",
            c.family, c.initial.seed
        );
        if let Some(m) = c.maintenance {
            assert_eq!(
                m.arms.iter().map(|a| a.occupancy).collect::<Vec<_>>(),
                if c.family == "renewal" {
                    vec![8, 8, 0, 8, 8]
                } else {
                    vec![12, 12, 12, 12, 12]
                }
            );
        }
    }
}
#[test]
fn fingerprint_is_exact_under_id_relabeling_and_ignores_state_resources() {
    let e = detector_fixtures::initial("active_pair", 0).unwrap();
    let members = BTreeSet::from([0, 1]);
    let a = analysis::fingerprint(&e.world, &members);
    let mut w = e.world.clone();
    let x = w.nodes.remove(&0).unwrap();
    let y = w.nodes.remove(&1).unwrap();
    w.nodes.insert(12, y);
    w.nodes.insert(40, x);
    w.edges.get_mut(&0).unwrap().ends = vec![40, 12];
    assert_eq!(a, analysis::fingerprint(&w, &BTreeSet::from([12, 40])));
    w.nodes.get_mut(&12).unwrap().state = 99;
    w.nodes.get_mut(&40).unwrap().matter = 0;
    assert_eq!(a, analysis::fingerprint(&w, &BTreeSet::from([12, 40])));
    w.edges.get_mut(&0).unwrap().ends.reverse();
    assert_ne!(a, analysis::fingerprint(&w, &BTreeSet::from([12, 40])));
}
#[test]
fn tampered_trace_rejected_and_short_window_does_not_pass() {
    let initial = detector_fixtures::initial("active_pair", 0).unwrap();
    let mut e = initial.clone();
    let mut frames = vec![];
    for _ in 0..7 {
        frames.push(runtime::step(&mut e, Matcher::Indexed).unwrap());
    }
    assert_eq!(
        analysis::analyze(&initial, &frames)
            .unwrap()
            .active_persistence,
        "not_supported"
    );
    frames[0].world.nodes.get_mut(&0).unwrap().state = 99;
    assert_eq!(
        analysis::analyze(&initial, &frames).unwrap_err(),
        "analysis_unverified_trace"
    );
}
