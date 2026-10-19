use crate::{
    core::*,
    experiments,
    interventions::*,
    runtime::{self, Frame, Matcher},
};
use serde::Serialize;

pub const FAMILIES: [&str; 2] = ["state_arrest", "activation_relocation"];
pub const ARMS: [&str; 5] = ["baseline", "sham", "target", "unrelated", "rescue"];
#[derive(Serialize)]
pub struct Arm {
    pub name: String,
    pub chain: Vec<Branch>,
    pub frames: Vec<Frame>,
}
#[derive(Serialize)]
pub struct Case {
    pub family: String,
    pub initial: Experiment,
    pub warmup: Vec<Frame>,
    pub source: Experiment,
    pub arms: Vec<Arm>,
}
#[derive(Serialize)]
pub struct Suite {
    pub schema: String,
    pub scientific_status: String,
    pub cases: Vec<Case>,
}

pub fn initial(family: &str, seed: u64) -> Result<Experiment> {
    let mut e = experiments::fixture("oscillator", seed)?;
    // Equalize the two test nodes' resources; contact degree and type already match.
    e.world.nodes.get_mut(&2).unwrap().matter = 8;
    e.world.matter_total = 21;
    if family == "activation_relocation" {
        for r in &mut e.rules {
            r.ops.push(Op::Burn { node: 0, amount: 1 });
        }
    } else if family != "state_arrest" {
        return Err("unknown_intervention_fixture".into());
    }
    e.validate()?;
    Ok(e)
}
pub fn operations(source: &Experiment, family: &str, arm: &str) -> Result<Vec<Intervention>> {
    if !FAMILIES.contains(&family) || !ARMS.contains(&arm) {
        return Err("unknown_intervention_arm".into());
    }
    if arm == "baseline" {
        return Ok(vec![]);
    }
    let node = if arm == "unrelated" { 2 } else { 0 };
    let n = &source.world.nodes[&node];
    Ok(vec![if family == "state_arrest" {
        Intervention::SetState {
            node,
            expected: n.state,
            value: if arm == "sham" { n.state } else { 9 },
        }
    } else {
        Intervention::MoveResources {
            from: node,
            to: 1,
            matter: 0,
            activation: if arm == "sham" { 0 } else { n.activation },
        }
    }])
}
pub fn make_arm(source: &Experiment, family: &str, name: &str) -> Result<Arm> {
    let first = branch(
        source,
        &Request::new(source, operations(source, family, name)?),
    )?;
    let mut current = first.experiment.clone();
    let mut chain = vec![first];
    if name == "rescue" {
        let restore = if family == "state_arrest" {
            Intervention::SetState {
                node: 0,
                expected: 9,
                value: source.world.nodes[&0].state,
            }
        } else {
            Intervention::MoveResources {
                from: 1,
                to: 0,
                matter: 0,
                activation: source.world.nodes[&0].activation,
            }
        };
        let rescued = branch(&current, &Request::new(&current, vec![restore]))?;
        current = rescued.experiment.clone();
        chain.push(rescued);
    }
    let mut reference = current.clone();
    let mut frames = Vec::new();
    for _ in 0..8 {
        let a = runtime::step(&mut current, Matcher::Indexed)?;
        let b = runtime::step(&mut reference, Matcher::Reference)?;
        if a != b {
            return Err("intervention_matcher_mismatch".into());
        }
        frames.push(a);
    }
    Ok(Arm {
        name: name.into(),
        chain,
        frames,
    })
}
pub fn suite() -> Result<Suite> {
    let mut cases = Vec::new();
    for family in FAMILIES {
        for seed in 0..16 {
            let initial = initial(family, seed)?;
            let mut source = initial.clone();
            let mut warmup = Vec::new();
            for _ in 0..2 {
                warmup.push(runtime::step(&mut source, Matcher::Indexed)?);
            }
            let arms = ARMS
                .into_iter()
                .map(|name| make_arm(&source, family, name))
                .collect::<Result<_>>()?;
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
        schema: "p00b-intervention-suite-v1".into(),
        scientific_status: "untested".into(),
        cases,
    })
}
