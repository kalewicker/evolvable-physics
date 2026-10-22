//! Literal-field construction only; no sampler, kernel, matcher or transitions.
use serde_json::{Value, json};
use std::io::{self, BufRead, Write};

type Checked<T> = Result<T, &'static str>;
const INVALID: &str = "invalid_literal_input";
const DOMAINS: [(&str, u64); 11] = [
    ("form", 8),
    ("kind0", 3),
    ("kind1", 3),
    ("new_kind", 3),
    ("state0", 4),
    ("state1", 4),
    ("value", 3),
    ("sign", 2),
    ("amount", 2),
    ("matter", 2),
    ("route", 2),
];

fn bounded(value: &Value, modulus: u64) -> Checked<u64> {
    value.as_u64().filter(|v| *v < modulus).ok_or(INVALID)
}

struct LiteralSource<'a> {
    request: &'a Value,
    reads: Vec<Value>,
}
impl<'a> LiteralSource<'a> {
    fn new(r: &'a Value) -> Checked<Self> {
        let map = r["map"].as_array().ok_or(INVALID)?;
        if map.len() != 3 || map.iter().any(|v| !matches!(v.as_u64(), Some(1..=3))) {
            return Err(INVALID);
        }
        let states = r["state_map"].as_array().ok_or(INVALID)?;
        if states.len() != 3 {
            return Err(INVALID);
        }
        for state in states {
            bounded(state, 3)?;
        }
        let fields: Vec<&Value> = if r["mode"] == "assembly" {
            let initial = bounded(&r["initial_id"], 4)?;
            let input = &r["initial_fields"];
            if input["id"].as_u64() != Some(initial) {
                return Err(INVALID);
            }
            for (field, n) in [("node_kind", 3), ("node_state", 3), ("structural", 2)] {
                let values = input[field].as_array().ok_or(INVALID)?;
                if values.len() != 8 {
                    return Err(INVALID);
                }
                for value in values {
                    bounded(value, n)?;
                }
            }
            bounded(&input["scheduler"], u64::MAX)?;
            let rules = r["rule_fields"].as_array().ok_or(INVALID)?;
            if rules.len() != 8 {
                return Err(INVALID);
            }
            rules.iter().collect()
        } else {
            bounded(&r["rule_id"], 8)?;
            vec![&r["fields"]]
        };
        for row in fields {
            let object = row.as_object().ok_or(INVALID)?;
            if object.len() != DOMAINS.len() {
                return Err(INVALID);
            }
            for (field, n) in DOMAINS {
                bounded(&row[field], n)?;
            }
        }
        Ok(Self {
            request: r,
            reads: vec![],
        })
    }
    fn read(&mut self, initial: u64, field: &str, index: u64, modulus: u64) -> Checked<u64> {
        let r = self.request;
        let value = if field == "child_kind_by_donor" {
            if initial != 0 || index >= 3 || modulus != 3 {
                return Err(INVALID);
            }
            r["map"][index as usize].as_u64().ok_or(INVALID)? - 1
        } else if field == "role_state_by_kind" {
            if initial != 0 || index >= 3 || modulus != 3 {
                return Err(INVALID);
            }
            bounded(&r["state_map"][index as usize], 3)?
        } else if let Some((_, n)) = DOMAINS.iter().find(|(name, _)| *name == field) {
            if initial != 0 || index >= 8 || modulus != *n {
                return Err(INVALID);
            }
            let row = if r["mode"] == "rule" {
                if r["rule_id"].as_u64() != Some(index) {
                    return Err(INVALID);
                }
                &r["fields"]
            } else {
                &r["rule_fields"][index as usize]
            };
            bounded(&row[field], modulus)?
        } else {
            if r["mode"] != "assembly" || r["initial_id"].as_u64() != Some(initial) {
                return Err(INVALID);
            }
            let n = match field {
                "node_kind" | "node_state" => 3,
                "structural" => 2,
                "scheduler" => u64::MAX,
                _ => return Err(INVALID),
            };
            if modulus != n {
                return Err(INVALID);
            }
            let value = if field == "scheduler" {
                if index != 0 {
                    return Err(INVALID);
                }
                &r["initial_fields"][field]
            } else {
                if index >= 8 {
                    return Err(INVALID);
                }
                &r["initial_fields"][field][index as usize]
            };
            bounded(value, modulus)?
        };
        self.reads
            .push(json!([initial, field, index, modulus, value]));
        Ok(value)
    }
}

fn rule(
    id: u64,
    map: &[u64],
    states: &[u64],
    source: &mut impl FnMut(u64, &str, u64, u64) -> Checked<u64>,
) -> Checked<Value> {
    let mut values = serde_json::Map::new();
    for (field, n) in DOMAINS {
        values.insert(field.into(), json!(source(0, field, id, n)?));
    }
    let f = |name: &str| values[name].as_u64().unwrap();
    let form = f("form");
    let pair = matches!(form, 3 | 5 | 6 | 7);
    let coherent = form == 7 || (form == 3 && f("route") == 1);
    let parent = 1 + f("kind0");
    let child = map[(parent - 1) as usize];
    let mut nodes = vec![];
    for i in 0..if pair { 2 } else { 1 } {
        let state = f(if i == 0 { "state0" } else { "state1" });
        let kind = if i == 0 {
            parent
        } else if coherent {
            child
        } else {
            1 + f("kind1")
        };
        let state = if coherent || form == 4 {
            states[(kind - 1) as usize]
        } else {
            state
        };
        nodes.push(json!({"kind":kind, "state":if state==3 {Value::Null} else {json!(state)}}));
    }
    let structural = json!({"class":"Structural","kind":0,"ends":[0,1]});
    let edges = if pair {
        vec![
            json!({"class":if form>=6 || coherent {"Structural"} else {"Contact"},
                                     "kind":0,"ends":[0,1]}),
        ]
    } else {
        vec![]
    };
    let ops = match form {
        0 => vec![json!({"op":"SetState","node":0,"value":f("value")})],
        1 => vec![json!({"op":"AddState","node":0,"delta":if f("sign")==0 {-1} else {1}})],
        2 => vec![json!({"op":"Burn","node":0,"amount":1+f("amount")})],
        3 => vec![
            json!({"op":"Transfer","from":0,"to":1,"matter":if coherent {1} else {f("matter")},"activation":1+f("amount")}),
        ],
        4 => vec![
            json!({"op":"CreateNode","account":0,"kind":child,"state":states[(child - 1) as usize]}),
            json!({"op":"CreateEdge","account":0,"kind":0,"ends":[0,1]}),
            json!({"op":"Transfer","from":0,"to":1,"matter":1,"activation":1}),
            json!({"op":"Burn","node":0,"amount":1}),
        ],
        5 | 6 => vec![
            json!({"op":if form==5 {"CreateEdge"} else {"DeleteEdge"},"account":0,"kind":0,"ends":[0,1]}),
        ],
        7 => vec![
            json!({"op":"DeleteEdge","account":0,"kind":0,"ends":[0,1]}),
            json!({"op":"DeleteNode","node":1,"recipient":0}),
            json!({"op":"Burn","node":0,"amount":1}),
        ],
        _ => return Err(INVALID),
    };
    Ok(
        json!({"id":id,"nodes":nodes,"edges":edges,"absent":if form==5 {vec![structural]} else {vec![]},"ops":ops}),
    )
}

fn assemble(
    initial: u64,
    source: &mut impl FnMut(u64, &str, u64, u64) -> Checked<u64>,
) -> Checked<Value> {
    let map = (0..3)
        .map(|i| source(0, "child_kind_by_donor", i, 3).map(|v| v + 1))
        .collect::<Checked<Vec<_>>>()?;
    let states = (0..3)
        .map(|i| source(0, "role_state_by_kind", i, 3))
        .collect::<Checked<Vec<_>>>()?;
    let rules = (0..8)
        .map(|id| rule(id, &map, &states, source))
        .collect::<Checked<Vec<_>>>()?;
    let mut nodes = serde_json::Map::new();
    let mut edges = serde_json::Map::new();
    for i in 0..8 {
        nodes.insert(
            i.to_string(),
            json!({"kind":1+source(initial,"node_kind",i,3)?,
            "state":source(initial,"node_state",i,3)?,"matter":8,"activation":8}),
        );
        edges.insert(
            i.to_string(),
            json!({"class":"Contact","kind":0,"ends":[i,(i+1)%8]}),
        );
    }
    for i in 0..8 {
        if source(initial, "structural", i, 2)? == 1 {
            edges.insert(
                edges.len().to_string(),
                json!({"class":"Structural","kind":0,"ends":[i,(i+1)%8]}),
            );
        }
    }
    Ok(
        json!({"profile":"p00c-local-driven-v1","channels":[],"initial_activation":64,"injected":0,"extracted":0,
        "native":{"profile":"p00a-local-closed-v1","seed":source(initial,"scheduler",0,u64::MAX)?,
        "rules":rules,"limits":{"max_candidates":4096,"max_bindings":65536,"max_nodes":128,"max_edges":256},
        "world":{"nodes":nodes,"next_node":8,"next_edge":edges.len(),"matter_total":72+edges.len(),
        "edges":edges,"epoch":0,"dissipated":0,"activation_total":64,"next_event":0,"writers":{}}}}),
    )
}

fn respond(r: &Value) -> Value {
    let result = (|| -> Checked<(Value, Vec<Value>)> {
        if r["mode"] != "rule" && r["mode"] != "assembly" {
            return Err(INVALID);
        }
        let mut source = LiteralSource::new(r)?;
        let mut callback = |i: u64, f: &str, j: u64, n: u64| source.read(i, f, j, n);
        let value = if r["mode"] == "assembly" {
            assemble(bounded(&r["initial_id"], 4)?, &mut callback)?
        } else {
            let map = (0..3)
                .map(|j| callback(0, "child_kind_by_donor", j, 3).map(|v| v + 1))
                .collect::<Checked<Vec<_>>>()?;
            let states = (0..3)
                .map(|i| callback(0, "role_state_by_kind", i, 3))
                .collect::<Checked<Vec<_>>>()?;
            rule(bounded(&r["rule_id"], 8)?, &map, &states, &mut callback)?
        };
        Ok((value, source.reads))
    })();
    match result {
        Ok((value, reads)) => {
            json!({"case_id":r["case_id"],"ok":true,"value":value,"field_reads":reads})
        }
        Err(_) => json!({"case_id":r["case_id"],"ok":false,"error":INVALID}),
    }
}

fn main() -> io::Result<()> {
    let stdin = io::stdin();
    let mut out = io::BufWriter::new(io::stdout().lock());
    for line in stdin.lock().lines() {
        let line = line?;
        let value = match serde_json::from_str::<Value>(&line) {
            Ok(request) => respond(&request),
            Err(_) => json!({"case_id":null,"ok":false,"error":INVALID}),
        };
        writeln!(out, "{value}")?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture() -> Value {
        json!({"case_id":"unit","mode":"rule","map":[2,3,1],"state_map":[2,0,1],"rule_id":0,
        "fields":{"form":4,"kind0":0,"kind1":2,"new_kind":0,"state0":3,"state1":3,
        "value":2,"sign":0,"amount":1,"matter":1,"route":0}})
    }
    #[test]
    fn literal_birth_uses_map_and_fixed_costs() {
        let r = respond(&fixture());
        assert_eq!(r["value"]["ops"][0]["kind"], 2);
        assert_eq!(r["value"]["ops"][0]["state"], 0);
        assert_eq!(r["value"]["nodes"][0]["state"], 2);
        assert_eq!(r["field_reads"].as_array().unwrap().len(), 17);
        assert_eq!(
            r["value"]["ops"][3],
            json!({"op":"Burn","node":0,"amount":1})
        );
        assert_eq!(
            r["field_reads"][0],
            json!([0, "child_kind_by_donor", 0, 3, 1])
        );
    }
    #[test]
    fn booleans_and_missing_fields_are_rejected() {
        let mut r = fixture();
        r["map"][0] = json!(true);
        assert_eq!(respond(&r)["ok"], false);
        r = fixture();
        r["fields"].as_object_mut().unwrap().remove("kind0");
        assert_eq!(respond(&r)["ok"], false);
    }
}
