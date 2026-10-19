use crate::{
    analysis::{self, Detection, Protocol},
    core::*,
    interventions::{self, Branch, Intervention, Request},
    runtime::{self, Frame, Matcher},
};
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};
pub const FAMILIES: [&str; 9] = [
    "frozen_pair",
    "active_pair",
    "inert_with_oscillator",
    "attached_inert",
    "irrelevant_bits",
    "wholesale_replacement",
    "noise_replacement",
    "renewal",
    "passive_turnover",
];
fn np(kind: u16, state: Option<i32>) -> NodePattern {
    NodePattern { kind, state }
}
fn ep(kind: u16, ends: Vec<usize>) -> EdgePattern {
    EdgePattern {
        class: Class::Structural,
        kind,
        ends,
    }
}
fn rule(id: u64, nodes: Vec<NodePattern>, edges: Vec<EdgePattern>, ops: Vec<Op>) -> Rule {
    Rule {
        id,
        nodes,
        edges,
        absent: vec![],
        ops,
    }
}
fn node(kind: u16) -> Node {
    Node {
        kind,
        state: 0,
        matter: 0,
        activation: 0,
    }
}
pub fn initial(family: &str, seed: u64) -> Result<Experiment> {
    if !FAMILIES.contains(&family) {
        return Err("unknown_detector_fixture".into());
    }
    let mut nodes = BTreeMap::from([(0, node(10)), (1, node(11))]);
    nodes.get_mut(&0).unwrap().matter = 8;
    let mut edges = BTreeMap::from([(
        0,
        Edge {
            class: Class::Structural,
            kind: 3,
            ends: vec![0, 1],
        },
    )]);
    let mut rules = vec![];
    match family {
        "frozen_pair" => {}
        "active_pair" | "attached_inert" | "irrelevant_bits" => {
            if family == "irrelevant_bits" {
                rules.push(rule(
                    0,
                    vec![np(10, None), np(11, None)],
                    vec![ep(3, vec![0, 1])],
                    vec![
                        Op::AddState { node: 0, delta: 1 },
                        Op::AddState { node: 1, delta: 1 },
                    ],
                ));
            } else {
                for s in 0..2 {
                    rules.push(rule(
                        s as u64,
                        vec![np(10, Some(s)), np(11, Some(s))],
                        vec![ep(3, vec![0, 1])],
                        vec![
                            Op::SetState {
                                node: 0,
                                value: 1 - s,
                            },
                            Op::SetState {
                                node: 1,
                                value: 1 - s,
                            },
                        ],
                    ));
                }
            }
            if family == "attached_inert" {
                nodes.insert(2, node(12));
                edges.insert(
                    1,
                    Edge {
                        class: Class::Structural,
                        kind: 4,
                        ends: vec![1, 2],
                    },
                );
            }
        }
        "inert_with_oscillator" => {
            for s in 0..2 {
                rules.push(rule(
                    s as u64,
                    vec![np(10, Some(s))],
                    vec![],
                    vec![Op::SetState {
                        node: 0,
                        value: 1 - s,
                    }],
                ));
            }
        }
        "renewal" | "passive_turnover" => {
            nodes.insert(2, node(12));
            edges.insert(
                1,
                Edge {
                    class: Class::Structural,
                    kind: 4,
                    ends: vec![0, 2],
                },
            );
            let pats = |state| vec![np(10, Some(state)), np(11, None), np(12, None)];
            let matched = vec![ep(3, vec![0, 1]), ep(4, vec![0, 2])];
            if family == "renewal" {
                rules.push(rule(
                    0,
                    vec![np(12, Some(0))],
                    vec![],
                    vec![Op::SetState { node: 0, value: 1 }],
                ));
                let mut p = pats(0);
                p[2].state = Some(1);
                rules.push(rule(
                    1,
                    p,
                    matched,
                    vec![
                        Op::DeleteEdge {
                            account: 0,
                            kind: 4,
                            ends: vec![0, 2],
                        },
                        Op::DeleteNode {
                            node: 2,
                            recipient: 0,
                        },
                        Op::SetState { node: 0, value: 1 },
                        Op::SetState { node: 1, value: 1 },
                    ],
                ));
                rules.push(rule(
                    2,
                    vec![np(10, Some(1)), np(11, None)],
                    vec![ep(3, vec![0, 1])],
                    vec![
                        Op::CreateNode {
                            account: 0,
                            kind: 12,
                            state: 0,
                        },
                        Op::CreateEdge {
                            account: 0,
                            kind: 4,
                            ends: vec![0, 2],
                        },
                        Op::SetState { node: 0, value: 0 },
                        Op::SetState { node: 1, value: 0 },
                    ],
                ));
            } else {
                for s in 0..2 {
                    rules.push(rule(
                        s as u64,
                        pats(s),
                        matched.clone(),
                        vec![
                            Op::DeleteEdge {
                                account: 0,
                                kind: 4,
                                ends: vec![0, 2],
                            },
                            Op::DeleteNode {
                                node: 2,
                                recipient: 0,
                            },
                            Op::CreateNode {
                                account: 0,
                                kind: 12,
                                state: 0,
                            },
                            Op::CreateEdge {
                                account: 0,
                                kind: 4,
                                ends: vec![0, 3],
                            },
                            Op::SetState {
                                node: 0,
                                value: 1 - s,
                            },
                            Op::SetState {
                                node: 1,
                                value: 1 - s,
                            },
                        ],
                    ));
                }
            }
            // Identical, disconnected control component for maintenance interventions.
            for id in 0..3 {
                nodes.insert(id + 3, nodes[&id].clone());
            }
            for id in 0..2 {
                let mut e = edges[&id].clone();
                e.ends.iter_mut().for_each(|id| *id += 3);
                edges.insert(id + 2, e);
            }
        }
        "wholesale_replacement" | "noise_replacement" => {
            nodes.insert(2, node(12));
            edges.insert(
                1,
                Edge {
                    class: Class::Structural,
                    kind: 4,
                    ends: vec![0, 2],
                },
            );
            rules.push(rule(
                0,
                vec![np(10, None), np(11, None), np(12, None)],
                vec![ep(3, vec![0, 1]), ep(4, vec![0, 2])],
                vec![
                    Op::DeleteEdge {
                        account: 0,
                        kind: 3,
                        ends: vec![0, 1],
                    },
                    Op::DeleteEdge {
                        account: 0,
                        kind: 4,
                        ends: vec![0, 2],
                    },
                    Op::DeleteNode {
                        node: 1,
                        recipient: 0,
                    },
                    Op::DeleteNode {
                        node: 2,
                        recipient: 0,
                    },
                    Op::CreateNode {
                        account: 0,
                        kind: 11,
                        state: 0,
                    },
                    Op::CreateNode {
                        account: 0,
                        kind: 12,
                        state: 0,
                    },
                    Op::CreateEdge {
                        account: 0,
                        kind: 3,
                        ends: vec![0, 3],
                    },
                    Op::CreateEdge {
                        account: 0,
                        kind: 4,
                        ends: vec![0, 4],
                    },
                ],
            ));
        }
        _ => unreachable!(),
    }
    if family == "noise_replacement" {
        let mut alternative = rules[0].clone();
        alternative.id = 1;
        for op in &mut alternative.ops {
            if let Op::CreateNode { kind, state, .. } = op {
                *state = if *kind == 11 { 7 } else { 13 };
            }
        }
        rules.push(alternative);
    }
    let matter_total = nodes.values().map(|n| n.matter + 1).sum::<u64>() + edges.len() as u64;
    let next_node = nodes.keys().next_back().unwrap() + 1;
    let next_edge = edges.keys().next_back().unwrap() + 1;
    let e = Experiment {
        profile: PROFILE.into(),
        seed,
        rules,
        limits: Limits {
            max_candidates: 10_000,
            max_bindings: 100_000,
            max_nodes: 128,
            max_edges: 256,
        },
        world: World {
            nodes,
            edges,
            next_node,
            next_edge,
            epoch: 0,
            dissipated: 0,
            matter_total,
            activation_total: 0,
            next_event: 0,
            writers: BTreeMap::new(),
        },
    };
    e.validate()?;
    Ok(e)
}
fn run(e: &mut Experiment, n: usize) -> Result<Vec<Frame>> {
    let mut reference = e.clone();
    let mut out = vec![];
    for _ in 0..n {
        let a = runtime::step(e, Matcher::Indexed)?;
        let b = runtime::step(&mut reference, Matcher::Reference)?;
        if a != b {
            return Err("detector_fixture_matcher_mismatch".into());
        }
        out.push(a);
    }
    Ok(out)
}
#[derive(Serialize)]
pub struct Arm {
    pub name: String,
    pub chain: Vec<Branch>,
    pub frames: Vec<Frame>,
    pub occupancy: usize,
}
#[derive(Serialize)]
pub struct Maintenance {
    pub warmup: Vec<Frame>,
    pub source: Experiment,
    pub root: u64,
    pub reference_fingerprint: String,
    pub arms: Vec<Arm>,
    pub supported: bool,
}
#[derive(Serialize)]
pub struct Case {
    pub family: String,
    pub split: String,
    pub initial: Experiment,
    pub frames: Vec<Frame>,
    pub detection: Detection,
    pub maintenance: Option<Maintenance>,
    pub maintenance_status: String,
}
#[derive(Serialize)]
pub struct Suite {
    pub schema: String,
    pub protocol: Protocol,
    pub protocol_digest: String,
    pub scientific_status: String,
    pub cases: Vec<Case>,
}
fn maintenance(initial: &Experiment, det: &Detection) -> Result<Maintenance> {
    let p = analysis::protocol();
    let reference = analysis::fingerprint(&initial.world, &BTreeSet::from([0, 1, 2]));
    let mut source = initial.clone();
    let warmup = run(&mut source, 2)?;
    let mut arms = vec![];
    for name in ["baseline", "sham", "target", "unrelated", "rescue"] {
        let node = if name == "unrelated" { 3 } else { 0 };
        let expected = source.world.nodes[&node].state;
        let ops = if name == "baseline" {
            vec![]
        } else {
            vec![Intervention::SetState {
                node,
                expected,
                value: if name == "sham" { expected } else { 9 },
            }]
        };
        let b = interventions::branch(&source, &Request::new(&source, ops))?;
        let mut current = b.experiment.clone();
        let mut chain = vec![b];
        if name == "rescue" {
            let b = interventions::branch(
                &current,
                &Request::new(
                    &current,
                    vec![Intervention::SetState {
                        node: 0,
                        expected: 9,
                        value: source.world.nodes[&0].state,
                    }],
                ),
            )?;
            current = b.experiment.clone();
            chain.push(b);
        }
        let frames = run(&mut current, p.maintenance_horizon)?;
        let worlds: Vec<_> = frames.iter().map(|f| f.world.clone()).collect();
        let occupancy = analysis::occupancy(&worlds, 0, &reference);
        arms.push(Arm {
            name: name.into(),
            chain,
            frames,
            occupancy,
        });
    }
    let base = arms[0].occupancy;
    let supported = det.active_persistence == "supported"
        && det.agreement_pairs.iter().any(|[i, j]| {
            let a = &det.connected.tracks[*i];
            let b = &det.interaction.tracks[*j];
            a.members.contains(&0)
                && b.members.contains(&0)
                && a.births.min(a.deaths) >= p.min_replacement_pairs
                && b.births.min(b.deaths) >= p.min_replacement_pairs
        })
        && base.saturating_sub(arms[2].occupancy) * p.min_occupancy_drop_denominator
            >= p.maintenance_horizon * p.min_occupancy_drop_numerator
        && [1, 3, 4]
            .iter()
            .all(|i| arms[*i].occupancy.abs_diff(base) <= p.control_occupancy_tolerance);
    Ok(Maintenance {
        warmup,
        source,
        root: 0,
        reference_fingerprint: reference,
        arms,
        supported,
    })
}
pub fn suite() -> Result<Suite> {
    let p = analysis::protocol();
    let mut cases = vec![];
    for family in FAMILIES {
        for seed in 0..16 {
            let initial = initial(family, seed)?;
            let mut e = initial.clone();
            let frames = run(&mut e, 12)?;
            let detection = analysis::analyze(&initial, &frames)?;
            let maintenance = if ["renewal", "passive_turnover"].contains(&family) {
                Some(maintenance(&initial, &detection)?)
            } else {
                None
            };
            let maintenance_status = if maintenance.as_ref().is_some_and(|m| m.supported) {
                "supported"
            } else {
                "not_supported"
            }
            .into();
            cases.push(Case {
                family: family.into(),
                split: if p.development_seeds.contains(&seed) {
                    "development"
                } else {
                    "validation"
                }
                .into(),
                initial,
                frames,
                detection,
                maintenance,
                maintenance_status,
            });
        }
    }
    Ok(Suite {
        schema: "p00e-detector-suite-v1".into(),
        protocol_digest: digest(&p),
        protocol: p,
        scientific_status: "untested".into(),
        cases,
    })
}
