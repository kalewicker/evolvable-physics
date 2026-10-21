//! P01k keyed sampler; sampled mode requires a frozen active-stage admission.
use serde_json::{Value, json};
use std::io::{self, BufRead, Write};

type Checked<T> = Result<T, &'static str>;
const NAMESPACE: &str = "p01-generator-v3";
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
            json!({"op":"Transfer","from":0,"to":1,"matter":f("matter"),"activation":1+f("amount")}),
        ],
        4 => vec![
            json!({"op":"CreateNode","account":0,"kind":child,"state":f("value")}),
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
    let rules = (0..8)
        .map(|id| rule(id, &map, source))
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

fn barrier(row: &Value) -> Checked<Value> {
    let p = bounded(&row["parent"], 4)?;
    if p == 0 {
        return Err(INVALID);
    }
    let c = row["map"][(p - 1) as usize].as_u64().ok_or(INVALID)?;
    let contains = |key: &str, k: u64| -> Checked<bool> {
        Ok(row[key].as_array().ok_or(INVALID)?.contains(&json!(k)))
    };
    let b = contains("birth_donors", p)?;
    let f = b && contains("funding_donors", p)?;
    let r = b && contains("recycle_donors", p)?;
    let d = b && contains("birth_donors", c)?;
    let state_ok = |key: &str| row[key].is_null() || row[key] == row["child_state"];
    Ok(json!([
        b,
        f,
        r,
        d,
        f && row["transfer_matter"].as_u64().ok_or(INVALID)? > 0
            && state_ok("funding_target_state"),
        d && state_ok("next_donor_state")
    ]))
}

fn respond(r: &Value) -> Value {
    let result = (|| -> Checked<(Value, Vec<Value>)> {
        if r["mode"] == "barrier" {
            return Ok((barrier(&r["descriptor"])?, vec![]));
        }
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
            rule(bounded(&r["rule_id"], 8)?, &map, &mut callback)?
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

fn literal_main() -> io::Result<()> {
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

fn message(proposal: u64, initial: u64, field: &str, index: u64) -> Vec<u8> {
    serde_json::to_vec(&(NAMESPACE, proposal, initial, field, index)).unwrap()
}

fn prefix_raw(prefix: &str, modulus: u64) -> Checked<u64> {
    if prefix.len() != 16 || modulus == 0 {
        return Err(INVALID);
    }
    Ok(u64::from_str_radix(prefix, 16).map_err(|_| INVALID)? % modulus)
}

fn file_json(path: &std::path::Path) -> Checked<Value> {
    serde_json::from_slice(&std::fs::read(path).map_err(|_| "admission file missing")?)
        .map_err(|_| INVALID)
}

fn file_sha(path: &std::path::Path) -> Checked<String> {
    use sha2::{Digest, Sha256};
    Ok(format!(
        "{:x}",
        Sha256::digest(std::fs::read(path).map_err(|_| "identity file missing")?)
    ))
}

fn authorize(bundle: &std::path::Path, slot: u64) -> Checked<()> {
    let root = bundle.join("source");
    let a = file_json(&root.join("docs/p01k_execution_admission.json"))?;
    let f = file_json(&root.join("docs/p01k_execution_freeze.json"))?;
    let p = file_json(&root.join("docs/p01k_protocol.json"))?;
    let m = file_json(&bundle.join("manifest.json"))?;
    if slot >= 128
        || a["schema"] != "p01k-static-execution-admission-v1"
        || a["sampling_admitted"] != true
        || a["world_execution_admitted"] != false
        || a["e01_authorized"] != false
        || a["fixed_cells"] != 128
        || a["output_absolute"] != bundle.to_str().ok_or(INVALID)?
        || a["protocol_sha256"] != file_sha(&root.join("docs/p01k_protocol.json"))?
        || a["registration_freeze_sha256"]
            != file_sha(&root.join("docs/p01k_registration_freeze.json"))?
        || a["execution_freeze_sha256"] != file_sha(&root.join("docs/p01k_execution_freeze.json"))?
        || p["generator"] != NAMESPACE
        || p["proposal_ids"] != json!((5000..5032).collect::<Vec<u64>>())
        || p["initial_state_ids"] != json!([0, 1, 2, 3])
        || p["environment_denominator"] != 128
        || p["epochs"] != 0
        || p["world_execution_admitted"] != false
        || m["execution_status"] != "running"
        || m["active_stage"] != json!({"name":"rust_generation","slot":slot})
        || m["execution_admission_sha256"]
            != file_sha(&root.join("docs/p01k_execution_admission.json"))?
        || file_sha(&std::env::current_exe().map_err(|_| INVALID)?)?
            != f["binaries"]["generator-v3"]["sha256"]
    {
        return Err("sampling not admitted");
    }
    let rows = m["rows"].as_array().ok_or(INVALID)?;
    if rows.len() != 128 {
        return Err("incomplete manifest");
    }
    for (n, row) in rows.iter().enumerate() {
        if row["slot"] != json!(n)
            || row["proposal"] != json!(5000 + n / 4)
            || row["initial"] != json!(n % 4)
        {
            return Err("reordered manifest");
        }
    }
    Ok(())
}

fn sample(bundle: &std::path::Path, slot: u64) -> Checked<Value> {
    authorize(bundle, slot)?;
    use sha2::{Digest, Sha256};
    let proposal = 5000 + slot / 4;
    let mut source = |i: u64, field: &str, index: u64, n: u64| -> Checked<(u64, Value)> {
        let preimage = message(proposal, i, field, index);
        let digest = format!("{:x}", Sha256::digest(&preimage));
        let prefix = u64::from_str_radix(&digest[..16], 16).map_err(|_| INVALID)?;
        let raw = prefix_raw(&digest[..16], n)?;
        Ok((
            raw,
            json!({"preimage":String::from_utf8(preimage).map_err(|_| INVALID)?,"digest":digest,"prefix":prefix}),
        ))
    };
    recorded(slot, proposal, slot % 4, &mut source)
}

fn recorded(
    slot: u64,
    proposal: u64,
    initial: u64,
    source: &mut impl FnMut(u64, &str, u64, u64) -> Checked<(u64, Value)>,
) -> Checked<Value> {
    let mut records = Vec::new();
    let mut checked = |i: u64, field: &str, index: u64, n: u64| -> Checked<u64> {
        let (raw, mut meta) = source(i, field, index, n)?;
        if raw >= n {
            return Err(INVALID);
        }
        let object = meta.as_object_mut().ok_or(INVALID)?;
        for (k, v) in [
            ("namespace", json!(NAMESPACE)),
            ("proposal", json!(proposal)),
            ("initial", json!(i)),
            ("field", json!(field)),
            ("index", json!(index)),
            ("modulus", json!(n)),
            ("raw", json!(raw)),
        ] {
            object.insert(k.into(), v);
        }
        records.push(meta);
        Ok(raw)
    };
    let environment = assemble(initial, &mut checked)?;
    if records.len() != 116 {
        return Err("field count");
    }
    let map = records[..3]
        .iter()
        .map(|r| r["raw"].as_u64().unwrap() + 1)
        .collect::<Vec<_>>();
    Ok(
        json!({"schema":"p01k-generated-environment-v1","slot":slot,"proposal":proposal,"initial":initial,
        "map":map,"environment":environment,"draws":records}),
    )
}

fn mock_record(r: &Value) -> Checked<Value> {
    let mut literal = LiteralSource::new(r)?;
    let slot = bounded(&r["cell"]["slot"], 128)?;
    let proposal = r["cell"]["proposal"].as_u64().ok_or(INVALID)?;
    let initial = bounded(&r["cell"]["initial"], 4)?;
    if r["mode"] != "assembly" || r["initial_id"] != json!(initial) {
        return Err(INVALID);
    }
    recorded(
        slot,
        proposal,
        initial,
        &mut |i: u64, f: &str, j: u64, n: u64| {
            let raw = literal.read(i, f, j, n)?;
            Ok((
                raw,
                json!({"preimage":String::from_utf8(message(proposal,i,f,j)).map_err(|_| INVALID)?,
            "digest":format!("{raw:016x}{:048x}",0),"prefix":raw}),
            ))
        },
    )
}

fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    if args.len() == 2 && args[1] == "--literal" {
        if let Err(error) = literal_main() {
            eprintln!("{error}");
            std::process::exit(1);
        }
        return;
    }
    if args.len() == 2 && args[1] == "--record-literal" {
        let mut out = io::BufWriter::new(io::stdout().lock());
        for line in io::stdin().lock().lines() {
            let result = line
                .map_err(|_| INVALID)
                .and_then(|s| serde_json::from_str::<Value>(&s).map_err(|_| INVALID))
                .and_then(|r| mock_record(&r));
            match result {
                Ok(v) => writeln!(out, "{v}").unwrap(),
                Err(e) => {
                    eprintln!("{e}");
                    std::process::exit(1);
                }
            }
        }
        return;
    }
    let result = (|| -> Checked<Value> {
        if args.len() != 3 {
            return Err("usage: generator-v3 BUNDLE SLOT or --literal");
        }
        let bundle = std::fs::canonicalize(&args[1]).map_err(|_| "missing bundle")?;
        let slot = args[2].parse().map_err(|_| INVALID)?;
        sample(&bundle, slot)
    })();
    match result {
        Ok(value) => println!("{value}"),
        Err(error) => {
            eprintln!("{error}");
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture() -> Value {
        json!({"case_id":"unit","mode":"rule","map":[2,3,1],"rule_id":0,
        "fields":{"form":4,"kind0":0,"kind1":2,"new_kind":0,"state0":3,"state1":3,
        "value":2,"sign":0,"amount":1,"matter":1,"route":0}})
    }
    #[test]
    fn literal_birth_uses_map_and_fixed_costs() {
        let r = respond(&fixture());
        assert_eq!(r["value"]["ops"][0]["kind"], 2);
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
    #[test]
    fn primitive_vectors_are_unhashed() {
        let vectors: Value =
            serde_json::from_str(include_str!("../../docs/p01k_primitive_vectors.json")).unwrap();
        for row in vectors["serialization"].as_array().unwrap() {
            let a = &row["arguments"];
            assert_eq!(
                String::from_utf8(message(
                    a[1].as_u64().unwrap(),
                    a[2].as_u64().unwrap(),
                    a[3].as_str().unwrap(),
                    a[4].as_u64().unwrap()
                ))
                .unwrap(),
                row["utf8"]
            );
        }
        for row in vectors["prefix_reduction"].as_array().unwrap() {
            assert_eq!(
                prefix_raw(
                    row["prefix_hex"].as_str().unwrap(),
                    row["modulus"].as_u64().unwrap()
                )
                .unwrap(),
                row["raw"]
            );
        }
    }
    #[test]
    fn absent_admission_rejects_before_source_use() {
        assert!(sample(std::path::Path::new("/nonexistent/p01k-test-bundle"), 0).is_err());
    }
}
