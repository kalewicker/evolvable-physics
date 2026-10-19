use crate::core::*;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::io::Write;
use std::path::Path;

#[derive(Clone, Copy, Debug)]
pub enum Matcher {
    Reference,
    Indexed,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Candidate {
    pub rule: u64,
    pub binding: Vec<u64>,
    pub priority: String,
    pub reads: BTreeSet<String>,
    pub writes: BTreeSet<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Event {
    pub id: u64,
    pub candidate: Candidate,
    pub parents: Vec<u64>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Frame {
    pub before: String,
    pub after: String,
    pub candidates: Vec<Candidate>,
    pub events: Vec<Event>,
    pub world: World,
}
fn node_key(id: u64) -> String {
    format!("node:{id}")
}
fn adj_key(id: u64) -> String {
    format!("adj:{id}")
}
fn add(a: u64, b: u64) -> Result<u64> {
    a.checked_add(b).ok_or("integer_overflow".into())
}
fn sub(a: u64, b: u64) -> Result<u64> {
    a.checked_sub(b).ok_or("insufficient_resource".into())
}
fn resolve(binding: &[u64], slot: usize, w: &World) -> Result<u64> {
    let id = *binding.get(slot).ok_or("invalid_slot")?;
    if !w.nodes.contains_key(&id) {
        return Err("deleted_slot".into());
    }
    Ok(id)
}
fn endpoints(binding: &[u64], slots: &[usize], w: &World) -> Result<Vec<u64>> {
    slots.iter().map(|s| resolve(binding, *s, w)).collect()
}
fn has_edge(w: &World, p: &EdgePattern, b: &[u64]) -> bool {
    let ends: Vec<_> = p.ends.iter().map(|s| b[*s]).collect();
    w.edges
        .values()
        .any(|e| e.kind == p.kind && e.class == p.class && e.ends == ends)
}

/// Pure checked execution against a private copy; caller publishes only on success.
pub(crate) fn apply(w: &World, rule: &Rule, original: &[u64]) -> Result<(World, BTreeSet<String>)> {
    let mut out = w.clone();
    let mut b = original.to_vec();
    let mut writes = BTreeSet::new();
    for op in &rule.ops {
        match op {
            Op::SetState { node, value } => {
                let id = resolve(&b, *node, &out)?;
                out.nodes.get_mut(&id).unwrap().state = *value;
                writes.insert(node_key(id));
            }
            Op::AddState { node, delta } => {
                let id = resolve(&b, *node, &out)?;
                let n = out.nodes.get_mut(&id).unwrap();
                n.state = n.state.checked_add(*delta).ok_or("state_overflow")?;
                writes.insert(node_key(id));
            }
            Op::Transfer {
                from,
                to,
                matter,
                activation,
            } => {
                let a = resolve(&b, *from, &out)?;
                let z = resolve(&b, *to, &out)?;
                if a == z {
                    return Err("self_transfer".into());
                }
                let n = out.nodes.get_mut(&a).unwrap();
                n.matter = sub(n.matter, *matter)?;
                n.activation = sub(n.activation, *activation)?;
                let n = out.nodes.get_mut(&z).unwrap();
                n.matter = add(n.matter, *matter)?;
                n.activation = add(n.activation, *activation)?;
                writes.extend([node_key(a), node_key(z)]);
            }
            Op::Burn { node, amount } => {
                let id = resolve(&b, *node, &out)?;
                let n = out.nodes.get_mut(&id).unwrap();
                n.activation = sub(n.activation, *amount)?;
                out.dissipated = add(out.dissipated, *amount)?;
                writes.insert(node_key(id));
            }
            Op::CreateNode {
                account,
                kind,
                state,
            } => {
                let a = resolve(&b, *account, &out)?;
                let n = out.nodes.get_mut(&a).unwrap();
                n.matter = sub(n.matter, 1)?;
                let id = out.next_node;
                out.next_node = add(id, 1)?;
                out.nodes.insert(
                    id,
                    Node {
                        kind: *kind,
                        state: *state,
                        matter: 0,
                        activation: 0,
                    },
                );
                b.push(id);
                writes.extend([node_key(a), node_key(id), adj_key(id)]);
            }
            Op::DeleteNode { node, recipient } => {
                let id = resolve(&b, *node, &out)?;
                let a = resolve(&b, *recipient, &out)?;
                if id == a {
                    return Err("self_delete_recipient".into());
                }
                if out.edges.values().any(|e| e.ends.contains(&id)) {
                    return Err("dangling_edge".into());
                }
                let old = out.nodes.remove(&id).unwrap();
                let n = out.nodes.get_mut(&a).unwrap();
                n.matter = add(n.matter, add(old.matter, 1)?)?;
                n.activation = add(n.activation, old.activation)?;
                writes.extend([node_key(a), node_key(id), adj_key(id)]);
            }
            Op::CreateEdge {
                account,
                kind,
                ends,
            } => {
                let a = resolve(&b, *account, &out)?;
                let ids = endpoints(&b, ends, &out)?;
                if out
                    .edges
                    .values()
                    .any(|e| e.class == Class::Structural && e.kind == *kind && e.ends == ids)
                {
                    return Err("duplicate_edge".into());
                }
                let n = out.nodes.get_mut(&a).unwrap();
                n.matter = sub(n.matter, 1)?;
                let id = out.next_edge;
                out.next_edge = add(id, 1)?;
                out.edges.insert(
                    id,
                    Edge {
                        class: Class::Structural,
                        kind: *kind,
                        ends: ids.clone(),
                    },
                );
                writes.insert(node_key(a));
                writes.extend(ids.into_iter().map(adj_key));
            }
            Op::DeleteEdge {
                account,
                kind,
                ends,
            } => {
                let a = resolve(&b, *account, &out)?;
                let ids = endpoints(&b, ends, &out)?;
                let id = out
                    .edges
                    .iter()
                    .find(|(_, e)| e.class == Class::Structural && e.kind == *kind && e.ends == ids)
                    .map(|(id, _)| *id)
                    .ok_or("missing_edge")?;
                out.edges.remove(&id);
                let n = out.nodes.get_mut(&a).unwrap();
                n.matter = add(n.matter, 1)?;
                writes.insert(node_key(a));
                writes.extend(ids.into_iter().map(adj_key));
            }
        }
    }
    out.validate()?;
    Ok((out, writes))
}

pub fn enumerate(exp: &Experiment, matcher: Matcher) -> Result<Vec<Candidate>> {
    exp.validate()?;
    let mut result = Vec::new();
    let mut visits = 0usize;
    let mut matches = 0usize;
    let mut index: BTreeMap<u16, Vec<u64>> = BTreeMap::new();
    for (id, node) in &exp.world.nodes {
        index.entry(node.kind).or_default().push(*id);
    }
    let mut rules: Vec<_> = exp.rules.iter().collect();
    rules.sort_by_key(|r| r.id);
    for rule in rules {
        let choices: Vec<Vec<u64>> = rule
            .nodes
            .iter()
            .map(|p| match matcher {
                Matcher::Reference => exp
                    .world
                    .nodes
                    .iter()
                    .filter(|(_, n)| n.kind == p.kind)
                    .map(|(id, _)| *id)
                    .collect(),
                Matcher::Indexed => index.get(&p.kind).cloned().unwrap_or_default(),
            })
            .collect();
        // Explicit stack: stable lexicographic order and identical budget semantics in both matchers.
        let mut stack = vec![Vec::new()];
        while let Some(b) = stack.pop() {
            if b.len() < rule.nodes.len() {
                for id in choices[b.len()].iter().rev() {
                    if b.contains(id) {
                        continue;
                    }
                    let p = &rule.nodes[b.len()];
                    if p.state.is_some_and(|s| exp.world.nodes[id].state != s) {
                        continue;
                    }
                    visits = visits.checked_add(1).ok_or("binding_budget_exceeded")?;
                    if visits > exp.limits.max_bindings {
                        return Err("binding_budget_exceeded".into());
                    }
                    let mut next = b.clone();
                    next.push(*id);
                    stack.push(next);
                }
                continue;
            }
            if !rule.edges.iter().all(|e| has_edge(&exp.world, e, &b))
                || rule.absent.iter().any(|e| has_edge(&exp.world, e, &b))
            {
                continue;
            }
            matches += 1;
            if matches > exp.limits.max_candidates {
                return Err("match_budget_exceeded".into());
            }
            // Unaffordable or otherwise inapplicable rewrites are not enabled transitions.
            let Ok((_, writes)) = apply(&exp.world, rule, &b) else {
                continue;
            };
            let reads = b
                .iter()
                .flat_map(|id| [node_key(*id), adj_key(*id)])
                .collect();
            // Created IDs are allocated during canonical commit, not during candidate preparation.
            let writes = writes
                .into_iter()
                .filter(|key| {
                    let id: u64 = key.split(':').nth(1).unwrap().parse().unwrap();
                    exp.world.nodes.contains_key(&id)
                })
                .collect();
            let priority = digest(&("priority-v1", exp.seed, exp.world.epoch, rule.id, &b));
            result.push(Candidate {
                rule: rule.id,
                binding: b,
                priority,
                reads,
                writes,
            });
        }
    }
    result
        .sort_by(|a, b| (&a.priority, a.rule, &a.binding).cmp(&(&b.priority, b.rule, &b.binding)));
    Ok(result)
}
pub fn step(exp: &mut Experiment, matcher: Matcher) -> Result<Frame> {
    let candidates = enumerate(exp, matcher)?;
    let mut selected = Vec::new();
    let mut reads = BTreeSet::new();
    let mut writes = BTreeSet::new();
    for c in &candidates {
        if !c.writes.is_disjoint(&reads)
            || !c.writes.is_disjoint(&writes)
            || !c.reads.is_disjoint(&writes)
        {
            continue;
        }
        reads.extend(c.reads.clone());
        writes.extend(c.writes.clone());
        selected.push(c);
    }
    selected.sort_by(|a, b| (a.rule, &a.binding).cmp(&(b.rule, &b.binding)));
    let mut world = exp.world.clone();
    let mut events = Vec::new();
    for c in selected {
        let rule = exp.rules.iter().find(|r| r.id == c.rule).unwrap();
        let parents: BTreeSet<u64> = c
            .reads
            .iter()
            .chain(&c.writes)
            .filter_map(|k| world.writers.get(k).copied())
            .collect();
        let (mut next, all_writes) = apply(&world, rule, &c.binding)?;
        let id = world.next_event;
        next.next_event = add(id, 1)?;
        for key in all_writes {
            next.writers.insert(key, id);
        }
        world = next;
        events.push(Event {
            id,
            candidate: c.clone(),
            parents: parents.into_iter().collect(),
        });
    }
    world.epoch = add(world.epoch, 1)?;
    world.validate()?;
    if world.nodes.len() > exp.limits.max_nodes || world.edges.len() > exp.limits.max_edges {
        return Err("world_size_exceeded".into());
    }
    let frame = Frame {
        before: digest(&exp.world),
        after: digest(&world),
        candidates,
        events,
        world: world.clone(),
    };
    exp.world = world;
    Ok(frame)
}

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Checkpoint {
    schema: String,
    digest: String,
    payload: Experiment,
}
pub fn save(path: &Path, exp: &Experiment) -> Result<()> {
    exp.validate()?;
    let data = serde_json::to_vec_pretty(&Checkpoint {
        schema: "checkpoint-v1".into(),
        digest: digest(exp),
        payload: exp.clone(),
    })
    .map_err(|e| e.to_string())?;
    publish_checkpoint(path, &data)
}
pub(crate) fn publish_checkpoint(path: &Path, data: &[u8]) -> Result<()> {
    // The final name is linked only after a complete, synced file exists; no overwrite.
    let tmp = path.with_extension("pending");
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&tmp)
        .map_err(|e| e.to_string())?;
    file.write_all(data).map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())?;
    std::fs::hard_link(&tmp, path).map_err(|e| e.to_string())?;
    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    std::fs::File::open(parent)
        .and_then(|d| d.sync_all())
        .map_err(|e| e.to_string())?;
    std::fs::remove_file(&tmp).map_err(|e| e.to_string())?;
    std::fs::File::open(parent)
        .and_then(|d| d.sync_all())
        .map_err(|e| e.to_string())?;
    Ok(())
}
pub fn load(path: &Path) -> Result<Experiment> {
    let data = std::fs::read(path).map_err(|e| e.to_string())?;
    let cp: Checkpoint = serde_json::from_slice(&data).map_err(|e| e.to_string())?;
    if cp.schema != "checkpoint-v1" || cp.digest != digest(&cp.payload) {
        return Err("checkpoint_identity_mismatch".into());
    }
    cp.payload.validate()?;
    Ok(cp.payload)
}
