//! Host interventions are recorded separately from native rewrite laws.
use crate::core::*;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

pub const SCHEMA: &str = "intervention-v1";
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "op", deny_unknown_fields)]
pub enum Intervention {
    SetState {
        node: u64,
        expected: i32,
        value: i32,
    },
    MoveResources {
        from: u64,
        to: u64,
        matter: u64,
        activation: u64,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema: String,
    pub expected_source: String,
    pub operations: Vec<Intervention>,
}
impl Request {
    pub fn new(source: &Experiment, operations: Vec<Intervention>) -> Self {
        Self {
            schema: SCHEMA.into(),
            expected_source: digest(source),
            operations,
        }
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Receipt {
    pub schema: String,
    pub request_digest: String,
    pub before: String,
    pub after: String,
    pub epoch: u64,
    pub event_id: Option<u64>,
    pub reads: BTreeSet<String>,
    pub writes: BTreeSet<String>,
    pub parents: Vec<u64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Branch {
    pub request: Request,
    pub receipt: Receipt,
    pub experiment: Experiment,
}
/// Returns a new branch. The source is immutable even if any operation fails.
pub fn branch(source: &Experiment, request: &Request) -> Result<Branch> {
    source.validate()?;
    if request.schema != SCHEMA {
        return Err("unknown_intervention_schema".into());
    }
    if request.expected_source != digest(source) {
        return Err("stale_intervention_source".into());
    }
    if request.operations.len() > 8 {
        return Err("intervention_operation_limit".into());
    }
    let mut out = source.clone();
    let mut keys = BTreeSet::new();
    for op in &request.operations {
        match op {
            Intervention::SetState {
                node,
                expected,
                value,
            } => {
                let n = out
                    .world
                    .nodes
                    .get_mut(node)
                    .ok_or("intervention_missing_node")?;
                if n.state != *expected {
                    return Err("intervention_state_precondition".into());
                }
                n.state = *value;
                keys.insert(format!("node:{node}"));
            }
            Intervention::MoveResources {
                from,
                to,
                matter,
                activation,
            } => {
                if from == to {
                    return Err("intervention_self_transfer".into());
                }
                let a = out
                    .world
                    .nodes
                    .get_mut(from)
                    .ok_or("intervention_missing_node")?;
                a.matter = a
                    .matter
                    .checked_sub(*matter)
                    .ok_or("intervention_insufficient_resource")?;
                a.activation = a
                    .activation
                    .checked_sub(*activation)
                    .ok_or("intervention_insufficient_resource")?;
                let b = out
                    .world
                    .nodes
                    .get_mut(to)
                    .ok_or("intervention_missing_node")?;
                b.matter = b
                    .matter
                    .checked_add(*matter)
                    .ok_or("intervention_overflow")?;
                b.activation = b
                    .activation
                    .checked_add(*activation)
                    .ok_or("intervention_overflow")?;
                keys.extend([format!("node:{from}"), format!("node:{to}")]);
            }
        }
    }
    let parents: BTreeSet<_> = keys
        .iter()
        .filter_map(|k| source.world.writers.get(k).copied())
        .collect();
    let event_id = if request.operations.is_empty() {
        None
    } else {
        let id = out.world.next_event;
        out.world.next_event = id.checked_add(1).ok_or("intervention_overflow")?;
        for key in &keys {
            out.world.writers.insert(key.clone(), id);
        }
        Some(id)
    };
    out.validate()?;
    Ok(Branch {
        request: request.clone(),
        receipt: Receipt {
            schema: "intervention-receipt-v1".into(),
            request_digest: digest(request),
            before: digest(source),
            after: digest(&out),
            epoch: source.world.epoch,
            event_id,
            reads: keys.clone(),
            writes: keys,
            parents: parents.into_iter().collect(),
        },
        experiment: out,
    })
}
