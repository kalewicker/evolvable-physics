//! Generator-v2 sampler. Hash-keyed draws require a separate frozen execution admission.
use causal_alife::{
    core::*,
    environment::{self, Environment},
};
use std::collections::BTreeMap;

pub const GENERATOR: &str = "p01-generator-v2";
// Deliberately uses modulo reduction, including its tiny bias; no rejection or repair.
fn draw(proposal: u64, initial: u64, field: &str, index: u64, n: u64) -> u64 {
    let h = digest(&(GENERATOR, proposal, initial, field, index));
    u64::from_str_radix(&h[..16], 16).unwrap() % n
}
fn construct(
    proposal: u64,
    initial: u64,
    draw: impl Fn(u64, u64, &str, u64, u64) -> u64,
) -> Result<Environment> {
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
                class: if form >= 6 || (form == 3 && d("route", 2) == 1) {
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
            4 => vec![
                Op::CreateNode {
                    account: 0,
                    kind: 1 + d("new_kind", 3) as u16,
                    state: d("value", 3) as i32,
                },
                Op::CreateEdge {
                    account: 0,
                    kind: 0,
                    ends: vec![0, 1],
                },
                Op::Transfer {
                    from: 0,
                    to: 1,
                    matter: 1,
                    activation: 1,
                },
                Op::Burn { node: 0, amount: 1 },
            ],
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
                    account: 0,
                    kind: 0,
                    ends: vec![0, 1],
                },
                Op::DeleteNode {
                    node: 1,
                    recipient: 0,
                },
                Op::Burn { node: 0, amount: 1 },
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

fn run() -> Result<()> {
    use serde_json::{Value, json};
    use sha2::{Digest, Sha256};
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 {
        return Err("usage: generator-v2 PROTOCOL.json EXECUTION_ADMISSION.json SLOT".into());
    }
    let raw = std::fs::read(&args[1]).map_err(|e| e.to_string())?;
    let p: Value = serde_json::from_slice(&raw).map_err(|e| e.to_string())?;
    let a: Value = serde_json::from_slice(&std::fs::read(&args[2]).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let slot: u64 = args[3].parse().map_err(|_| "invalid_slot")?;
    let ids: Vec<u64> = (4000..4016).collect();
    if p["schema"] != "p01g-generator-v2-feasibility-registration-v1"
        || p["proposal_ids"] != json!(ids)
        || p["initial_state_ids"] != json!([0, 1, 2, 3])
        || p["trajectory_denominator"] != 64
        || slot >= 64
        || a["schema"] != "p01g-execution-admission-v1"
        || a["law_sampling_admitted"] != true
        || a["fixed_slots"] != 64
        || a["protocol_sha256"] != format!("{:x}", Sha256::digest(&raw))
        || a["e01_authorized"] != false
    {
        return Err("sampling_not_admitted".into());
    }
    let initial = construct(4000 + slot / 4, slot % 4, draw)?;
    println!("{}", String::from_utf8(canonical(&initial)).unwrap());
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    // The injected fields are literal fixture values, never hash-keyed laws.
    fn fields(_: u64, _: u64, field: &str, index: u64, n: u64) -> u64 {
        match field {
            "form" => index,
            "route" => 1,
            "state0" | "state1" => 3,
            "structural" => 1,
            _ => n - 1,
        }
    }
    #[test]
    fn mock_all_templates_and_accounting() {
        let e = construct(0, 0, fields).unwrap();
        let v = serde_json::to_value(&e).unwrap();
        assert_eq!(v["native"]["world"]["matter_total"], 88);
        assert_eq!(v["native"]["world"]["next_edge"], 16);
        assert_eq!(v["native"]["world"]["next_node"], 8);
        let rules = &v["native"]["rules"];
        assert_eq!(rules[3]["edges"][0]["class"], "Structural");
        assert_eq!(rules[3]["ops"][0]["activation"], 2);
        assert_eq!(
            rules[4]["ops"],
            json!([
            {"op":"CreateNode","account":0,"kind":3,"state":2},
            {"op":"CreateEdge","account":0,"kind":0,"ends":[0,1]},
            {"op":"Transfer","from":0,"to":1,"matter":1,"activation":1},
            {"op":"Burn","node":0,"amount":1}])
        );
        assert_eq!(
            rules[7]["ops"],
            json!([
            {"op":"DeleteEdge","account":0,"kind":0,"ends":[0,1]},
            {"op":"DeleteNode","node":1,"recipient":0},
            {"op":"Burn","node":0,"amount":1}])
        );
        for rule in &e.native.rules {
            rule.validate().unwrap();
        }
    }
    #[test]
    fn mock_contact_route_and_no_initial_structural_edges() {
        let e = construct(0, 3, |p, i, f, j, n| {
            if f == "route" || f == "structural" {
                0
            } else {
                fields(p, i, f, j, n)
            }
        })
        .unwrap();
        assert_eq!(e.native.world.edges.len(), 8);
        assert_eq!(e.native.world.matter_total, 80);
        assert_eq!(e.native.rules[3].edges[0].class, Class::Contact);
    }
    #[test]
    fn invalid_initial_rejected_before_any_draw() {
        assert!(construct(0, 4, |_, _, _, _, _| panic!("draw called")).is_err());
    }
}
