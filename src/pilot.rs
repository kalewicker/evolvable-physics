//! P01 development generator and atomic, bounded observer. Frozen P00 code is unchanged.
use crate::{
    core::*,
    environment::{self, Environment, Epoch},
    runtime::Matcher,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const GENERATOR: &str = "p01-generator-v1";
// Deliberately uses modulo reduction, including its tiny bias; no rejection or repair.
fn draw(proposal: u64, initial: u64, field: &str, index: u64, n: u64) -> u64 {
    let h = digest(&(GENERATOR, proposal, initial, field, index));
    u64::from_str_radix(&h[..16], 16).unwrap() % n
}
pub fn generate(proposal: u64, initial: u64) -> Result<Environment> {
    if initial >= 4 {
        return Err("initial_state_out_of_range".into());
    }
    let mut rules = Vec::new();
    for id in 0..8 {
        let d = |field, n| draw(proposal, 0, field, id, n);
        let form = d("form", 8);
        let pair = form >= 3 && form != 4;
        let nodes = (0..if pair { 2 } else { 1 })
            .map(|slot| {
                let state = d(if slot == 0 { "state0" } else { "state1" }, 4);
                NodePattern {
                    kind: 1 + d(if slot == 0 { "kind0" } else { "kind1" }, 3) as u16,
                    state: if state == 3 { None } else { Some(state as i32) },
                }
            })
            .collect();
        let structural = EdgePattern {
            class: Class::Structural,
            kind: 0,
            ends: vec![0, 1],
        };
        let edges = if !pair {
            vec![]
        } else {
            vec![EdgePattern {
                class: if form >= 6 {
                    Class::Structural
                } else {
                    Class::Contact
                },
                kind: 0,
                ends: vec![0, 1],
            }]
        };
        let amount = 1 + d("amount", 2);
        let ops = match form {
            0 => vec![Op::SetState {
                node: 0,
                value: d("value", 3) as i32,
            }],
            1 => vec![Op::AddState {
                node: 0,
                delta: if d("sign", 2) == 0 { -1 } else { 1 },
            }],
            2 => vec![Op::Burn { node: 0, amount }],
            3 => vec![Op::Transfer {
                from: 0,
                to: 1,
                matter: d("matter", 2),
                activation: amount,
            }],
            4 => vec![Op::CreateNode {
                account: 0,
                kind: 1 + d("new_kind", 3) as u16,
                state: d("value", 3) as i32,
            }],
            5 => vec![Op::CreateEdge {
                account: 0,
                kind: 0,
                ends: vec![0, 1],
            }],
            6 => vec![Op::DeleteEdge {
                account: 0,
                kind: 0,
                ends: vec![0, 1],
            }],
            _ => vec![
                Op::DeleteEdge {
                    account: 1,
                    kind: 0,
                    ends: vec![0, 1],
                },
                Op::DeleteNode {
                    node: 0,
                    recipient: 1,
                },
            ],
        };
        rules.push(Rule {
            id,
            nodes,
            edges,
            absent: if form == 5 { vec![structural] } else { vec![] },
            ops,
        });
    }
    let nodes = (0..8)
        .map(|id| {
            (
                id,
                Node {
                    kind: 1 + draw(proposal, initial, "node_kind", id, 3) as u16,
                    state: draw(proposal, initial, "node_state", id, 3) as i32,
                    matter: 8,
                    activation: 8,
                },
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut edges = BTreeMap::new();
    for id in 0..8 {
        edges.insert(
            id,
            Edge {
                class: Class::Contact,
                kind: 0,
                ends: vec![id, (id + 1) % 8],
            },
        );
    }
    for id in 0..8 {
        if draw(proposal, initial, "structural", id, 2) == 1 {
            edges.insert(
                edges.len() as u64,
                Edge {
                    class: Class::Structural,
                    kind: 0,
                    ends: vec![id, (id + 1) % 8],
                },
            );
        }
    }
    let matter_total = 72 + edges.len() as u64;
    let env = Environment {
        profile: environment::PROFILE.into(),
        channels: vec![],
        initial_activation: 64,
        injected: 0,
        extracted: 0,
        native: Experiment {
            profile: PROFILE.into(),
            seed: draw(proposal, initial, "scheduler", 0, u64::MAX),
            rules,
            limits: Limits {
                max_candidates: 4096,
                max_bindings: 65536,
                max_nodes: 128,
                max_edges: 256,
            },
            world: World {
                nodes,
                edges,
                next_node: 8,
                next_edge: matter_total - 72,
                epoch: 0,
                dissipated: 0,
                matter_total,
                activation_total: 64,
                next_event: 0,
                writers: BTreeMap::new(),
            },
        },
    };
    env.validate()?;
    Ok(env)
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema: String,
    pub initial: Environment,
    pub epochs: u64,
    pub max_events: u64,
    pub max_trace_bytes: u64,
}
/// Event limit includes environment and native events. A rejected epoch changes nothing.
pub fn bounded_step(state: &mut Environment, start_event: u64, max_events: u64) -> Result<Epoch> {
    let mut staged = state.clone();
    let frame = environment::step(&mut staged, Matcher::Indexed)?;
    let used = staged
        .native
        .world
        .next_event
        .checked_sub(start_event)
        .ok_or("event_counter_regressed")?;
    if used > max_events {
        return Err("event_budget_exceeded".into());
    }
    *state = staged;
    Ok(frame)
}
