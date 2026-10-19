use causal_alife::{core::Class, generalization};
#[test]
fn every_registered_generator_is_valid_and_bounded() {
    let p = generalization::protocol();
    assert_eq!(p.families.len() * p.seeds.len() * p.encodings.len(), 176);
    for family in p.families.keys() {
        for seed in &p.seeds {
            for encoding in &p.encodings {
                let e = generalization::initial(family, *seed, encoding).unwrap();
                e.validate().unwrap();
                assert!(
                    e.rules
                        .iter()
                        .all(|r| r.nodes.len() <= 6 && r.ops.len() <= 8)
                );
            }
        }
    }
}
#[test]
fn identifier_encoding_preserves_roles_and_resources() {
    for family in generalization::protocol().families.keys() {
        let a = generalization::initial(family, 101, "identity").unwrap();
        let b = generalization::initial(family, 101, "relabeled").unwrap();
        assert_eq!(a.world.matter_total, b.world.matter_total);
        assert_eq!(a.world.nodes.len(), b.world.nodes.len());
        let mut kinds_a: Vec<_> = a.world.nodes.values().map(|n| n.kind).collect();
        let mut kinds_b: Vec<_> = b.world.nodes.values().map(|n| n.kind).collect();
        kinds_a.sort();
        kinds_b.sort();
        assert_eq!(kinds_a, kinds_b);
        assert!(b.world.nodes.keys().all(|id| *id >= 1000));
        assert!(b.world.edges.values().all(|e| e.class == Class::Structural));
        assert_eq!(a.rules, b.rules.into_iter().rev().collect::<Vec<_>>());
    }
}
