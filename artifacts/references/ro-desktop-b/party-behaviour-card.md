# Party Behaviour Card — Issue 133

Authority: `reference-native.png` SHA-256 `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`, rect `[1107,505,215,269]`; control inventory; manual-attested research from `research/manual-attested-behaviour`.

## Source state

- One Party/Friends Window. Image 79 uses a two-choice radio group: `友達` unselected and `パーティー` selected.
- Party mode shows five logged-in member rows. Each row owns a name, parenthesised map location, green HP meter, and current/maximum HP fact.
- Five icon buttons are visible. Only the final icon is confidently mapped: Leave Party. Memo, Info, Target, and Search remain unavailable because their old-client behavior is unattested.
- Chrome owns title drag, close, and focused Escape. No minimize control exists.

## Gestures and transitions

| Gesture | Source state | Result | Rejection |
| --- | --- | --- | --- |
| Click Party/Friends choice | Either mode | Exactly one choice selected; affected list and action availability update in one version/frame | Unknown choice: `ActionRoutingError`, immutable |
| Click member row | Party mode with membership | Exactly one selected member | Hidden/non-member state: `TransactionRejectedError`, immutable |
| Click Memo/Info/Target/Search | Any | No transition | `TransactionRejectedError`, immutable |
| Click Leave | Party mode with membership | Membership becomes none; member rows clear; member-only actions disable | Repeat/unavailable: `TransactionRejectedError`, immutable |
| Drag title | Visible | Window follows pointer and clamps to desktop | Undeclared gesture rejected |
| Click close or focused Escape | Visible | Window closes | — |

## State Sets

- Radio choices: selected/unselected × idle/hover/pressed.
- Member rows: unselected/selected/unavailable × idle/hover/pressed. Friends mode renders the unavailable State Set rather than retaining selected or visible Party rows.
- Unattested icons: disabled × idle/hover/pressed with no implied live hover treatment.
- Leave: available/disabled × idle/hover/pressed.
- Party, Friends, and no-membership list surfaces are distinct semantic states. Only the Image-79 Party state is visual authority; missing list content is rendered as an honest empty source-style surface.
- `membership` describes the active mode and is always `none` in Friends mode. `party_membership` explicitly records whether the Party roster still exists so returning to Party can restore it without silently exposing Party membership in Friends; Leave clears both.

## Explicitly parked

The manual-attested no-party `パーティー作成` flow continues into a separate party-name entry dialog absent from Image 79. A lone generated button would be a partial unsupported flow, so v0.2 preserves the missing State Set here and does not fake or partially implement it. Party Settings is a separate absent Window and is also out of scope.
