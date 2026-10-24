# Problem framing with natural systems

When to read this: Use this reference when an algorithm, workflow, or logistics problem needs new candidate approaches.

## Start with the problem class

Describe the problem without naming a preferred implementation.
State the inputs, outputs, constraints, failure costs, and success measure.
Then ask whether a natural system solves an analogous class of problem.

Useful problem classes include:

- Routing and pathfinding.
- Load balancing and allocation.
- Resilience and fault tolerance.
- Scaling and distribution.
- Consensus and coordination.
- Scheduling and timing.
- Information flow and shared memory.
- Iteration and optimization.
- Caching and resource storage.
- Exploit-explore and stopping decisions.

## Extract the mechanism

Do not copy the surface appearance of the natural system.
Extract the rule that produces the useful behavior.

| Problem | Natural system | Transferable mechanism |
| --- | --- | --- |
| Routing | Slime mold or ant trails | Reinforce useful paths and decay unused paths |
| Allocation | Ant foraging recruitment | Local signals recruit effort toward useful sources |
| Resilience | Biodiversity or mycelial rerouting | Redundant functions and alternate routes |
| Scaling | Vascular branching | Hierarchical fan-out with bounded local cost |
| Consensus | Bee nest-site selection | Commit after support reaches a quorum |
| Scheduling | Circadian feedback | Adjust timing from feedback instead of fixed polling |
| Information flow | Pheromone trails | Shared external state that fades over time |
| Optimization | Evolution or immune adaptation | Generate variation, test it, and retain useful changes |
| Exploit vs. explore / patch leaving | Animal foraging | Leave a source when its expected marginal return falls below alternatives |

## Translate the mechanism

Write the transfer in plain engineering terms.

Example:

```text
Problem: Requests pile up behind one dispatcher.
Natural analogy: Ant foraging.
Mechanism: Workers use local signals and reinforce productive routes.
Candidate design: Partition the queue, publish local load, and let workers select the least-loaded eligible partition.
```

The candidate design must stand without the analogy.
If you cannot describe it without animal or plant terms, the mechanism is not yet clear.

## Use recurring motifs carefully

Natural systems often use:

- Decentralized decisions.
- Local rules.
- Feedback loops.
- Redundancy.
- Selective boundaries.
- Signals that strengthen or decay.
- Variation followed by selection.

These motifs can generate alternatives.
They do not prove that an alternative is correct.

## Verify with engineering

Test each candidate against:

- Correctness requirements.
- Latency and throughput.
- Resource cost.
- Security and privacy boundaries.
- Failure recovery.
- Observability.
- Operational ownership.
- Relevant standards.

Reject the candidate if the mechanism fails a real constraint.
Do not claim that a design is good because it is natural.
That is an appeal-to-nature fallacy.

## Compare approaches

Generate at least one conventional approach and one analogy-derived approach.
Compare them with the same criteria.
Keep a hybrid when it combines useful mechanisms without extra operational cost.
Prefer the simpler design when evidence does not distinguish them.

## Communication check

Use the natural parallel in the final explanation only when it improves understanding.
Keep it short.
Lead with the actual mechanism and design.
Remove the analogy if it becomes decoration.

## Final check

- Did you define the problem before choosing an analogy?
- Did you extract a mechanism instead of copying a metaphor?
- Can the proposed design be explained without the analogy?
- Did you compare it with a conventional alternative?
- Did you validate cost, correctness, and failure behavior?
- Did you reject any natural feature that does not transfer?

## Sources

- Tero et al., ["Rules for Biologically Inspired Adaptive Network Design"](https://doi.org/10.1126/science.1177894), on transport networks modeled from slime mold behavior.
- Seeley et al., ["Stop Signals Provide Cross Inhibition in Collective Decision-Making by Honeybee Swarms"](https://doi.org/10.1126/science.1210361), on distributed consensus and competing signals.
- Charnov, ["Optimal foraging, the marginal value theorem"](https://doi.org/10.1016/0040-5809(76)90040-X), on when a forager should leave a resource patch.
