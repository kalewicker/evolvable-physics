use crate::{
    core::*,
    environment::{self, Action, Channel, Environment, Epoch},
    runtime::Matcher,
};
use serde::Serialize;
use std::collections::BTreeMap;
pub const MODES: [&str; 4] = ["closed", "local_transport", "driven", "blocked"];
pub fn fixture(mode: &str, seed: u64) -> Result<Environment> {
    if !MODES.contains(&mode) {
        return Err("unknown_environment_fixture".into());
    }
    let nodes = BTreeMap::from([
        (
            0,
            Node {
                kind: 2,
                state: 0,
                matter: 8,
                activation: 2,
            },
        ),
        (
            1,
            Node {
                kind: 1,
                state: 0,
                matter: 4,
                activation: 0,
            },
        ),
        (
            2,
            Node {
                kind: 2,
                state: 0,
                matter: 0,
                activation: 0,
            },
        ),
        (
            3,
            Node {
                kind: 1,
                state: 0,
                matter: 4,
                activation: 0,
            },
        ),
    ]);
    let native = Experiment {
        profile: crate::core::PROFILE.into(),
        seed,
        limits: Limits {
            max_candidates: 10_000,
            max_bindings: 100_000,
            max_nodes: 128,
            max_edges: 256,
        },
        rules: (0..2)
            .map(|s| Rule {
                id: s as u64,
                nodes: vec![NodePattern {
                    kind: 1,
                    state: Some(s),
                }],
                edges: vec![],
                absent: vec![],
                ops: vec![
                    Op::SetState {
                        node: 0,
                        value: 1 - s,
                    },
                    Op::Burn { node: 0, amount: 1 },
                ],
            })
            .collect(),
        world: World {
            nodes,
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
                        ends: vec![1, 2],
                    },
                ),
            ]),
            next_node: 4,
            next_edge: 2,
            epoch: 0,
            dissipated: 0,
            matter_total: 22,
            activation_total: 2,
            next_event: 0,
            writers: BTreeMap::new(),
        },
    };
    let mut channels = vec![];
    let channel = |id, action| Channel {
        id,
        start: 0,
        end: None,
        period: 1,
        action,
    };
    if ["driven", "blocked"].contains(&mode) {
        channels.push(channel(10, Action::Supply { node: 0, amount: 2 }));
    }
    if ["driven", "local_transport"].contains(&mode) {
        channels.push(channel(
            20,
            Action::Transport {
                edge: 0,
                from: 0,
                to: 1,
                matter: 0,
                activation: if mode == "driven" { 2 } else { 1 },
            },
        ));
        channels.push(Channel {
            id: 40,
            start: 1,
            end: Some(7),
            period: 2,
            action: Action::Transport {
                edge: 1,
                from: 1,
                to: 2,
                matter: 1,
                activation: 0,
            },
        });
    }
    if mode == "driven" {
        channels.push(channel(30, Action::Extract { node: 1, amount: 1 }));
    }
    let env = Environment {
        profile: environment::PROFILE.into(),
        channels,
        initial_activation: 2,
        injected: 0,
        extracted: 0,
        native,
    };
    env.validate()?;
    Ok(env)
}
#[derive(Serialize)]
pub struct Case {
    pub mode: String,
    pub initial: Environment,
    pub epochs: Vec<Epoch>,
}
#[derive(Serialize)]
pub struct Suite {
    pub schema: String,
    pub scientific_status: String,
    pub cases: Vec<Case>,
}
pub fn suite() -> Result<Suite> {
    let mut cases = vec![];
    for mode in MODES {
        for seed in 0..16 {
            let initial = fixture(mode, seed)?;
            let mut a = initial.clone();
            let mut b = a.clone();
            let mut epochs = vec![];
            for _ in 0..8 {
                let x = environment::step(&mut a, Matcher::Reference)?;
                let y = environment::step(&mut b, Matcher::Indexed)?;
                if x != y {
                    return Err("environment_matcher_mismatch".into());
                }
                epochs.push(x);
            }
            cases.push(Case {
                mode: mode.into(),
                initial,
                epochs,
            });
        }
    }
    Ok(Suite {
        schema: "p00c-environment-suite-v1".into(),
        scientific_status: "untested".into(),
        cases,
    })
}
