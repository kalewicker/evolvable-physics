use crate::{
    core::*,
    environment::{self, Environment},
    interventions::{self, Intervention},
    runtime,
};
use serde::{Deserialize, Serialize};
use std::path::Path;
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema: String,
    pub expected_source: String,
    pub operations: Vec<Intervention>,
}
impl Request {
    pub fn new(source: &Environment, operations: Vec<Intervention>) -> Self {
        Self {
            schema: "environment-intervention-v1".into(),
            expected_source: digest(source),
            operations,
        }
    }
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Receipt {
    pub schema: String,
    pub request_digest: String,
    pub before: String,
    pub after: String,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Branch {
    pub request: Request,
    pub receipt: Receipt,
    pub native_branch: interventions::Branch,
    pub environment: Environment,
}
pub fn branch(source: &Environment, request: &Request) -> Result<Branch> {
    source.validate()?;
    if request.schema != "environment-intervention-v1" {
        return Err("unknown_environment_intervention_schema".into());
    }
    if request.expected_source != digest(source) {
        return Err("stale_environment_intervention_source".into());
    }
    let native_branch = interventions::branch(
        &source.native,
        &interventions::Request::new(&source.native, request.operations.clone()),
    )?;
    let mut out = source.clone();
    out.native = native_branch.experiment.clone();
    out.validate()?;
    Ok(Branch {
        request: request.clone(),
        receipt: Receipt {
            schema: "environment-intervention-receipt-v1".into(),
            request_digest: digest(request),
            before: digest(source),
            after: digest(&out),
        },
        native_branch,
        environment: out,
    })
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    schema: String,
    execution_status: String,
    scientific_status: String,
    source_digest: String,
    branch_digest: String,
    checkpoint_digest: String,
}
fn publish_with_hook(
    source: &Environment,
    request: &Request,
    dir: &Path,
    mut hook: impl FnMut(&str) -> Result<()>,
) -> Result<()> {
    let b = branch(source, request)?;
    std::fs::create_dir(dir).map_err(|e| e.to_string())?;
    environment::save(&dir.join("source.json"), source)?;
    hook("source")?;
    runtime::publish_checkpoint(
        &dir.join("branch.json"),
        &serde_json::to_vec_pretty(&b).map_err(|e| e.to_string())?,
    )?;
    hook("record")?;
    environment::save(&dir.join("checkpoint.json"), &b.environment)?;
    hook("checkpoint")?;
    let manifest = Manifest {
        schema: "environment-branch-bundle-v1".into(),
        execution_status: "complete".into(),
        scientific_status: "untested".into(),
        source_digest: digest(source),
        branch_digest: digest(&b),
        checkpoint_digest: digest(&b.environment),
    };
    runtime::publish_checkpoint(
        &dir.join("manifest.json"),
        &serde_json::to_vec_pretty(&manifest).map_err(|e| e.to_string())?,
    )?;
    hook("manifest")?;
    Ok(())
}
pub fn publish(source: &Environment, request: &Request, dir: &Path) -> Result<()> {
    publish_with_hook(source, request, dir, |_| Ok(()))
}
/// Admission checks completion and recomputes the entire requested transition.
pub fn load_bundle(dir: &Path) -> Result<Environment> {
    let manifest: Manifest = serde_json::from_slice(
        &std::fs::read(dir.join("manifest.json")).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    if manifest.schema != "environment-branch-bundle-v1"
        || manifest.execution_status != "complete"
        || manifest.scientific_status != "untested"
    {
        return Err("incomplete_environment_branch".into());
    }
    let source = environment::load(&dir.join("source.json"))?;
    let record: Branch =
        serde_json::from_slice(&std::fs::read(dir.join("branch.json")).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    let checkpoint = environment::load(&dir.join("checkpoint.json"))?;
    if record != branch(&source, &record.request)?
        || checkpoint != record.environment
        || manifest.source_digest != digest(&source)
        || manifest.branch_digest != digest(&record)
        || manifest.checkpoint_digest != digest(&checkpoint)
    {
        return Err("environment_branch_identity_mismatch".into());
    }
    Ok(checkpoint)
}

#[cfg(test)]
mod recovery_tests {
    use super::*;
    use crate::environment_fixtures;
    #[test]
    fn child_writer() {
        let Ok(stage) = std::env::var("P00D_TEST_STOP") else {
            return;
        };
        let path = std::env::var("P00D_TEST_PATH").unwrap();
        let source = environment_fixtures::fixture("driven", 0).unwrap();
        publish_with_hook(
            &source,
            &Request::new(&source, vec![]),
            Path::new(&path),
            |at| {
                if at == stage {
                    std::process::exit(71);
                }
                Ok(())
            },
        )
        .unwrap();
        panic!("fault stage not reached");
    }
    #[test]
    fn fresh_process_exit_at_every_publication_boundary() {
        let root = std::env::temp_dir().join(format!("p00d-recovery-{}", std::process::id()));
        std::fs::create_dir(&root).unwrap();
        for stage in ["source", "record", "checkpoint", "manifest"] {
            let path = root.join(stage);
            let status = std::process::Command::new(std::env::current_exe().unwrap())
                .args([
                    "--exact",
                    "environment_branches::recovery_tests::child_writer",
                    "--nocapture",
                ])
                .env("P00D_TEST_STOP", stage)
                .env("P00D_TEST_PATH", &path)
                .status()
                .unwrap();
            assert_eq!(status.code(), Some(71));
            let loaded = load_bundle(&path);
            assert_eq!(loaded.is_ok(), stage == "manifest");
            if let Ok(env) = loaded {
                assert_eq!(env, environment_fixtures::fixture("driven", 0).unwrap());
            }
        }
        // The artifacts are deliberately retained in the temporary directory for inspection.
    }
    #[test]
    fn partial_pending_checkpoint_is_never_promoted_or_overwritten() {
        let root = std::env::temp_dir().join(format!("p00d-pending-{}", std::process::id()));
        std::fs::create_dir(&root).unwrap();
        let final_path = root.join("checkpoint.json");
        let pending = final_path.with_extension("pending");
        std::fs::write(&pending, b"{partial").unwrap();
        let env = environment_fixtures::fixture("driven", 0).unwrap();
        assert!(environment::save(&final_path, &env).is_err());
        assert!(!final_path.exists());
        assert_eq!(std::fs::read(&pending).unwrap(), b"{partial");
        assert!(environment::load(&final_path).is_err());
    }
}
