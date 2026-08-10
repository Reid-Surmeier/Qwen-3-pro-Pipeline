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

## Relationships

- One **Reference Screen** has one or more **Edit Briefs**.
- An **Edit Brief** declares **Preservation Invariants** and **Exact Copy**.
- An **Edit Brief** produces one or more **Render Passes**.
- **Asset Passes** and **Screen Passes** feed **Assembly**.
- **Fidelity Checks** gate both **Assembly** and the **Interactive Replica**.

## Example dialogue

> **Designer:** “Keep the Reference Screen's spacing and visual hierarchy, but replace the flower with a golf club.”
> **Developer:** “I’ll encode those as Preservation Invariants, run a focused Asset Pass for the club, assemble the approved asset and Exact Copy, then validate the Interactive Replica.”

## Flagged ambiguities

- “Prompt” previously meant both an unstructured sentence and the complete controlled input. Resolved: user intent is an **Edit Brief**; the provider prompt is compiled from it.
- “Stitching” obscured the difference between generating pixels and placing approved elements. Resolved: deterministic placement is **Assembly**.
- “No drift” previously mixed visual similarity with pixel identity. Resolved: strict preservation means a Fidelity Check reports zero changed pixels outside declared edit regions; similarity metrics remain useful for ranking generative donor images.
