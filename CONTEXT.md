# Reference-Preserving UI Generation

This context describes a repeatable system for transforming an existing interface while preserving its visual identity, then producing an interactive counterpart.

## Language

**Reference Screen**:
The source interface image whose composition and visual relationships are authoritative.
_Avoid_: Inspiration image, loose reference

**Edit Brief**:
A structured description of intended changes to a Reference Screen.
_Avoid_: Prompt, request blob

**Preservation Invariant**:
A visual or semantic relationship that must remain unchanged during a Render Pass.
_Avoid_: Preference, suggestion

**Exact Copy**:
Text that must appear verbatim in the approved interface.
_Avoid_: Suggested wording, sample text

**Render Pass**:
One image-model invocation with a fixed Edit Brief, inputs, and seed.
_Avoid_: Attempt, random generation

**Asset Pass**:
A Render Pass that produces one isolated reusable interface element.
_Avoid_: Full-screen generation

**Screen Pass**:
A Render Pass that produces a composed interface view.
_Avoid_: Asset generation

**Assembly**:
The placement of approved assets and Exact Copy into a screen composition.
_Avoid_: Stitching

**Fidelity Check**:
A comparison of a Render Pass or Interactive Replica against the Reference Screen and Preservation Invariants.
_Avoid_: Vibe check

**Interactive Replica**:
A working software view derived from an approved screen composition.
_Avoid_: Screenshot, mockup

**Source Game**:
The real game or application being replicated, and the authority for how a control behaves.
_Avoid_: The original, the inspiration

**Behaviour Card**:
The record of one control type's behaviour in the Source Game — gesture, expected visible response, timing in frames, reversibility, whether the source shows a hover state — with its primary evidence. States plainly when something is unverified, and marks anything specified from intent as intent-specified.
_Avoid_: Spec, description, requirement

**Control Library**:
The reusable implementations of control types, one per type, each with its frozen interface and contract tests. A new Reference Screen brings a new manifest and new assets, not new engine code.
_Avoid_: Widgets, components

**Control Catalogue**:
The named set of control types the system can bring alive.
_Avoid_: Feature list

**State Set**:
The full set of visual states one control owns — idle, hover, pressed, settled or active, and disabled where the Source Game has one.
_Avoid_: Variants, versions

**Missing State**:
A state of a control that the Reference Screen does not show, because a screenshot captures only one state per control. Produced by deterministic derivation where the source's rendering is a known transform, and by an Asset Pass otherwise.
_Avoid_: Extra state, generated asset

**Playtester**:
An agent that operates the Interactive Replica through real input events and produces its own evidence. It is never given the builder's evidence to grade.
_Avoid_: Reviewer, tester, QA agent

**Play Log**:
What a Playtester produces: one record per action — control, gesture, expected behaviour from the Behaviour Card, what was observed, whether the UI responded, and the frames that show it. The verdict is computed from it, never asserted by the Playtester.
_Avoid_: Report, review, verdict

**Window Issue**:
One GitHub Issue covering one window of a Reference Screen. Windows are built and verified individually, then composed.
_Avoid_: Task, subtask

**Release**:
One pull request covering a whole Reference Screen, folding every Window Issue. The owner reviews versions, never fragments.
_Avoid_: PR per window, increment


## Relationships

- One **Reference Screen** has one or more **Edit Briefs**.
- An **Edit Brief** declares **Preservation Invariants** and **Exact Copy**.
- An **Edit Brief** produces one or more **Render Passes**.
- **Asset Passes** and **Screen Passes** feed **Assembly**.
- **Fidelity Checks** gate both **Assembly** and the **Interactive Replica**.
- A **Reference Screen** is decomposed into **Window Issues**, which fold into one **Release**.
- Every control in a window has a **State Set**; the states the Reference Screen does not show are its **Missing States**.
- A **Behaviour Card** takes its authority from the **Source Game** and tells both the builder and the **Playtester** what a control must do.
- A **Playtester** produces a **Play Log**; the verdict is computed from the log, and a **Fidelity Check** is a backstop to it, never a substitute.

## Example dialogue

> **Designer:** “Keep the Reference Screen's spacing and visual hierarchy, but replace the flower with a golf club.”
> **Developer:** “I’ll encode those as Preservation Invariants, run a focused Asset Pass for the club, assemble the approved asset and Exact Copy, then validate the Interactive Replica.”

## Flagged ambiguities

- “Prompt” previously meant both an unstructured sentence and the complete controlled input. Resolved: user intent is an **Edit Brief**; the provider prompt is compiled from it.
- “Stitching” obscured the difference between generating pixels and placing approved elements. Resolved: deterministic placement is **Assembly**.
- “No drift” previously mixed visual similarity with pixel identity. Resolved: strict preservation means a Fidelity Check reports zero changed pixels outside declared edit regions; similarity metrics remain useful for ranking generative donor images.
- "Reviewer" named an agent that graded evidence someone else produced. Retired: the agent that judges an **Interactive Replica** is a **Playtester**, and it produces its own evidence by playing.
- "Animation" suggested tweening. Resolved: in the Source Game every measured transition completes in one frame (Issue #115); aliveness is an instant **State Set** swap, not easing.
- "Pixel-exact" mixed two claims when the Reference Screen is itself a lossy capture. See ADR 0006 and Issue #114.
