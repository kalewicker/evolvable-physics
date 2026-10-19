use crate::{
    analysis::{self, Detection},
    core::*,
    detector_fixtures,
    environment::{self, Action, Channel, Environment, Epoch},
    environment_analysis,
    environment_branches::{self, Branch, Request},
    environment_fixtures, experiments,
    interventions::Intervention,
    runtime::{self, Frame, Matcher, TraceMode},
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
#[derive(Clone, Serialize, Deserialize)]
pub struct Family {
    pub expected_ap: String,
    pub expected_native_events: usize,
}
#[derive(Clone, Serialize, Deserialize)]
pub struct Protocol {
    pub schema: String,
    pub base_detector_protocol_digest: String,
    pub analysis_schema: String,
    pub epochs: usize,
    pub seeds: Vec<u64>,
    pub families: BTreeMap<String, Family>,
    pub maintenance_family: String,
    pub maintenance_arms: Vec<String>,
    pub maintenance_warmup_epochs: usize,
    pub maintenance_expected_occupancy: Vec<usize>,
    pub logging_semantics: String,
    pub external_activity_policy: String,
    pub admission_policy: String,
}
pub fn protocol() -> Protocol {
    serde_json::from_str(include_str!("../docs/p00g_protocol.json")).unwrap()
}
fn channels(flux: bool) -> Vec<Channel> {
    let channel = |id, action| Channel {
        id,
        start: 0,
        end: None,
        period: 1,
        action,
    };
    let mut out = vec![
        channel(10, Action::Supply { node: 0, amount: 2 }),
        channel(
            20,
            Action::Transport {
                edge: 0,
                from: 0,
                to: 1,
                matter: 0,
                activation: 2,
            },
        ),
    ];
    if flux {
        out.push(channel(
            25,
            Action::Transport {
                edge: 2,
                from: 1,
                to: 2,
                matter: 0,
                activation: 1,
            },
        ));
    }
    out.push(channel(30, Action::Extract { node: 1, amount: 1 }));
    if flux {
        out.push(channel(40, Action::Extract { node: 2, amount: 1 }));
    }
    out
}
pub fn initial(family: &str, seed: u64) -> Result<Environment> {
    if !protocol().families.contains_key(family) {
        return Err("unknown_integration_fixture".into());
    }
    if family == "driven_renewal" {
        let native = detector_fixtures::initial("renewal", seed)?;
        let e = Environment {
            profile: environment::PROFILE.into(),
            native,
            initial_activation: 0,
            injected: 0,
            extracted: 0,
            channels: [0, 3]
                .into_iter()
                .enumerate()
                .map(|(i, node)| Channel {
                    id: 10 + i as u64,
                    start: 0,
                    end: None,
                    period: 1,
                    action: Action::Supply { node, amount: 1 },
                })
                .collect(),
        };
        e.validate()?;
        return Ok(e);
    }
    let nodes: BTreeMap<_, _> = [(0, 2, 8, 2), (1, 10, 4, 0), (2, 11, 0, 0), (3, 2, 0, 0)]
        .into_iter()
        .map(|(id, kind, matter, activation)| {
            (
                id,
                Node {
                    kind,
                    state: 0,
                    matter,
                    activation,
                },
            )
        })
        .collect();
    let edges: BTreeMap<_, _> = [
        (0, Class::Contact, vec![0, 1]),
        (1, Class::Contact, vec![1, 3]),
        (2, Class::Contact, vec![1, 2]),
        (3, Class::Structural, vec![1, 2]),
    ]
    .into_iter()
    .map(|(id, class, ends)| {
        (
            id,
            Edge {
                class,
                kind: 3,
                ends,
            },
        )
    })
    .collect();
    let mut rules: Vec<_> = (0..2)
        .map(|state| Rule {
            id: state as u64,
            nodes: vec![
                NodePattern {
                    kind: 10,
                    state: Some(state),
                },
                NodePattern {
                    kind: 11,
                    state: Some(state),
                },
            ],
            edges: vec![EdgePattern {
                class: Class::Structural,
                kind: 3,
                ends: vec![0, 1],
            }],
            absent: vec![],
            ops: vec![
                Op::SetState {
                    node: 0,
                    value: 1 - state,
                },
                Op::SetState {
                    node: 1,
                    value: 1 - state,
                },
                Op::Burn { node: 0, amount: 1 },
            ],
        })
        .collect();
    if family == "external_flux" {
        rules.clear();
    }
    if family == "no_op_pair" {
        rules.truncate(1);
        for n in &mut rules[0].nodes {
            n.state = None;
        }
        rules[0].ops = vec![
            Op::SetState { node: 0, value: 0 },
            Op::SetState { node: 1, value: 0 },
            Op::Burn { node: 0, amount: 1 },
        ];
    }
    let native = Experiment {
        profile: crate::core::PROFILE.into(),
        seed,
        rules,
        limits: Limits {
            max_candidates: 10000,
            max_bindings: 100000,
            max_nodes: 128,
            max_edges: 256,
        },
        world: World {
            nodes,
            edges,
            next_node: 4,
            next_edge: 4,
            epoch: 0,
            dissipated: 0,
            matter_total: 20,
            activation_total: 2,
            next_event: 0,
            writers: BTreeMap::new(),
        },
    };
    let mut e = Environment {
        profile: environment::PROFILE.into(),
        channels: channels(family == "external_flux"),
        initial_activation: 2,
        injected: 0,
        extracted: 0,
        native,
    };
    if family == "unfunded_pair" {
        e.channels.retain(|c| c.id != 10);
    }
    if family == "mixed_islands" {
        for id in 0..4 {
            let mut n = e.native.world.nodes[&id].clone();
            if [10, 11].contains(&n.kind) {
                n.kind += 100;
            }
            e.native.world.nodes.insert(id + 4, n);
        }
        for id in 0..4 {
            let mut edge = e.native.world.edges[&id].clone();
            edge.ends.iter_mut().for_each(|id| *id += 4);
            e.native.world.edges.insert(id + 4, edge);
        }
        for mut c in channels(true) {
            c.id += 100;
            match &mut c.action {
                Action::Supply { node, .. } | Action::Extract { node, .. } => *node += 4,
                Action::Transport { edge, from, to, .. } => {
                    *edge += 4;
                    *from += 4;
                    *to += 4;
                }
            }
            e.channels.push(c);
        }
        e.native.world.next_node = 8;
        e.native.world.next_edge = 8;
        e.native.world.matter_total = 40;
        e.native.world.activation_total = 4;
        e.initial_activation = 4;
    }
    e.validate()?;
    Ok(e)
}
fn run_environment(source: &Environment, n: usize) -> Result<(Vec<Epoch>, Vec<String>)> {
    let mut full = source.clone();
    let mut reference = source.clone();
    let mut quiet = source.clone();
    let mut epochs = vec![];
    let mut quiet_digests = vec![];
    for _ in 0..n {
        let a = environment::step(&mut full, Matcher::Indexed)?;
        let b = environment::step(&mut reference, Matcher::Reference)?;
        let no_frame =
            environment::step_with_logging(&mut quiet, Matcher::Indexed, TraceMode::Disabled)?;
        if a != b || full != quiet || no_frame.is_some() {
            return Err("integration_environment_logging_mismatch".into());
        }
        quiet_digests.push(digest(&quiet));
        epochs.push(a);
    }
    Ok((epochs, quiet_digests))
}
#[derive(Serialize)]
pub struct NativeLogging {
    pub family: String,
    pub initial: Experiment,
    pub frames: Vec<Frame>,
    pub disabled_digests: Vec<String>,
}
#[derive(Serialize)]
pub struct EnvironmentLogging {
    pub family: String,
    pub initial: Environment,
    pub epochs: Vec<Epoch>,
    pub disabled_digests: Vec<String>,
}
#[derive(Serialize)]
pub struct Arm {
    pub name: String,
    pub chain: Vec<Branch>,
    pub epochs: Vec<Epoch>,
    pub disabled_digests: Vec<String>,
    pub occupancy: usize,
}
#[derive(Serialize)]
pub struct Maintenance {
    pub warmup: Vec<Epoch>,
    pub disabled_warmup_digests: Vec<String>,
    pub source: Environment,
    pub reference_fingerprint: String,
    pub arms: Vec<Arm>,
    pub supported: bool,
}
#[derive(Serialize)]
pub struct Case {
    pub family: String,
    pub initial: Environment,
    pub epochs: Vec<Epoch>,
    pub disabled_digests: Vec<String>,
    pub detection: Detection,
    pub maintenance: Option<Maintenance>,
}
#[derive(Serialize)]
pub struct Suite {
    pub schema: String,
    pub protocol: Protocol,
    pub protocol_digest: String,
    pub scientific_status: String,
    pub native_logging: Vec<NativeLogging>,
    pub environment_logging: Vec<EnvironmentLogging>,
    pub cases: Vec<Case>,
}
fn maintenance(source: &Environment, det: &Detection) -> Result<Maintenance> {
    let p = protocol();
    let reference_fingerprint =
        analysis::fingerprint(&source.native.world, &[0, 1, 2].into_iter().collect());
    let (warmup, disabled_warmup_digests) = run_environment(source, p.maintenance_warmup_epochs)?;
    let source = warmup.last().unwrap().state.clone();
    let mut arms = vec![];
    for name in &p.maintenance_arms {
        let node = if name == "unrelated" { 3 } else { 0 };
        let expected = source.native.world.nodes[&node].state;
        let ops = if name == "baseline" {
            vec![]
        } else {
            vec![Intervention::SetState {
                node,
                expected,
                value: if name == "sham" { expected } else { 9 },
            }]
        };
        let b = environment_branches::branch(&source, &Request::new(&source, ops))?;
        let mut current = b.environment.clone();
        let mut chain = vec![b];
        if name == "rescue" {
            let b = environment_branches::branch(
                &current,
                &Request::new(
                    &current,
                    vec![Intervention::SetState {
                        node: 0,
                        expected: 9,
                        value: source.native.world.nodes[&0].state,
                    }],
                ),
            )?;
            current = b.environment.clone();
            chain.push(b);
        }
        let (epochs, disabled_digests) = run_environment(&current, p.epochs)?;
        let worlds: Vec<_> = epochs
            .iter()
            .map(|f| f.state.native.world.clone())
            .collect();
        let occupancy = analysis::occupancy(&worlds, 0, &reference_fingerprint);
        arms.push(Arm {
            name: name.clone(),
            chain,
            epochs,
            disabled_digests,
            occupancy,
        });
    }
    let cfg = analysis::protocol();
    let base = arms[0].occupancy;
    let supported = det.active_persistence == "supported"
        && det.agreement_pairs.iter().any(|[i, j]| {
            let a = &det.connected.tracks[*i];
            let b = &det.interaction.tracks[*j];
            a.members.contains(&0)
                && b.members.contains(&0)
                && a.births.min(a.deaths) >= cfg.min_replacement_pairs
                && b.births.min(b.deaths) >= cfg.min_replacement_pairs
        })
        && base.saturating_sub(arms[2].occupancy) * cfg.min_occupancy_drop_denominator
            >= p.epochs * cfg.min_occupancy_drop_numerator
        && [1, 3, 4]
            .iter()
            .all(|i| arms[*i].occupancy.abs_diff(base) <= cfg.control_occupancy_tolerance);
    Ok(Maintenance {
        warmup,
        disabled_warmup_digests,
        source,
        reference_fingerprint,
        arms,
        supported,
    })
}
pub fn suite() -> Result<Suite> {
    let p = protocol();
    if digest(&analysis::protocol()) != p.base_detector_protocol_digest {
        return Err("integration_detector_protocol_drift".into());
    }
    let mut native_logging = vec![];
    let mut environment_logging = vec![];
    let mut cases = vec![];
    for seed in &p.seeds {
        for family in experiments::FIXTURES {
            let initial = experiments::fixture(family, *seed)?;
            let mut full = initial.clone();
            let mut quiet = initial.clone();
            let mut frames = vec![];
            let mut disabled_digests = vec![];
            for _ in 0..p.epochs {
                let frame = runtime::step(&mut full, Matcher::Indexed)?;
                let none =
                    runtime::step_with_logging(&mut quiet, Matcher::Indexed, TraceMode::Disabled)?;
                if full != quiet || none.is_some() {
                    return Err("integration_native_logging_mismatch".into());
                }
                disabled_digests.push(digest(&quiet.world));
                frames.push(frame);
            }
            native_logging.push(NativeLogging {
                family: family.into(),
                initial,
                frames,
                disabled_digests,
            });
        }
        for family in environment_fixtures::MODES {
            let initial = environment_fixtures::fixture(family, *seed)?;
            let (epochs, disabled_digests) = run_environment(&initial, p.epochs)?;
            environment_logging.push(EnvironmentLogging {
                family: family.into(),
                initial,
                epochs,
                disabled_digests,
            });
        }
        for family in p.families.keys() {
            let initial = initial(family, *seed)?;
            let (epochs, disabled_digests) = run_environment(&initial, p.epochs)?;
            let detection = environment_analysis::analyze_environment(&initial, &epochs)?;
            let maintenance = if *family == p.maintenance_family {
                Some(maintenance(&initial, &detection)?)
            } else {
                None
            };
            cases.push(Case {
                family: family.clone(),
                initial,
                epochs,
                disabled_digests,
                detection,
                maintenance,
            });
        }
    }
    Ok(Suite {
        schema: "p00g-integration-suite-v1".into(),
        protocol_digest: digest(&p),
        protocol: p,
        scientific_status: "untested".into(),
        native_logging,
        environment_logging,
        cases,
    })
}
