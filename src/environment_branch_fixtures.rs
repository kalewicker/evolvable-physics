use crate::{
    core::*,
    environment::{self, Action, Environment, Epoch},
    environment_branches::{self, Branch, Request},
    environment_fixtures,
    interventions::Intervention,
    runtime::Matcher,
};
use serde::Serialize;
pub const FAMILIES: [&str; 2] = ["state_arrest", "replenished_activation"];
pub const ARMS: [&str; 5] = ["baseline", "sham", "target", "unrelated", "rescue"];
pub fn initial(seed: u64) -> Result<Environment> {
    let mut e = environment_fixtures::fixture("driven", seed)?;
    e.native.world.nodes.remove(&3);
    for id in 0..3 {
        e.native
            .world
            .nodes
            .insert(id + 3, e.native.world.nodes[&id].clone());
    }
    for id in 0..2 {
        let mut edge = e.native.world.edges[&id].clone();
        edge.ends.iter_mut().for_each(|n| *n += 3);
        e.native.world.edges.insert(id + 2, edge);
    }
    let extra: Vec<_> = e
        .channels
        .iter()
        .cloned()
        .map(|mut c| {
            c.id += 100;
            match &mut c.action {
                Action::Supply { node, .. } | Action::Extract { node, .. } => *node += 3,
                Action::Transport { edge, from, to, .. } => {
                    *edge += 2;
                    *from += 3;
                    *to += 3;
                }
            }
            c
        })
        .collect();
    e.channels.extend(extra);
    e.native.world.next_node = 6;
    e.native.world.next_edge = 4;
    e.native.world.matter_total = 34;
    e.native.world.activation_total = 4;
    e.initial_activation = 4;
    e.validate()?;
    Ok(e)
}
#[derive(Serialize)]
pub struct Arm {
    pub name: String,
    pub chain: Vec<Branch>,
    pub epochs: Vec<Epoch>,
}
#[derive(Serialize)]
pub struct Case {
    pub family: String,
    pub initial: Environment,
    pub warmup: Vec<Epoch>,
    pub source: Environment,
    pub arms: Vec<Arm>,
}
#[derive(Serialize)]
pub struct Suite {
    pub schema: String,
    pub scientific_status: String,
    pub cases: Vec<Case>,
}
pub fn suite() -> Result<Suite> {
    let mut cases = vec![];
    for family in FAMILIES {
        for seed in 0..16 {
            let initial = initial(seed)?;
            let mut source = initial.clone();
            let mut warmup = vec![];
            for _ in 0..2 {
                warmup.push(environment::step(&mut source, Matcher::Indexed)?);
            }
            let mut arms = vec![];
            for name in ARMS {
                let offset = if name == "unrelated" { 3 } else { 0 };
                let op = if family == "state_arrest" {
                    Intervention::SetState {
                        node: 1 + offset,
                        expected: 0,
                        value: if name == "sham" { 0 } else { 9 },
                    }
                } else {
                    Intervention::MoveResources {
                        from: offset,
                        to: 2 + offset,
                        matter: 0,
                        activation: if name == "sham" {
                            0
                        } else {
                            source.native.world.nodes[&offset].activation
                        },
                    }
                };
                let b = environment_branches::branch(
                    &source,
                    &Request::new(&source, if name == "baseline" { vec![] } else { vec![op] }),
                )?;
                let mut current = b.environment.clone();
                let mut chain = vec![b];
                if name == "rescue" {
                    let restore = if family == "state_arrest" {
                        Intervention::SetState {
                            node: 1,
                            expected: 9,
                            value: 0,
                        }
                    } else {
                        Intervention::MoveResources {
                            from: 2,
                            to: 0,
                            matter: 0,
                            activation: source.native.world.nodes[&0].activation,
                        }
                    };
                    let b = environment_branches::branch(
                        &current,
                        &Request::new(&current, vec![restore]),
                    )?;
                    current = b.environment.clone();
                    chain.push(b);
                }
                let mut reference = current.clone();
                let mut epochs = vec![];
                for _ in 0..6 {
                    let a = environment::step(&mut current, Matcher::Indexed)?;
                    let b = environment::step(&mut reference, Matcher::Reference)?;
                    if a != b {
                        return Err("environment_branch_matcher_mismatch".into());
                    }
                    epochs.push(a);
                }
                arms.push(Arm {
                    name: name.into(),
                    chain,
                    epochs,
                });
            }
            cases.push(Case {
                family: family.into(),
                initial,
                warmup,
                source,
                arms,
            });
        }
    }
    Ok(Suite {
        schema: "p00d-environment-branch-suite-v1".into(),
        scientific_status: "untested".into(),
        cases,
    })
}
