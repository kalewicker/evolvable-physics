//! Versioned environment orchestration around the unchanged closed native kernel.
use crate::{
    core::*,
    runtime::{self, Frame, Matcher, TraceMode},
};
use serde::{Deserialize, Serialize};
use std::{collections::BTreeSet, path::Path};
pub const PROFILE: &str = "p00c-local-driven-v1";
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "op", deny_unknown_fields)]
pub enum Action {
    Supply {
        node: u64,
        amount: u64,
    },
    Extract {
        node: u64,
        amount: u64,
    },
    Transport {
        edge: u64,
        from: u64,
        to: u64,
        matter: u64,
        activation: u64,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Channel {
    pub id: u64,
    pub start: u64,
    pub end: Option<u64>,
    pub period: u64,
    pub action: Action,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Environment {
    pub profile: String,
    pub channels: Vec<Channel>,
    pub initial_activation: u64,
    pub injected: u64,
    pub extracted: u64,
    pub native: Experiment,
}
impl Environment {
    pub fn validate(&self) -> Result<()> {
        if self.profile != PROFILE {
            return Err("unknown_environment_profile".into());
        }
        self.native.validate()?;
        if self.initial_activation as u128 + self.injected as u128
            != self.native.world.activation_total as u128 + self.extracted as u128
        {
            return Err("environment_balance_mismatch".into());
        }
        if self.channels.len() > 32 {
            return Err("environment_channel_limit".into());
        }
        let mut ids = BTreeSet::new();
        for c in &self.channels {
            if !ids.insert(c.id) || c.period == 0 || c.end.is_some_and(|end| end <= c.start) {
                return Err("invalid_channel_schedule".into());
            }
            let nodes = match &c.action {
                Action::Supply { node, amount } | Action::Extract { node, amount } => {
                    if *amount == 0 {
                        return Err("zero_environment_amount".into());
                    }
                    vec![*node]
                }
                Action::Transport {
                    edge,
                    from,
                    to,
                    matter,
                    activation,
                } => {
                    if *matter == 0 && *activation == 0 {
                        return Err("zero_environment_amount".into());
                    }
                    let e = self
                        .native
                        .world
                        .edges
                        .get(edge)
                        .ok_or("missing_transport_contact")?;
                    if e.class != Class::Contact || e.ends != vec![*from, *to] {
                        return Err("invalid_transport_contact".into());
                    }
                    vec![*from, *to]
                }
            };
            if nodes
                .iter()
                .any(|id| !self.native.world.nodes.contains_key(id))
            {
                return Err("missing_environment_node".into());
            }
        }
        Ok(())
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Event {
    pub channel: u64,
    pub event_id: Option<u64>,
    pub status: String,
    pub reads: BTreeSet<String>,
    pub writes: BTreeSet<String>,
    pub parents: Vec<u64>,
    pub before: String,
    pub after: String,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Epoch {
    pub before: String,
    pub after: String,
    pub environment_events: Vec<Event>,
    pub prepared: Experiment,
    pub native_frame: Frame,
    pub state: Environment,
}
fn add(a: u64, b: u64) -> Result<u64> {
    a.checked_add(b).ok_or("environment_overflow".into())
}
pub fn step(env: &mut Environment, matcher: Matcher) -> Result<Epoch> {
    Ok(step_with_logging(env, matcher, TraceMode::Full)?.expect("full environment trace"))
}
pub fn step_with_logging(
    env: &mut Environment,
    matcher: Matcher,
    mode: TraceMode,
) -> Result<Option<Epoch>> {
    env.validate()?;
    let mut out = env.clone();
    let mut channels = env.channels.clone();
    channels.sort_by_key(|c| c.id);
    let mut events = Vec::new();
    let epoch = out.native.world.epoch;
    for c in channels {
        if epoch < c.start
            || c.end.is_some_and(|end| epoch >= end)
            || !(epoch - c.start).is_multiple_of(c.period)
        {
            continue;
        }
        let before = if mode == TraceMode::Full {
            Some(digest(&out))
        } else {
            None
        };
        let mut reads = BTreeSet::new();
        let mut writes = BTreeSet::new();
        let w = &mut out.native.world;
        let enabled = match c.action {
            Action::Supply { node, amount } => {
                reads.insert(format!("node:{node}"));
                writes.insert(format!("node:{node}"));
                let n = w.nodes.get_mut(&node).unwrap();
                n.activation = add(n.activation, amount)?;
                w.activation_total = add(w.activation_total, amount)?;
                out.injected = add(out.injected, amount)?;
                true
            }
            Action::Extract { node, amount } => {
                reads.insert(format!("node:{node}"));
                let n = w.nodes.get_mut(&node).unwrap();
                if n.activation < amount {
                    false
                } else {
                    writes.insert(format!("node:{node}"));
                    n.activation -= amount;
                    w.activation_total = w
                        .activation_total
                        .checked_sub(amount)
                        .ok_or("environment_balance_mismatch")?;
                    out.extracted = add(out.extracted, amount)?;
                    true
                }
            }
            Action::Transport {
                from,
                to,
                matter,
                activation,
                ..
            } => {
                reads.extend([
                    format!("node:{from}"),
                    format!("node:{to}"),
                    format!("adj:{from}"),
                    format!("adj:{to}"),
                ]);
                let n = &w.nodes[&from];
                if n.matter < matter || n.activation < activation {
                    false
                } else {
                    let n = w.nodes.get_mut(&from).unwrap();
                    n.matter -= matter;
                    n.activation -= activation;
                    let n = w.nodes.get_mut(&to).unwrap();
                    n.matter = add(n.matter, matter)?;
                    n.activation = add(n.activation, activation)?;
                    writes.extend([format!("node:{from}"), format!("node:{to}")]);
                    true
                }
            }
        };
        let parents: BTreeSet<_> = if mode == TraceMode::Full {
            reads
                .iter()
                .filter_map(|k| w.writers.get(k).copied())
                .collect()
        } else {
            BTreeSet::new()
        };
        let event_id = if enabled {
            let id = w.next_event;
            w.next_event = add(id, 1)?;
            for key in &writes {
                w.writers.insert(key.clone(), id);
            }
            Some(id)
        } else {
            None
        };
        out.validate()?;
        if mode == TraceMode::Full {
            events.push(Event {
                channel: c.id,
                event_id,
                status: if enabled {
                    "applied"
                } else {
                    "insufficient_resource"
                }
                .into(),
                reads,
                writes,
                parents: parents.into_iter().collect(),
                before: before.expect("full environment before"),
                after: digest(&out),
            });
        }
    }
    let prepared = if mode == TraceMode::Full {
        Some(out.native.clone())
    } else {
        None
    };
    let native_frame = runtime::step_with_logging(&mut out.native, matcher, mode)?;
    out.validate()?;
    let frame = if mode == TraceMode::Full {
        Some(Epoch {
            before: digest(env),
            after: digest(&out),
            environment_events: events,
            prepared: prepared.expect("full prepared"),
            native_frame: native_frame.expect("full native frame"),
            state: out.clone(),
        })
    } else {
        None
    };
    *env = out;
    Ok(frame)
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Checkpoint {
    schema: String,
    digest: String,
    payload: Environment,
}
pub fn save(path: &Path, env: &Environment) -> Result<()> {
    env.validate()?;
    let bytes = serde_json::to_vec_pretty(&Checkpoint {
        schema: "environment-checkpoint-v1".into(),
        digest: digest(env),
        payload: env.clone(),
    })
    .map_err(|e| e.to_string())?;
    runtime::publish_checkpoint(path, &bytes)
}
pub fn load(path: &Path) -> Result<Environment> {
    let cp: Checkpoint = serde_json::from_slice(&std::fs::read(path).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    if cp.schema != "environment-checkpoint-v1" || cp.digest != digest(&cp.payload) {
        return Err("environment_checkpoint_mismatch".into());
    }
    cp.payload.validate()?;
    Ok(cp.payload)
}
