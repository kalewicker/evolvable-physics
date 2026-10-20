# Generator v1: reachable structural scope

This is a source-level inductive argument for the frozen `p01-generator-v1` in `src/pilot.rs`, using the admitted `src/runtime.rs` semantics. It is not a proof about every rule permitted by the kernel, a formal verification certificate, or an impossibility result for active persistence. P00 fixtures already exercise node deletion/recycling outside this generator's restricted distribution.

## Assumptions fixed by the source

Every generated initial state has eight original nodes, eight directed immutable Contact edges forming a ring, and zero to eight parallel kind-0 Structural edges. There are no environment channels. The eight rule slots choose only the eight disclosed templates. Matched two-node templates require either a Contact or a Structural edge. Unary CreateNode creates a node with zero free matter/activation and creates no incident edge. CreateEdge matches a Contact pair and uses precisely that ordered pair. The kernel creates/deletes only Structural edges; Contact edges cannot be removed. DeleteNode rejects any node incident to any edge. Operations in an inapplicable rule are staged and discarded together.

## Induction

Initially all Structural endpoints are original Contact-ring nodes. Assume Contacts remain the initial ring, every Structural endpoint pair is an original ring pair, all original nodes remain, and all newer nodes are isolated.

1. Unary state changes and Burn do not change node membership or edges. Contact-pair Transfer touches only original nodes.
2. CreateNode adds an isolated, unfunded node. It cannot add a Contact edge or attach that node to a Structural edge.
3. CreateEdge requires an existing Contact pair, so it adds only a Structural edge on an original ring pair. DeleteEdge removes a Structural edge and returns matter; neither changes the Contact ring.
4. The DeleteEdge+DeleteNode template matches a Structural pair, hence original nodes. Deleting its Structural edge does not remove the target's immutable Contact edges. DeleteNode therefore rejects the whole rule, including the staged edge deletion. It commits no transition.
5. New nodes have no edges and therefore cannot match either two-node template family. No resource-transfer or node-deletion rule can target them. Their zero matter/activation prevents funded birth or Burn. Unary SetState/AddState may still change their state, at no declared Burn cost in this template set.

These cases preserve the invariant. **Original nodes cannot be deleted; created nodes cannot be attached, funded or deleted; node deletion and node-replacement turnover are unreachable in this generator.** This is a property of the templates plus initial distribution, not a kernel limitation. It does not prevent Structural-edge recycling among original ring pairs.

If the initial Structural-edge count is S, total matter is 80+S. The eight immutable Contact edges retain eight units. Nonnegative free matter and remaining Structural edges imply `node_count <= total_matter - 8 = 72+S <= 80`. All allocations remain live, so `next_node == node_count` and node IDs stay contiguous. These bounds apply while checked counters and the registered semantics remain valid; they do not authorize execution beyond the experiment's limits.

## Detector consequence

The frozen activity definition counts node birth/death, kind/state changes and Structural-edge changes, but excludes resource-only changes. A standalone CreateNode event therefore credits its newborn singleton, not the funding account's matter change. Later unary changes on that node also produce singleton groups. Such a node never joins a Structural component or a multi-node coactivity group. Both estimators require at least two nodes, so **no newborn can enter an eligible proposal** under these assumptions. Eligible proposals and AP tracks are restricted to the eight original nodes, and their node births/deaths/turnover stay zero. This does not rule out AP on original-node edge/state dynamics, nor establish maintenance.

The P01d trace/report scan corroborates these statements over the entire retained pilot corpus. The source argument extends beyond those finite observations only for this frozen generator and semantics. Changes to attachment templates, Contact topology, multi-operation birth rules, channels, activity credit or thresholds require a separately versioned protocol; do not silently repair the consumed pilot.
