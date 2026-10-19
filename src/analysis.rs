//! Offline, bounded structure proposals and conservative temporal tracking.
use crate::{
    core::*,
    runtime::{self, Frame, Matcher},
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Protocol {
    pub schema: String,
    pub min_nodes: usize,
    pub max_nodes: usize,
    pub min_duration: usize,
    pub identity_jaccard_numerator: usize,
    pub identity_jaccard_denominator: usize,
    pub feature_similarity_numerator: usize,
    pub feature_similarity_denominator: usize,
    pub min_active_epoch_numerator: usize,
    pub min_active_epoch_denominator: usize,
    pub require_all_members_active: bool,
    pub interaction_lookback: usize,
    pub min_replacement_pairs: usize,
    pub maintenance_horizon: usize,
    pub min_occupancy_drop_numerator: usize,
    pub min_occupancy_drop_denominator: usize,
    pub control_occupancy_tolerance: usize,
    pub development_seeds: Vec<u64>,
    pub validation_seeds: Vec<u64>,
    pub expected: BTreeMap<String, Vec<String>>,
}
pub fn protocol() -> Protocol {
    serde_json::from_str(include_str!("../docs/detector_protocol.json")).unwrap()
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Proposal {
    pub members: BTreeSet<u64>,
    pub features: BTreeMap<String, usize>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Track {
    pub first: usize,
    pub last: usize,
    pub observations: usize,
    pub members: BTreeSet<u64>,
    pub all_members: BTreeSet<u64>,
    pub active_members: BTreeSet<u64>,
    pub active_epochs: usize,
    pub births: usize,
    pub deaths: usize,
    pub initial_features: BTreeMap<String, usize>,
    pub similar_observations: usize,
    pub ambiguous: bool,
    pub active_persistence: bool,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Estimator {
    pub samples: Vec<Vec<Proposal>>,
    pub tracks: Vec<Track>,
    pub excluded_large: usize,
    pub ambiguous_links: usize,
    pub supported: bool,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Detection {
    pub protocol_digest: String,
    pub connected: Estimator,
    pub interaction: Estimator,
    pub active_persistence: String,
    pub disagreement: bool,
    pub turnover: bool,
    pub agreement_pairs: Vec<[usize; 2]>,
}
fn components(nodes: &BTreeSet<u64>, links: &[BTreeSet<u64>]) -> Vec<BTreeSet<u64>> {
    let mut remaining = nodes.clone();
    let mut out = vec![];
    while let Some(root) = remaining.pop_first() {
        let mut group = BTreeSet::from([root]);
        loop {
            let n = group.len();
            for edge in links {
                if !group.is_disjoint(edge) {
                    group.extend(edge.intersection(nodes));
                }
            }
            if group.len() == n {
                break;
            }
        }
        for id in &group {
            remaining.remove(id);
        }
        out.push(group);
    }
    out
}
pub fn features(w: &World, members: &BTreeSet<u64>) -> BTreeMap<String, usize> {
    let mut f = BTreeMap::new();
    for id in members {
        *f.entry(format!("n:{}", w.nodes[id].kind)).or_default() += 1;
    }
    for e in w
        .edges
        .values()
        .filter(|e| e.class == Class::Structural && e.ends.iter().all(|id| members.contains(id)))
    {
        let kinds: Vec<_> = e.ends.iter().map(|id| w.nodes[id].kind).collect();
        *f.entry(format!("e:{}:{kinds:?}", e.kind)).or_default() += 1;
    }
    f
}
/// Exact isomorphism fingerprint for at most six nodes, excluding state/resources/IDs.
pub fn fingerprint(w: &World, members: &BTreeSet<u64>) -> String {
    fn visit(w: &World, remaining: Vec<u64>, order: &mut Vec<u64>, best: &mut Option<Vec<u8>>) {
        if remaining.is_empty() {
            let kinds: Vec<_> = order.iter().map(|id| w.nodes[id].kind).collect();
            let mut edges: Vec<_> = w
                .edges
                .values()
                .filter(|e| {
                    e.class == Class::Structural && e.ends.iter().all(|id| order.contains(id))
                })
                .map(|e| {
                    (
                        e.kind,
                        e.ends
                            .iter()
                            .map(|id| order.iter().position(|n| n == id).unwrap())
                            .collect::<Vec<_>>(),
                    )
                })
                .collect();
            edges.sort();
            let bytes = canonical(&(kinds, edges));
            if best.as_ref().is_none_or(|old| bytes < *old) {
                *best = Some(bytes);
            }
            return;
        }
        for i in 0..remaining.len() {
            let mut rest = remaining.clone();
            let id = rest.remove(i);
            order.push(id);
            visit(w, rest, order, best);
            order.pop();
        }
    }
    // This bounded algorithm must not be called on unbounded components.
    assert!(!members.is_empty() && members.len() <= 6);
    let mut best = None;
    visit(w, members.iter().copied().collect(), &mut vec![], &mut best);
    digest(&best.unwrap())
}
fn similar(a: &BTreeMap<String, usize>, b: &BTreeMap<String, usize>, p: &Protocol) -> bool {
    let keys: BTreeSet<_> = a.keys().chain(b.keys()).collect();
    let mut intersection = 0;
    let mut union = 0;
    for key in keys {
        let x = *a.get(key).unwrap_or(&0);
        let y = *b.get(key).unwrap_or(&0);
        intersection += x.min(y);
        union += x.max(y);
    }
    intersection * p.feature_similarity_denominator >= union * p.feature_similarity_numerator
}
fn identity(a: &BTreeSet<u64>, b: &BTreeSet<u64>, p: &Protocol) -> bool {
    a.intersection(b).count() * p.identity_jaccard_denominator
        >= a.union(b).count() * p.identity_jaccard_numerator
}
fn changed(a: &World, b: &World) -> BTreeSet<u64> {
    let mut out = BTreeSet::new();
    for id in a.nodes.keys().chain(b.nodes.keys()) {
        if match (a.nodes.get(id), b.nodes.get(id)) {
            (Some(x), Some(y)) => x.kind != y.kind || x.state != y.state,
            _ => true,
        } {
            out.insert(*id);
        }
    }
    for id in a.edges.keys().chain(b.edges.keys()) {
        if a.edges.get(id) != b.edges.get(id) {
            for e in [a.edges.get(id), b.edges.get(id)].into_iter().flatten() {
                if e.class == Class::Structural {
                    out.extend(&e.ends);
                }
            }
        }
    }
    out
}
pub fn event_activity(initial: &Experiment, frames: &[Frame]) -> Result<Vec<Vec<BTreeSet<u64>>>> {
    let mut expected = initial.clone();
    let mut result = vec![];
    for frame in frames {
        let before = expected.world.clone();
        let replay = runtime::step(&mut expected, Matcher::Reference)?;
        if replay != *frame {
            return Err("analysis_unverified_trace".into());
        }
        let mut w = before;
        let mut events = vec![];
        for e in &frame.events {
            let rule = initial
                .rules
                .iter()
                .find(|r| r.id == e.candidate.rule)
                .ok_or("analysis_unknown_rule")?;
            let (next, _) = runtime::apply(&w, rule, &e.candidate.binding)?;
            events.push(changed(&w, &next));
            w = next;
        }
        result.push(events);
    }
    Ok(result)
}
fn estimator(
    worlds: &[World],
    activity: &[Vec<BTreeSet<u64>>],
    interaction: bool,
    p: &Protocol,
) -> Estimator {
    let mut samples = vec![];
    let mut excluded = 0;
    for (t, w) in worlds.iter().enumerate() {
        let nodes: BTreeSet<_> = w.nodes.keys().copied().collect();
        let links: Vec<BTreeSet<u64>> = if interaction {
            activity[t.saturating_sub(p.interaction_lookback)..t]
                .iter()
                .flatten()
                .map(|s| s.intersection(&nodes).copied().collect())
                .collect()
        } else {
            w.edges
                .values()
                .filter(|e| e.class == Class::Structural)
                .map(|e| e.ends.iter().copied().collect())
                .collect()
        };
        let eligible = if interaction {
            links.iter().flatten().copied().collect()
        } else {
            nodes
        };
        let mut proposals = vec![];
        for members in components(&eligible, &links) {
            if members.len() > p.max_nodes {
                excluded += 1;
            } else if members.len() >= p.min_nodes {
                proposals.push(Proposal {
                    features: features(w, &members),
                    members,
                });
            }
        }
        samples.push(proposals);
    }
    let mut tracks: Vec<Track> = vec![];
    let mut previous: Vec<usize> = vec![];
    let mut ambiguous_links = 0;
    for (t, proposals) in samples.iter().enumerate() {
        let links: Vec<Vec<usize>> = proposals
            .iter()
            .map(|q| {
                previous
                    .iter()
                    .copied()
                    .filter(|i| identity(&tracks[*i].members, &q.members, p))
                    .collect()
            })
            .collect();
        let mut current = vec![];
        for (j, q) in proposals.iter().enumerate() {
            let possible = &links[j];
            let mut ambiguous = false;
            let continuation = if possible.len() == 1 {
                let i = possible[0];
                if links.iter().filter(|x| x.contains(&i)).count() == 1 {
                    Some(i)
                } else {
                    ambiguous = true;
                    None
                }
            } else {
                ambiguous = !possible.is_empty();
                None
            };
            if ambiguous {
                ambiguous_links += 1;
                for i in possible {
                    tracks[*i].ambiguous = true;
                }
            }
            let i = if let Some(i) = continuation {
                i
            } else {
                tracks.push(Track {
                    first: t,
                    last: t,
                    observations: 0,
                    members: q.members.clone(),
                    all_members: BTreeSet::new(),
                    active_members: BTreeSet::new(),
                    active_epochs: 0,
                    births: 0,
                    deaths: 0,
                    initial_features: q.features.clone(),
                    similar_observations: 0,
                    ambiguous,
                    active_persistence: false,
                });
                tracks.len() - 1
            };
            let track = &mut tracks[i];
            if t > track.first {
                track.births += q
                    .members
                    .difference(&track.members)
                    .filter(|id| !worlds[t - 1].nodes.contains_key(id))
                    .count();
                track.deaths += track
                    .members
                    .difference(&q.members)
                    .filter(|id| !worlds[t].nodes.contains_key(id))
                    .count();
            }
            let affected: BTreeSet<_> = if t > 0 {
                activity[t - 1].iter().flatten().copied().collect()
            } else {
                BTreeSet::new()
            };
            let local: BTreeSet<_> = q.members.union(&track.members).copied().collect();
            let active: BTreeSet<_> = local.intersection(&affected).copied().collect();
            if t > track.first && !active.is_empty() {
                track.active_epochs += 1;
            }
            track.active_members.extend(active);
            track.all_members.extend(&q.members);
            track.members = q.members.clone();
            track.last = t;
            track.observations += 1;
            if similar(&track.initial_features, &q.features, p) {
                track.similar_observations += 1;
            }
            current.push(i);
        }
        previous = current;
    }
    for tr in &mut tracks {
        let duration = tr.last - tr.first;
        tr.active_persistence = !tr.ambiguous
            && duration >= p.min_duration
            && tr.observations == duration + 1
            && tr.similar_observations == tr.observations
            && tr.active_epochs * p.min_active_epoch_denominator
                >= duration * p.min_active_epoch_numerator
            && tr.all_members.is_subset(&tr.active_members);
    }
    let supported = tracks.iter().any(|t| t.active_persistence);
    Estimator {
        samples,
        tracks,
        excluded_large: excluded,
        ambiguous_links,
        supported,
    }
}
pub fn analyze(initial: &Experiment, frames: &[Frame]) -> Result<Detection> {
    let p = protocol();
    let activity = event_activity(initial, frames)?;
    let worlds: Vec<_> = std::iter::once(initial.world.clone())
        .chain(frames.iter().map(|f| f.world.clone()))
        .collect();
    let connected = estimator(&worlds, &activity, false, &p);
    let interaction = estimator(&worlds, &activity, true, &p);
    let mut agreement_pairs = vec![];
    for (i, a) in connected.tracks.iter().enumerate() {
        for (j, b) in interaction.tracks.iter().enumerate() {
            if a.active_persistence
                && b.active_persistence
                && a.last == b.last
                && identity(&a.members, &b.members, &p)
            {
                agreement_pairs.push([i, j]);
            }
        }
    }
    let disagreement = connected.supported != interaction.supported
        || (connected.supported && interaction.supported && agreement_pairs.is_empty());
    let active_persistence = if disagreement {
        "inconclusive"
    } else if connected.supported {
        "supported"
    } else {
        "not_supported"
    }
    .into();
    let turnover = agreement_pairs.iter().any(|[i, j]| {
        let a = &connected.tracks[*i];
        let b = &interaction.tracks[*j];
        a.births.min(a.deaths) >= p.min_replacement_pairs
            && b.births.min(b.deaths) >= p.min_replacement_pairs
    });
    Ok(Detection {
        protocol_digest: digest(&p),
        connected,
        interaction,
        active_persistence,
        disagreement,
        turnover,
        agreement_pairs,
    })
}
pub fn occupancy(worlds: &[World], root: u64, reference: &str) -> usize {
    let p = protocol();
    worlds
        .iter()
        .filter(|w| {
            let nodes = w.nodes.keys().copied().collect();
            let links: Vec<BTreeSet<_>> = w
                .edges
                .values()
                .filter(|e| e.class == Class::Structural)
                .map(|e| e.ends.iter().copied().collect())
                .collect();
            components(&nodes, &links).iter().any(|m| {
                m.contains(&root)
                    && m.len() >= p.min_nodes
                    && m.len() <= p.max_nodes
                    && fingerprint(w, m) == reference
            })
        })
        .count()
}
