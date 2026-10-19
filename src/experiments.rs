use crate::core::*;
use crate::runtime::{self, Frame, Matcher};
use serde::Serialize;
use std::collections::BTreeMap;

fn node(kind: u16, matter: u64) -> Node {
    Node {
        kind,
        state: 0,
        matter,
        activation: 8,
    }
}
fn pattern(kind: u16, state: Option<i32>) -> NodePattern {
    NodePattern { kind, state }
}
fn edge(class: Class, kind: u16) -> EdgePattern {
    EdgePattern {
        class,
        kind,
        ends: vec![0, 1],
    }
}
fn rule(
    id: u64,
    nodes: Vec<NodePattern>,
    edges: Vec<EdgePattern>,
    absent: Vec<EdgePattern>,
    ops: Vec<Op>,
) -> Rule {
    Rule {
        id,
        nodes,
        edges,
        absent,
        ops,
    }
}
pub const FIXTURES: [&str; 7] = [
    "frozen",
    "oscillator",
    "attach_detach",
    "growth_recycling",
    "transfer",
    "absence_conflict",
    "resource_exhaustion",
];
pub fn fixture(name: &str, seed: u64) -> Result<Experiment> {
    let mut world = World {
        nodes: BTreeMap::from([(0, node(1, 8)), (1, node(2, 0)), (2, node(1, 4))]),
        edges: BTreeMap::from([
            (
                0,
                Edge {
                    class: Class::Contact,
                    kind: 0,
                    ends: vec![0, 1],
                },
            ),
            (
                1,
                Edge {
                    class: Class::Contact,
                    kind: 0,
                    ends: vec![2, 1],
                },
            ),
        ]),
        next_node: 3,
        next_edge: 2,
        epoch: 0,
        dissipated: 0,
        matter_total: 17,
        activation_total: 24,
        next_event: 0,
        writers: BTreeMap::new(),
    };
    let pair = vec![pattern(1, None), pattern(2, None)];
    let contact = vec![edge(Class::Contact, 0)];
    let structural = edge(Class::Structural, 3);
    let rules = match name {
        "frozen" => vec![],
        "oscillator" => vec![
            rule(
                0,
                vec![pattern(1, Some(0))],
                vec![],
                vec![],
                vec![Op::SetState { node: 0, value: 1 }],
            ),
            rule(
                1,
                vec![pattern(1, Some(1))],
                vec![],
                vec![],
                vec![Op::SetState { node: 0, value: 0 }],
            ),
        ],
        "attach_detach" => vec![
            rule(
                0,
                pair.clone(),
                contact.clone(),
                vec![structural.clone()],
                vec![
                    Op::CreateEdge {
                        account: 0,
                        kind: 3,
                        ends: vec![0, 1],
                    },
                    Op::Burn { node: 0, amount: 1 },
                ],
            ),
            rule(
                1,
                pair.clone(),
                vec![structural.clone()],
                vec![],
                vec![Op::DeleteEdge {
                    account: 0,
                    kind: 3,
                    ends: vec![0, 1],
                }],
            ),
        ],
        "growth_recycling" => vec![
            rule(
                0,
                vec![pattern(1, None)],
                vec![],
                vec![],
                vec![
                    Op::CreateNode {
                        account: 0,
                        kind: 3,
                        state: 0,
                    },
                    Op::CreateEdge {
                        account: 0,
                        kind: 3,
                        ends: vec![0, 1],
                    },
                ],
            ),
            rule(
                1,
                vec![pattern(1, None), pattern(3, None)],
                vec![structural.clone()],
                vec![],
                vec![
                    Op::DeleteEdge {
                        account: 0,
                        kind: 3,
                        ends: vec![0, 1],
                    },
                    Op::DeleteNode {
                        node: 1,
                        recipient: 0,
                    },
                ],
            ),
        ],
        "transfer" => vec![rule(
            0,
            pair.clone(),
            contact.clone(),
            vec![],
            vec![Op::Transfer {
                from: 0,
                to: 1,
                matter: 1,
                activation: 1,
            }],
        )],
        "absence_conflict" => vec![
            rule(
                0,
                pair.clone(),
                contact.clone(),
                vec![structural.clone()],
                vec![Op::CreateEdge {
                    account: 0,
                    kind: 3,
                    ends: vec![0, 1],
                }],
            ),
            rule(
                1,
                pair,
                contact,
                vec![structural],
                vec![Op::AddState { node: 1, delta: 1 }],
            ),
        ],
        "resource_exhaustion" => {
            world.nodes.get_mut(&0).unwrap().matter = 0;
            world.nodes.get_mut(&2).unwrap().matter = 0;
            world.matter_total = 5;
            vec![rule(
                0,
                vec![pattern(1, None)],
                vec![],
                vec![],
                vec![
                    Op::SetState { node: 0, value: 99 },
                    Op::CreateNode {
                        account: 0,
                        kind: 3,
                        state: 0,
                    },
                ],
            )]
        }
        _ => return Err("unknown_fixture".into()),
    };
    Ok(Experiment {
        profile: PROFILE.into(),
        seed,
        rules,
        limits: Limits {
            max_candidates: 10_000,
            max_bindings: 100_000,
            max_nodes: 128,
            max_edges: 256,
        },
        world,
    })
}
#[derive(Serialize)]
pub struct Case {
    pub name: String,
    pub initial: Experiment,
    pub frames: Vec<Frame>,
}
#[derive(Serialize)]
pub struct Suite {
    pub schema: String,
    pub engineering_status: String,
    pub scientific_status: String,
    pub cases: Vec<Case>,
}
pub fn suite() -> Result<Suite> {
    let mut cases = Vec::new();
    for name in FIXTURES {
        for seed in 0..16 {
            let initial = fixture(name, seed)?;
            let mut reference = initial.clone();
            let mut indexed = initial.clone();
            let mut frames = Vec::new();
            for _ in 0..12 {
                let a = runtime::step(&mut reference, Matcher::Reference)?;
                let b = runtime::step(&mut indexed, Matcher::Indexed)?;
                if a != b {
                    return Err(format!("differential_mismatch:{name}:{seed}"));
                }
                frames.push(a);
            }
            cases.push(Case {
                name: name.into(),
                initial,
                frames,
            });
        }
    }
    Ok(Suite {
        schema: "p00a-suite-v1".into(),
        engineering_status: "rust_matchers_agree_pending_independent_audit".into(),
        scientific_status: "untested".into(),
        cases,
    })
}
