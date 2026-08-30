# Third Reference Screen reuse probe

This throwaway planning prototype asks whether the screenshot-to-app contract can absorb a materially different pixel UI as a Reference Screen packet without changing shared engine code.

Open `index.html`. It needs no build step or server. The owner can free-play the candidate, run the two guided walkthroughs, and select **Check actual Godot seam** for the honest current verdict.

## Candidate

- Screen: GolfStudio main window, 474×403.
- Authority: `reference.png`.
- SHA-256: `76965f552c2337685de8b73a62df35465462e25b6bcf730ba02ebd49870ed3e4`.
- Preserved from: `/home/reidsurmeier/figma-ui-ux-qwen-pipeline/artifacts/figma/golfstudio-interactive-reference.png`.
- Provenance in the source project traces the underlying PlantStudio screenshot to `https://www.kurtz-fernhout.com/PlantStudio/screenMainWindow.gif`; GolfStudio changes the selected plant into the source-project's approved club asset.

## What the packet exercises

The manifest embedded in `index.html` supplies geometry, initial Window data, full State Set names, gesture bindings, and semantic values for eight already-decided modules: Window, Button, Tabs, Range, ScrollView, Dropdown, SelectionView, and Stepper. It requires no new gesture type.

The intentionally unsupported remainder is named rather than faked: native file chooser integration, the four-frame swing artwork, and canvas pan/rotate semantics. These require adapters or assets, not a new input gesture.

## Finding

The declarative interface is sufficient for this candidate in the throwaway reducer. The actual Godot zero-diff claim is not yet testable: `replica/scripts/desktop.gd` directly preloads `options_window.gd`, and `options_window.gd` explicitly builds and dispatches the Options controls. There is no frozen shared Godot engine implementation to compare before and after adding this packet.

The v0.3.0 specification must therefore make this candidate a post-engine tracer: once the shared Control Library exists, add only the candidate Reference Screen packet and require a zero diff under the shared engine/module source paths. Any shared-source change fails the reusability acceptance criterion and becomes a missing-interface issue.

## Manual verification

A browser drive exercised dropdown open/commit, Stepper, SelectionView, ScrollView wheel, Tabs, title drag, and the engine-diff audit. It produced eight Play Log entries, the expected mutated state, and zero browser console/page errors. `evidence-driven.png` is the resulting frame.
