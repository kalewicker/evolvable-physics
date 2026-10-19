use causal_alife::{
    core::*,
    environment::{self, Action, Channel},
    experiments, pilot,
};
#[test]
fn generated_distribution_valid_and_initials_share_rules() {
    for proposal in 2000..2016 {
        let first = pilot::generate(proposal, 0).unwrap();
        for initial in 0..4 {
            let env = pilot::generate(proposal, initial).unwrap();
            env.validate().unwrap();
            assert_eq!(first.native.rules, env.native.rules);
            assert_eq!(env, pilot::generate(proposal, initial).unwrap());
        }
    }
    assert!(pilot::generate(2000, 4).is_err());
}
#[test]
fn event_ceiling_is_atomic_and_counts_external_events() {
    let native = experiments::fixture("oscillator", 0).unwrap();
    let mut env = environment::Environment {
        profile: environment::PROFILE.into(),
        channels: vec![Channel {
            id: 0,
            start: 0,
            end: None,
            period: 1,
            action: Action::Supply { node: 0, amount: 1 },
        }],
        initial_activation: native.world.activation_total,
        injected: 0,
        extracted: 0,
        native,
    };
    let before = env.clone();
    assert_eq!(
        pilot::bounded_step(&mut env, 0, 2).unwrap_err(),
        "event_budget_exceeded"
    );
    assert_eq!(env, before);
    pilot::bounded_step(&mut env, 0, 3).unwrap();
    assert_eq!(env.native.world.next_event, 3);
    let before = env.clone();
    assert_eq!(
        pilot::bounded_step(&mut env, 0, 3).unwrap_err(),
        "event_budget_exceeded"
    );
    assert_eq!(env, before);
    assert_eq!(digest(&env), digest(&before));
}
