use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub type Result<T> = std::result::Result<T, String>;
pub const PROFILE: &str = "p00a-local-closed-v1";

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Node {
    pub kind: u16,
    pub state: i32,
    pub matter: u64,
    pub activation: u64,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum Class {
    Contact,
    Structural,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Edge {
    pub class: Class,
    pub kind: u16,
    pub ends: Vec<u64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct World {
    pub nodes: BTreeMap<u64, Node>,
    pub edges: BTreeMap<u64, Edge>,
    pub next_node: u64,
    pub next_edge: u64,
    pub epoch: u64,
    pub dissipated: u64,
    pub matter_total: u64,
    pub activation_total: u64,
    pub next_event: u64,
    pub writers: BTreeMap<String, u64>,
}
impl World {
    pub fn validate(&self) -> Result<()> {
        if self.nodes.keys().any(|id| *id >= self.next_node)
            || self.edges.keys().any(|id| *id >= self.next_edge)
        {
            return Err("allocator_not_ahead".into());
        }
        let mut unique = BTreeSet::new();
        for e in self.edges.values() {
            if !(2..=4).contains(&e.ends.len())
                || e.ends.iter().collect::<BTreeSet<_>>().len() != e.ends.len()
                || e.ends.iter().any(|id| !self.nodes.contains_key(id))
            {
                return Err("invalid_endpoints".into());
            }
            if !unique.insert((&e.class, e.kind, &e.ends)) {
                return Err("duplicate_edge".into());
            }
        }
        let matter = self
            .nodes
            .values()
            .map(|n| n.matter as u128 + 1)
            .sum::<u128>()
            + self.edges.len() as u128;
        let activation = self
            .nodes
            .values()
            .map(|n| n.activation as u128)
            .sum::<u128>()
            + self.dissipated as u128;
        if matter != self.matter_total as u128 {
            return Err("matter_not_conserved".into());
        }
        if activation != self.activation_total as u128 {
            return Err("activation_not_conserved".into());
        }
        if self.writers.values().any(|e| *e >= self.next_event) {
            return Err("invalid_writer".into());
        }
        Ok(())
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct NodePattern {
    pub kind: u16,
    pub state: Option<i32>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct EdgePattern {
    pub class: Class,
    pub kind: u16,
    pub ends: Vec<usize>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "op", deny_unknown_fields)]
pub enum Op {
    SetState {
        node: usize,
        value: i32,
    },
    AddState {
        node: usize,
        delta: i32,
    },
    Transfer {
        from: usize,
        to: usize,
        matter: u64,
        activation: u64,
    },
    Burn {
        node: usize,
        amount: u64,
    },
    CreateNode {
        account: usize,
        kind: u16,
        state: i32,
    },
    DeleteNode {
        node: usize,
        recipient: usize,
    },
    CreateEdge {
        account: usize,
        kind: u16,
        ends: Vec<usize>,
    },
    DeleteEdge {
        account: usize,
        kind: u16,
        ends: Vec<usize>,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Rule {
    pub id: u64,
    pub nodes: Vec<NodePattern>,
    pub edges: Vec<EdgePattern>,
    pub absent: Vec<EdgePattern>,
    pub ops: Vec<Op>,
}
impl Rule {
    pub fn validate(&self) -> Result<()> {
        let n = self.nodes.len();
        if !(1..=6).contains(&n)
            || self.edges.len() > 8
            || self.absent.len() > 8
            || self.ops.is_empty()
            || self.ops.len() > 8
        {
            return Err("grammar_bounds".into());
        }
        for p in self.edges.iter().chain(&self.absent) {
            validate_ends(&p.ends, n)?;
        }
        let mut reached = BTreeSet::from([0]);
        loop {
            let before = reached.len();
            for e in &self.edges {
                if e.ends.iter().any(|v| reached.contains(v)) {
                    reached.extend(&e.ends);
                }
            }
            if reached.len() == before {
                break;
            }
        }
        if reached.len() != n {
            return Err("disconnected_pattern".into());
        }
        let mut slots = n;
        for op in &self.ops {
            let refs = match op {
                Op::SetState { node, .. } | Op::AddState { node, .. } | Op::Burn { node, .. } => {
                    vec![*node]
                }
                Op::Transfer { from, to, .. } => vec![*from, *to],
                Op::DeleteNode { node, recipient } => vec![*node, *recipient],
                Op::CreateNode { account, .. } => vec![*account],
                Op::CreateEdge { account, ends, .. } | Op::DeleteEdge { account, ends, .. } => {
                    validate_ends(ends, slots)?;
                    let mut v = ends.clone();
                    v.push(*account);
                    v
                }
            };
            if refs.iter().any(|r| *r >= slots) {
                return Err("invalid_slot".into());
            }
            if matches!(op, Op::CreateNode { .. }) {
                slots += 1;
            }
        }
        Ok(())
    }
}
fn validate_ends(ends: &[usize], slots: usize) -> Result<()> {
    if !(2..=4).contains(&ends.len())
        || ends.iter().any(|r| *r >= slots)
        || ends.iter().collect::<BTreeSet<_>>().len() != ends.len()
    {
        return Err("invalid_pattern_endpoints".into());
    }
    Ok(())
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Limits {
    pub max_candidates: usize,
    pub max_bindings: usize,
    pub max_nodes: usize,
    pub max_edges: usize,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Experiment {
    pub profile: String,
    pub seed: u64,
    pub rules: Vec<Rule>,
    pub limits: Limits,
    pub world: World,
}
impl Experiment {
    pub fn validate(&self) -> Result<()> {
        if self.profile != PROFILE {
            return Err("unknown_profile".into());
        }
        self.world.validate()?;
        if self.world.nodes.len() > self.limits.max_nodes
            || self.world.edges.len() > self.limits.max_edges
        {
            return Err("world_size_exceeded".into());
        }
        let mut ids = BTreeSet::new();
        for r in &self.rules {
            r.validate()?;
            if !ids.insert(r.id) {
                return Err("duplicate_rule_id".into());
            }
        }
        Ok(())
    }
}
pub fn canonical<T: Serialize>(value: &T) -> Vec<u8> {
    // serde_json's default Value object map is a BTreeMap, recursively sorting keys.
    serde_json::to_vec(&serde_json::to_value(value).expect("serializable value")).expect("JSON")
}
pub fn digest<T: Serialize>(value: &T) -> String {
    format!("{:x}", Sha256::digest(canonical(value)))
}
