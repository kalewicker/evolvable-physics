//! Frozen P00e detector transfer panel; no detector parameters are changed here.
use crate::{
    analysis::{self, Detection},
    core::*,
    runtime::{self, Frame, Matcher},
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Family {
    pub nodes: usize,
    pub expected_ap: String,
    pub scope: String,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Protocol {
    pub schema: String,
    pub base_protocol_digest: String,
    pub epochs: usize,
    pub seeds: Vec<u64>,
    pub encodings: Vec<String>,
    pub families: BTreeMap<String, Family>,
    pub label_invariance_required: bool,
    pub claims: BTreeMap<String, String>,
    pub admission_policy: String,
}
pub fn protocol() -> Protocol {
    serde_json::from_str(include_str!("../docs/generalization_panel.json")).unwrap()
}
fn topology(family: &str, n: usize) -> Vec<Vec<usize>> {
    match family {
        "ring6" | "async_ring4" => (0..n).map(|i| vec![i, (i + 1) % n]).collect(),
        "star5" => (1..n).map(|i| vec![0, i]).collect(),
        "hyperedge3" | "hyperedge4" => vec![(0..n).collect()],
        "templated_births" => vec![],
        _ => (0..n - 1).map(|i| vec![i, i + 1]).collect(),
    }
}
fn rule(
    id: u64,
    kinds: Vec<u16>,
    states: Vec<Option<i32>>,
    edges: Vec<Vec<usize>>,
    ops: Vec<Op>,
) -> Rule {
    Rule {
        id,
        nodes: kinds
            .into_iter()
            .zip(states)
            .map(|(kind, state)| NodePattern { kind, state })
            .collect(),
        edges: edges
            .into_iter()
            .map(|ends| EdgePattern {
                class: Class::Structural,
                kind: 3,
                ends,
            })
            .collect(),
        absent: vec![],
        ops,
    }
}
fn base(family: &str, seed: u64) -> Result<Experiment> {
    let p = protocol();
    let cfg = p
        .families
        .get(family)
        .ok_or("unknown_generalization_family")?;
    let n = cfg.nodes;
    let kinds: Vec<_> = (0..n).map(|i| 100 + i as u16).collect();
    let shape = topology(family, n);
    let mut nodes: BTreeMap<_, _> = kinds
        .iter()
        .enumerate()
        .map(|(i, k)| {
            (
                i as u64,
                Node {
                    kind: *k,
                    state: 0,
                    matter: 2,
                    activation: 0,
                },
            )
        })
        .collect();
    let edges: BTreeMap<_, _> = shape
        .iter()
        .enumerate()
        .map(|(i, e)| {
            (
                i as u64,
                Edge {
                    class: Class::Structural,
                    kind: 3,
                    ends: e.iter().map(|n| *n as u64).collect(),
                },
            )
        })
        .collect();
    let mut rules = vec![];
    match family {
        "frozen6" => {}
        "resource_cycle3" => rules.push(rule(
            0,
            kinds.clone(),
            vec![None; n],
            shape.clone(),
            vec![
                Op::Transfer {
                    from: 0,
                    to: 1,
                    matter: 1,
                    activation: 0,
                },
                Op::Transfer {
                    from: 1,
                    to: 2,
                    matter: 1,
                    activation: 0,
                },
                Op::Transfer {
                    from: 2,
                    to: 0,
                    matter: 1,
                    activation: 0,
                },
            ],
        )),
        "async_ring4" | "oversize7" => {
            for (i, k) in kinds.iter().enumerate() {
                rules.push(rule(
                    i as u64,
                    vec![*k],
                    vec![None],
                    vec![],
                    vec![Op::AddState { node: 0, delta: 1 }],
                ));
            }
        }
        "fragmentation4" => {
            rules.push(rule(
                0,
                kinds.clone(),
                vec![Some(0); n],
                shape.clone(),
                (0..n).map(|node| Op::SetState { node, value: 1 }).collect(),
            ));
            let mut ops: Vec<_> = (0..n).map(|node| Op::SetState { node, value: 2 }).collect();
            ops.push(Op::DeleteEdge {
                account: 0,
                kind: 3,
                ends: vec![1, 2],
            });
            rules.push(rule(1, kinds.clone(), vec![Some(1); n], shape.clone(), ops));
            for (j, start) in [0, 2].into_iter().enumerate() {
                for state in [2, 3] {
                    rules.push(rule(
                        2 + (j * 2 + (state - 2)) as u64,
                        kinds[start..start + 2].to_vec(),
                        vec![Some(state as i32); 2],
                        vec![vec![0, 1]],
                        vec![
                            Op::SetState {
                                node: 0,
                                value: 5 - state as i32,
                            },
                            Op::SetState {
                                node: 1,
                                value: 5 - state as i32,
                            },
                        ],
                    ));
                }
            }
        }
        "templated_births" => {
            for node in nodes.values_mut() {
                node.kind = 99;
                node.matter = 3;
            }
            rules.push(rule(
                0,
                vec![99],
                vec![Some(0)],
                vec![],
                vec![
                    Op::CreateNode {
                        account: 0,
                        kind: 100,
                        state: 0,
                    },
                    Op::CreateNode {
                        account: 0,
                        kind: 101,
                        state: 0,
                    },
                    Op::CreateEdge {
                        account: 0,
                        kind: 3,
                        ends: vec![1, 2],
                    },
                    Op::SetState { node: 0, value: 1 },
                ],
            ));
        }
        _ => rules.push(rule(
            0,
            kinds,
            vec![None; n],
            shape,
            (0..n).map(|node| Op::AddState { node, delta: 1 }).collect(),
        )),
    }
    let matter_total = nodes.values().map(|n| n.matter + 1).sum::<u64>() + edges.len() as u64;
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
            next_node: n as u64,
            next_edge: edges.len() as u64,
            nodes,
            edges,
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
fn id_map(n: usize, seed: u64, offset: u64) -> BTreeMap<u64, u64> {
    (0..n)
        .map(|i| {
            (
                i as u64,
                offset + 17 * (((n - 1 - i) + seed as usize % n) % n) as u64,
            )
        })
        .collect()
}
pub fn initial(family: &str, seed: u64, encoding: &str) -> Result<Experiment> {
    let mut e = base(family, seed)?;
    if encoding == "identity" {
        return Ok(e);
    }
    if encoding != "relabeled" {
        return Err("unknown_generalization_encoding".into());
    }
    let nodes = id_map(e.world.nodes.len(), seed, 1_000);
    let edges = id_map(e.world.edges.len(), seed, 10_000);
    e.world.nodes = e
        .world
        .nodes
        .into_iter()
        .map(|(id, node)| (nodes[&id], node))
        .collect();
    e.world.edges = e
        .world
        .edges
        .into_iter()
        .map(|(id, mut edge)| {
            edge.ends.iter_mut().for_each(|id| *id = nodes[id]);
            (edges[&id], edge)
        })
        .collect();
    e.world.next_node = e.world.nodes.keys().next_back().unwrap() + 1;
    e.world.next_edge = e.world.edges.keys().next_back().map_or(0, |i| i + 1);
    e.rules.reverse();
    e.validate()?;
    Ok(e)
}
#[derive(Serialize)]
pub struct Case {
    pub family: String,
    pub encoding: String,
    pub scope: String,
    pub expected_ap: String,
    pub initial: Experiment,
    pub frames: Vec<Frame>,
    pub detection: Detection,
    pub initial_fingerprint: Option<String>,
}
#[derive(Serialize)]
pub struct Suite {
    pub schema: String,
    pub protocol: Protocol,
    pub protocol_digest: String,
    pub scientific_status: String,
    pub cases: Vec<Case>,
}
pub fn suite() -> Result<Suite> {
    let p = protocol();
    if digest(&analysis::protocol()) != p.base_protocol_digest {
        return Err("generalization_detector_protocol_drift".into());
    }
    let mut cases = vec![];
    for (family, cfg) in &p.families {
        for seed in &p.seeds {
            for encoding in &p.encodings {
                let initial = initial(family, *seed, encoding)?;
                let members: BTreeSet<_> = initial.world.nodes.keys().copied().collect();
                let initial_fingerprint = if members.len() <= 6 {
                    Some(analysis::fingerprint(&initial.world, &members))
                } else {
                    None
                };
                let mut e = initial.clone();
                let mut reference = initial.clone();
                let mut frames = vec![];
                for _ in 0..p.epochs {
                    let a = runtime::step(&mut e, Matcher::Indexed)?;
                    let b = runtime::step(&mut reference, Matcher::Reference)?;
                    if a != b {
                        return Err("generalization_matcher_mismatch".into());
                    }
                    frames.push(a);
                }
                let detection = analysis::analyze(&initial, &frames)?;
                cases.push(Case {
                    family: family.clone(),
                    encoding: encoding.clone(),
                    scope: cfg.scope.clone(),
                    expected_ap: cfg.expected_ap.clone(),
                    initial,
                    frames,
                    detection,
                    initial_fingerprint,
                });
            }
        }
    }
    Ok(Suite {
        schema: "p00f-generalization-suite-v1".into(),
        protocol_digest: digest(&p),
        protocol: p,
        scientific_status: "untested".into(),
        cases,
    })
}
