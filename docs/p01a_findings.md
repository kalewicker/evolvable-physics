# P01a: registered generator and engineering cost preflight

Date: 2026-10-19. **Engineering gate passed: 64/64 registered runs, 4,096 independently replayed epochs. Scientific status: untested.** The full proposed P01 pilot and E01 have not started.

The [registration](p01a_registration.md), [panel and limits](p01a_protocol.json), and [revision-2 source freeze](p01a_freeze.json) were recorded before the successful attempt. This is a deliberately narrow closed-environment distribution with eight rule slots; it is not a sample of all possible laws. Rules are shared across each proposal's four initial states. There were zero duplicate complete law sets, and no duplicates or invalid outcomes were discarded.

## Evidence and outcomes

[Independent audit](evidence/p01a-002/independent_audit.json) binds the [manifest](evidence/p01a-002/manifest.json) and complete raw-bundle checksum inventory. It independently regenerates the initial environments and replays candidates, scheduling, operation execution, parents, ledgers and final state. All 64 fixed slots completed their 64 epochs; none hit a limit or required a replacement. There were 18,969 applicable candidates and 18,081 native events, with no external events. Final worlds contained at most 65 nodes. Applicable candidates exclude full pattern matches whose operations were inapplicable; partial binding work is not counted by this observer.

| Measured quantity | Successful panel |
| --- | ---: |
| Child user + system CPU | 2.322386 seconds |
| Campaign elapsed, including replay/supervision | 15.790630 seconds |
| Full epoch trace output | 47,306,474 bytes |
| Observed child peak RSS | 5,210,112 bytes |
| Step / JSON serialization / writes | 1.563387 / 0.520051 / 0.086152 seconds |

Timings are release-build, observer-inclusive development measurements. CPU excludes parent replay, generation processes and `ps`. Step time includes one atomic staging clone but excludes the worker's additional rollback copy; campaign elapsed and child CPU include that work. Summary/source/checksum/log storage is additional to the reported trace bytes. These values are host-specific, and one run supplies no confidence interval on timing or rare-tail behavior.

Forced controls verified zero-event and zero-trace rollback, exact event/byte equality at the first epoch, rejection of the following whole epoch, wall expiry, sampled RSS expiry, nonzero-child infrastructure classification, and four corrupted-evidence rejections. Rust tests also verified that the event cap counts external supply and rolls back its ledgers. Three Python tests cover fixed-denominator failure accounting, exact campaign launch boundaries and killing/reaping a child when RSS observation fails. Rust tests, Clippy and formatting passed; original logs are published with the receipts.

Attempt [p01a-001](evidence/p01a-001/manifest.json) failed in the first forced control because the desktop sandbox denied `ps`. No panel slot ran. All original files remain locally; compact failed receipts are public. Revision 2 fixes failure accounting so all 64 slots remain represented even on infrastructure failure; its checks were completed before attempt 002. Attempt 002 used permission to observe RSS outside the sandbox. The original failed gate was not reclassified; seeds, thresholds, limits and the panel were unchanged. The revision-1 freeze is retained as [p01a_freeze_v1.json](p01a_freeze_v1.json).

## Cost scenarios and limits

Linear scaling to the proposed 512 runs × 1,000 epochs yields 0.080638 child CPU-hours at the observed mean, 0.209304 using the observed 95th-percentile run cost for every slot, or 0.268716 using the observed maximum. Corresponding full trace output is **5,913,309,250 bytes at the mean**, or 14,909,008,000 bytes if every slot had the observed maximum trace rate. These are scenarios, not forecasts, cost gates or upper bounds. Growth after epoch 64, unseen laws, long tails, detector replay and parent overhead can change costs substantially. No full-P01 storage/compute ceiling is admitted by these numbers.

The watchdog samples RSS, so short memory peaks can escape detection and a worker can overshoot between samples. It is not a hard instantaneous memory guarantee. Wall enforcement likewise includes polling and observation delay. Interrupted traces are retained, can contain a partial final record, and are not accepted as complete. Exact event and trace caps apply at whole-epoch publication boundaries.

The v1 distribution includes Contact-ring nodes that cannot be deleted while immutable Contact edges remain, making its DeleteNode template potentially inapplicable. This is a disclosed sampling bias, not repaired after observation. No detector or maintenance score has been assigned to generated trajectories. AP results from the existing fixture panel do not establish detector sensitivity/specificity on this distribution.

## P00 regression and next gate

The [full regression manifest](evidence/p01a-p00-regression-001/manifest.json) passed all retained audits and keeps P00 admitted. All seven suite JSON outputs are [byte-identical to P00g](evidence/p01a-p00-regression-001/suite_equivalence.json). Frozen P00f/P00g source and detector hashes remain unchanged. The P00 admission receipt's historical P01 checklist is intentionally preserved; this report and `status.json` describe the new readiness work.

Full P01 readiness remains false. The next bounded task is to register the full pilot's run/compute/storage ceilings and slow-tail policy, record the choice of sampled versus stronger memory enforcement, and integrate frozen detector reporting while retaining inconclusive cases. P01a's budget admits only its fixed preflight. The full pilot must retain every one of its own registered slots, cap hit and infrastructure error. E01 remains gated.

Raw local bundles are `artifacts/p01a-001`, `artifacts/p01a-002` and `artifacts/p01a-p00-regression-001`; they remain ignored. Public receipts contain original bytes. The standalone read-only audit script was added after sealing and checked the complete successful bundle. Later CLI metadata sets Cargo's default executable to `causal-alife`, preserving existing commands after adding `pilot-worker`; a zero-epoch CLI continuation passed. These packaging/report changes do not modify the frozen worker, generator or kernel.
