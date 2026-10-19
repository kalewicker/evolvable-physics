use causal_alife::{
    core::*,
    experiments::*,
    runtime::{self, Matcher},
};

#[test]
fn full_fixture_differential_suite() {
    assert_eq!(suite().unwrap().cases.len(), 112);
}
#[test]
fn expected_oscillator_and_frozen_behavior() {
    for name in ["oscillator", "frozen", "resource_exhaustion"] {
        let mut e = fixture(name, 0).unwrap();
        let initial = e.world.clone();
        for tick in 1..=12 {
            let f = runtime::step(&mut e, Matcher::Indexed).unwrap();
            assert_eq!(f.events.len(), if name == "oscillator" { 2 } else { 0 });
            assert_eq!(
                e.world.nodes[&0].state,
                if name == "oscillator" { tick % 2 } else { 0 }
            );
        }
        assert_eq!(e.world.nodes, initial.nodes);
        assert_eq!(e.world.matter_total, initial.matter_total);
    }
}
#[test]
fn cap_errors_leave_entire_experiment_unchanged() {
    for cap in ["matches", "bindings", "nodes", "edges"] {
        let mut e = fixture("growth_recycling", 0).unwrap();
        match cap {
            "matches" => e.limits.max_candidates = 0,
            "bindings" => e.limits.max_bindings = 0,
            "nodes" => e.limits.max_nodes = 3,
            _ => e.limits.max_edges = 2,
        }
        let original = e.clone();
        assert!(runtime::step(&mut e, Matcher::Indexed).is_err());
        assert_eq!(e, original);
    }
}
#[test]
fn invalid_inputs_rejected_without_mutation() {
    let mut e = fixture("transfer", 1).unwrap();
    e.rules[0].edges.clear();
    let original = e.clone();
    assert_eq!(
        runtime::step(&mut e, Matcher::Reference).unwrap_err(),
        "disconnected_pattern"
    );
    assert_eq!(e, original);
    let mut e = fixture("frozen", 0).unwrap();
    e.world.nodes.get_mut(&0).unwrap().matter += 1;
    assert_eq!(e.validate().unwrap_err(), "matter_not_conserved");
    let mut e = fixture("frozen", 0).unwrap();
    e.world.edges.insert(2, e.world.edges[&0].clone());
    e.world.next_edge = 3;
    assert_eq!(e.validate().unwrap_err(), "duplicate_edge");
}
#[test]
fn failed_compound_operations_are_not_partially_applied() {
    let mut e = fixture("growth_recycling", 0).unwrap();
    e.rules.truncate(1);
    e.rules[0].ops.push(Op::AddState {
        node: 0,
        delta: i32::MAX,
    });
    e.rules[0].ops.push(Op::AddState { node: 0, delta: 1 });
    let before = e.world.clone();
    assert!(
        runtime::step(&mut e, Matcher::Indexed)
            .unwrap()
            .events
            .is_empty()
    );
    assert_eq!(e.world.nodes, before.nodes);
    assert_eq!(e.world.edges, before.edges);
    assert_eq!(e.world.next_node, before.next_node);
    assert_eq!(e.world.next_edge, before.next_edge);
}
#[test]
fn dangling_deletion_and_duplicate_edges_are_inapplicable() {
    let mut e = fixture("transfer", 0).unwrap();
    e.rules[0].ops = vec![Op::DeleteNode {
        node: 0,
        recipient: 1,
    }];
    assert!(
        runtime::step(&mut e, Matcher::Indexed)
            .unwrap()
            .events
            .is_empty()
    );
    let mut e = fixture("attach_detach", 0).unwrap();
    e.rules.truncate(1);
    e.rules[0].ops.push(Op::CreateEdge {
        account: 0,
        kind: 3,
        ends: vec![0, 1],
    });
    assert!(
        runtime::step(&mut e, Matcher::Indexed)
            .unwrap()
            .events
            .is_empty()
    );
}
#[test]
fn absent_predicates_and_shared_accounts_conflict() {
    for name in ["absence_conflict", "transfer"] {
        for seed in 0..32 {
            let mut e = fixture(name, seed).unwrap();
            let f = runtime::step(&mut e, Matcher::Indexed).unwrap();
            assert!(f.candidates.len() >= 2);
            assert_eq!(f.events.len(), 1);
        }
    }
}
#[test]
fn storage_order_and_independent_workers_do_not_change_results() {
    let mut a = fixture("attach_detach", 4).unwrap();
    let mut b = a.clone();
    b.rules.reverse();
    for _ in 0..20 {
        assert_eq!(
            runtime::step(&mut a, Matcher::Reference),
            runtime::step(&mut b, Matcher::Indexed)
        );
    }
    let handles: Vec<_> = (0..4)
        .map(|_| {
            std::thread::spawn(|| {
                let mut e = fixture("growth_recycling", 8).unwrap();
                for _ in 0..20 {
                    runtime::step(&mut e, Matcher::Indexed).unwrap();
                }
                e.world
            })
        })
        .collect();
    let states: Vec<_> = handles.into_iter().map(|h| h.join().unwrap()).collect();
    assert!(states.windows(2).all(|s| s[0] == s[1]));
}
#[test]
fn provenance_has_prior_event_ids_and_no_op_branch_is_identical() {
    let mut a = fixture("oscillator", 4).unwrap();
    runtime::step(&mut a, Matcher::Indexed).unwrap();
    let mut branch = a.clone();
    let f = runtime::step(&mut a, Matcher::Indexed).unwrap();
    assert_eq!(f, runtime::step(&mut branch, Matcher::Indexed).unwrap());
    for event in f.events {
        assert!(!event.parents.is_empty());
        assert!(event.parents.iter().all(|p| *p < event.id));
    }
}
#[test]
fn ordered_hyperedges_support_three_and_four_endpoints() {
    for arity in 3..=4 {
        let mut e = fixture("frozen", 0).unwrap();
        e.world.nodes.clear();
        e.world.edges.clear();
        for id in 0..arity {
            e.world.nodes.insert(
                id,
                Node {
                    kind: id as u16,
                    state: 0,
                    matter: 2,
                    activation: 0,
                },
            );
        }
        let ids: Vec<u64> = (0..arity).collect();
        e.world.edges.insert(
            0,
            Edge {
                class: Class::Contact,
                kind: 5,
                ends: ids,
            },
        );
        e.world.next_node = arity;
        e.world.next_edge = 1;
        e.world.matter_total = arity * 3 + 1;
        e.world.activation_total = 0;
        e.rules = vec![Rule {
            id: 0,
            nodes: (0..arity)
                .map(|id| NodePattern {
                    kind: id as u16,
                    state: None,
                })
                .collect(),
            edges: vec![EdgePattern {
                class: Class::Contact,
                kind: 5,
                ends: (0..arity as usize).collect(),
            }],
            absent: vec![],
            ops: vec![Op::CreateEdge {
                account: 0,
                kind: 6,
                ends: (0..arity as usize).collect(),
            }],
        }];
        let mut other = e.clone();
        let a = runtime::step(&mut e, Matcher::Reference).unwrap();
        assert_eq!(a, runtime::step(&mut other, Matcher::Indexed).unwrap());
        assert_eq!(a.events.len(), 1);
        assert_eq!(e.world.nodes[&0].matter, 1);
        e.rules[0].edges[0].ends.reverse();
        assert!(
            runtime::step(&mut e, Matcher::Indexed)
                .unwrap()
                .events
                .is_empty()
        );
    }
}
#[test]
fn counter_overflow_rolls_back_whole_epoch() {
    for counter in ["epoch", "event"] {
        let mut e = fixture("oscillator", 0).unwrap();
        if counter == "epoch" {
            e.world.epoch = u64::MAX;
        } else {
            e.world.next_event = u64::MAX;
        }
        let before = e.clone();
        assert_eq!(
            runtime::step(&mut e, Matcher::Indexed).unwrap_err(),
            "integer_overflow"
        );
        assert_eq!(e, before);
    }
}
