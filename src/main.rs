use causal_alife::{
    core::*,
    detector_fixtures, environment, environment_analysis, environment_branch_fixtures,
    environment_branches, environment_fixtures, experiments, generalization, integration_fixtures,
    intervention_fixtures, interventions,
    runtime::{self, Matcher},
};
use std::path::Path;
fn run() -> Result<()> {
    let a: Vec<String> = std::env::args().collect();
    match a.get(1).map(String::as_str) {
        Some("integration-fixtures") if a.len()==3 => {
            let dir=Path::new(&a[2]);std::fs::create_dir(dir).map_err(|e|e.to_string())?;
            let suite=integration_fixtures::suite()?;
            std::fs::write(dir.join("suite.json"),serde_json::to_vec_pretty(&suite).unwrap()).map_err(|e|e.to_string())?;
            for c in suite.cases.iter().filter(|c|c.initial.native.seed==0) {
                environment::save(&dir.join(format!("{}-checkpoint.json",c.family)),&c.epochs[2].state)?;
                environment::save(&dir.join(format!("{}-expected.json",c.family)),&c.epochs[11].state)?;
            }
            println!("96 environment-detector cases plus legacy logging and maintenance controls. Independent audit pending.");
        }
        Some("analysis-equivalence") if a.len()==4 => {
            #[derive(serde::Deserialize)] struct Case { initial:Experiment, frames:Vec<runtime::Frame>, detection:causal_alife::analysis::Detection }
            #[derive(serde::Deserialize)] struct Suite { cases:Vec<Case> }
            let suite:Suite=serde_json::from_slice(&std::fs::read(&a[2]).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
            for c in &suite.cases { if environment_analysis::analyze_native(&c.initial,&c.frames)?!=c.detection {return Err("analysis_engine_equivalence_mismatch".into());} }
            let receipt=serde_json::json!({"schema":"p00g-analysis-equivalence-v1","cases":suite.cases.len(),"all_outputs_equal":true});
            std::fs::OpenOptions::new().write(true).create_new(true).open(&a[3]).and_then(|mut f| {use std::io::Write;f.write_all(&serde_json::to_vec_pretty(&receipt).unwrap())}).map_err(|e|e.to_string())?;
            println!("{} equivalent detector cases",suite.cases.len());
        }
        Some("generalization-panel") if a.len()==3 => {
            let dir=Path::new(&a[2]);std::fs::create_dir(dir).map_err(|e|e.to_string())?;
            let suite=generalization::suite()?;
            std::fs::write(dir.join("suite.json"),serde_json::to_vec_pretty(&suite).unwrap()).map_err(|e|e.to_string())?;
            println!("176 generalization runs. Detector frozen; independent audit and admission pending.");
        }
        Some("detector-fixtures") if a.len()==3 => {
            let dir=Path::new(&a[2]);std::fs::create_dir(dir).map_err(|e|e.to_string())?;
            let suite=detector_fixtures::suite()?;
            std::fs::write(dir.join("suite.json"),serde_json::to_vec_pretty(&suite).unwrap()).map_err(|e|e.to_string())?;
            println!("144 detector cases; thresholds frozen in protocol; independent audit pending.");
        }
        Some("environment-branch-fixtures") if a.len()==3 => {
            let dir=Path::new(&a[2]);std::fs::create_dir(dir).map_err(|e|e.to_string())?;
            let suite=environment_branch_fixtures::suite()?;
            std::fs::write(dir.join("suite.json"),serde_json::to_vec_pretty(&suite).unwrap()).map_err(|e|e.to_string())?;
            for c in suite.cases.iter().filter(|c|c.initial.native.seed==0) {
                environment::save(&dir.join(format!("{}-source.json",c.family)),&c.source)?;
                std::fs::write(dir.join(format!("{}-request.json",c.family)),serde_json::to_vec_pretty(&c.arms[2].chain[0].request).unwrap()).map_err(|e|e.to_string())?;
                environment::save(&dir.join(format!("{}-expected.json",c.family)),&c.arms[2].epochs.last().unwrap().state)?;
            }
            println!("32 integrated cases / 160 arms / 960 continuation epochs. Independent audit pending.");
        }
        Some("environment-branch") if a.len()==5 => {
            let source=environment::load(Path::new(&a[2]))?;
            let request:environment_branches::Request=serde_json::from_slice(&std::fs::read(&a[3]).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
            environment_branches::publish(&source,&request,Path::new(&a[4]))?;
            println!("{}",digest(&environment_branches::load_bundle(Path::new(&a[4]))?));
        }
        Some("environment-branch-resume") if a.len()==5 => {
            let mut e=environment_branches::load_bundle(Path::new(&a[2]))?;
            let epochs:u64=a[3].parse().map_err(|_|"invalid_epoch_count")?;
            for _ in 0..epochs {environment::step(&mut e,Matcher::Indexed)?;}
            environment::save(Path::new(&a[4]),&e)?;
            println!("{}",digest(&e));
        }
        Some("environment-fixtures") if a.len() == 3 => {
            let dir=Path::new(&a[2]); std::fs::create_dir(dir).map_err(|e|e.to_string())?;
            let suite=environment_fixtures::suite()?;
            std::fs::write(dir.join("suite.json"),serde_json::to_vec_pretty(&suite).unwrap()).map_err(|e|e.to_string())?;
            for case in suite.cases.iter().filter(|c|c.initial.native.seed==0) {
                environment::save(&dir.join(format!("{}-checkpoint.json",case.mode)),&case.epochs[2].state)?;
                environment::save(&dir.join(format!("{}-expected.json",case.mode)),&case.epochs[7].state)?;
            }
            println!("64 environment cases / 512 epochs. Independent audit pending.");
        }
        Some("environment-resume" | "environment-resume-quiet") if a.len()==5 => {
            let mut env=environment::load(Path::new(&a[2]))?;
            let epochs:u64=a[3].parse().map_err(|_|"invalid_epoch_count")?;
            for _ in 0..epochs {
                if a[1]=="environment-resume-quiet" { environment::step_with_logging(&mut env,Matcher::Indexed,runtime::TraceMode::Disabled)?; }
                else { environment::step(&mut env,Matcher::Indexed)?; }
            }
            environment::save(Path::new(&a[4]),&env)?;
            println!("{}",digest(&env));
        }
        Some("intervention-fixtures") if a.len() == 3 => {
            let dir = Path::new(&a[2]);
            std::fs::create_dir(dir).map_err(|e| e.to_string())?;
            let suite = intervention_fixtures::suite()?;
            std::fs::write(dir.join("suite.json"), serde_json::to_vec_pretty(&suite).unwrap()).map_err(|e| e.to_string())?;
            for case in suite.cases.iter().filter(|c| c.source.seed == 0) {
                runtime::save(&dir.join(format!("{}-source.json", case.family)), &case.source)?;
                let arm = case.arms.iter().find(|a| a.name == "target").unwrap();
                std::fs::write(dir.join(format!("{}-request.json", case.family)), serde_json::to_vec_pretty(&arm.chain[0].request).unwrap()).map_err(|e| e.to_string())?;
                let mut expected = arm.chain[0].experiment.clone();
                expected.world = arm.frames.last().unwrap().world.clone();
                runtime::save(&dir.join(format!("{}-expected.json", case.family)), &expected)?;
            }
            println!("32 matched cases / 160 arms / 1280 continuation epochs. Independent audit pending.");
        }
        Some("branch") if a.len() == 5 => {
            let source = runtime::load(Path::new(&a[2]))?;
            let request: interventions::Request = serde_json::from_slice(&std::fs::read(&a[3]).map_err(|e| e.to_string())?).map_err(|e| e.to_string())?;
            let branch = interventions::branch(&source, &request)?;
            let dir = Path::new(&a[4]);
            std::fs::create_dir(dir).map_err(|e| e.to_string())?;
            let write_manifest = |status: &str| -> Result<()> {
                std::fs::write(dir.join("manifest.json"), serde_json::to_vec_pretty(&serde_json::json!({
                    "schema": "branch-bundle-v1", "execution_status": status,
                    "scientific_status": "untested", "source_digest": digest(&source),
                    "branch_digest": digest(&branch), "checkpoint_digest": digest(&branch.experiment)
                })).unwrap()).map_err(|e| e.to_string())
            };
            write_manifest("running")?;
            let publish = || -> Result<()> {
                runtime::save(&dir.join("source.json"), &source)?;
                std::fs::write(dir.join("branch.json"), serde_json::to_vec_pretty(&branch).unwrap()).map_err(|e| e.to_string())?;
                runtime::save(&dir.join("checkpoint.json"), &branch.experiment)?;
                write_manifest("complete")
            };
            if let Err(error) = publish() { let _ = write_manifest("failed"); return Err(error); }
            println!("{}", digest(&branch));
        }
        Some("fixtures") if a.len() == 3 => {
            let dir = Path::new(&a[2]);
            std::fs::create_dir(dir).map_err(|e| e.to_string())?;
            let suite = experiments::suite()?;
            std::fs::write(
                dir.join("suite.json"),
                serde_json::to_vec_pretty(&suite).unwrap(),
            )
            .map_err(|e| e.to_string())?;
            let mut exp = experiments::fixture("growth_recycling", 7)?;
            for _ in 0..5 {
                runtime::step(&mut exp, Matcher::Indexed)?;
            }
            runtime::save(&dir.join("checkpoint.json"), &exp)?;
            for _ in 0..7 {
                runtime::step(&mut exp, Matcher::Indexed)?;
            }
            runtime::save(&dir.join("expected.json"), &exp)?;
            println!("112 cases / 1344 epochs: Rust matcher agreement. Independent audit pending.");
        }
        Some("resume" | "resume-quiet") if a.len() == 5 => {
            let mut exp = runtime::load(Path::new(&a[2]))?;
            let epochs: u64 = a[3].parse().map_err(|_| "invalid_epoch_count")?;
            for _ in 0..epochs {
                if a[1]=="resume-quiet" { runtime::step_with_logging(&mut exp,Matcher::Indexed,runtime::TraceMode::Disabled)?; }
                else { runtime::step(&mut exp,Matcher::Indexed)?; }
            }
            runtime::save(Path::new(&a[4]), &exp)?;
            println!("{}", digest(&exp));
        }
        _ => return Err(
            "usage: causal-alife integration-fixtures NEW_DIRECTORY | analysis-equivalence SUITE NEW_RECEIPT | generalization-panel NEW_DIRECTORY | detector-fixtures NEW_DIRECTORY | environment-branch-fixtures NEW_DIRECTORY | environment-branch CHECKPOINT REQUEST_JSON NEW_DIRECTORY | environment-branch-resume BUNDLE EPOCHS NEW_CHECKPOINT | environment-fixtures NEW_DIRECTORY | environment-resume[-quiet] CHECKPOINT EPOCHS NEW_CHECKPOINT | fixtures NEW_DIRECTORY | intervention-fixtures NEW_DIRECTORY | branch CHECKPOINT REQUEST_JSON NEW_DIRECTORY | resume[-quiet] CHECKPOINT EPOCHS NEW_CHECKPOINT"
                .into(),
        ),
    }
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(1);
    }
}
