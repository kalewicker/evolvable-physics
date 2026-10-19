//! Versioned environment adapter using the unchanged P00e operational thresholds.
//! The archived v1 extractor remains in analysis.rs for frozen regression checks.
use crate::{
    analysis::{self, Detection, Estimator, Proposal, Protocol, Track, features},
    core::*,
    environment::{self, Environment, Epoch},
    runtime::{Frame, Matcher},
};
use std::collections::{BTreeMap, BTreeSet};

pub const SCHEMA: &str = "p00g-environment-analysis-v1";

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
pub fn observations(worlds: &[World], activity: &[Vec<BTreeSet<u64>>]) -> Result<Detection> {
    if worlds.len() != activity.len() + 1 {
        return Err("analysis_observation_length".into());
    }
    for world in worlds {
        world.validate()?;
    }
    let p = analysis::protocol();
    let connected = estimator(worlds, activity, false, &p);
    let interaction = estimator(worlds, activity, true, &p);
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

pub fn analyze_native(initial: &Experiment, frames: &[Frame]) -> Result<Detection> {
    let activity = analysis::event_activity(initial, frames)?;
    let worlds: Vec<_> = std::iter::once(initial.world.clone())
        .chain(frames.iter().map(|f| f.world.clone()))
        .collect();
    observations(&worlds, &activity)
}

pub fn analyze_environment(initial: &Environment, epochs: &[Epoch]) -> Result<Detection> {
    initial.validate()?;
    let mut current = initial.clone();
    let mut worlds = vec![initial.native.world.clone()];
    let mut activity = vec![];
    for frame in epochs {
        let expected = environment::step(&mut current, Matcher::Reference)?;
        if expected != *frame {
            return Err("analysis_environment_trace_mismatch".into());
        }
        let mut native =
            analysis::event_activity(&frame.prepared, std::slice::from_ref(&frame.native_frame))?;
        activity.push(native.pop().expect("one epoch activity"));
        worlds.push(current.native.world.clone());
    }
    observations(&worlds, &activity)
}
