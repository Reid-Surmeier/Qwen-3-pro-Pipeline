# System Menu Behaviour Card

## Source authority

- Reference: `artifacts/references/ro-desktop-b/reference-native.png`
- SHA-256: `f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f`
- Native rectangle: `[1328, 505, 204, 273]`
- Button copy and order: `セーブポイントへ`, `キャラクター選択`, `サウンド設定`, `環境設定`, `ショートカット`, `ゲーム終了`, `return to game`
- Assembly is deterministic. Prototype code and plates are discarded; no provider request is used.

## State Sets

The minimize Control and all seven source buttons expose `idle`, `hover`, and `pressed` interaction phases and settle back to `idle`. Minimize swaps the expanded `204×273` plate for a purpose-built `204×27` top Window; it never crops the expanded Window at runtime. Restore preserves expanded geometry and position.

## Gestures

- `Drag` moves continuously, clamps to the desktop, and reverses to the source position.
- `Activate` commits one Control action after pressed feedback.
- `Escape` is contextual and belongs to the frontmost closeable Window before the Desktop fallback runs.

## Destination policy

| Control | Result |
| --- | --- |
| `セーブポイントへ` | Reject with `ActionRoutingError`; live-session travel is outside the replica. |
| `キャラクター選択` | Reject with `ActionRoutingError`; the character screen is outside the replica. |
| `サウンド設定` | Open or raise the existing Options Window without changing its position or semantic state. |
| `環境設定` | Reject with `ActionRoutingError`; no source-complete destination Window exists. |
| `ショートカット` | Reject with `ActionRoutingError`; no source-complete destination Window exists. |
| `ゲーム終了` | Reject with `ActionRoutingError`; process exit is outside the replica. |
| `return to game` | Close System Menu in one committed state. |

The System Menu Window-state adapter owns every `OpenWindow` Control exactly once. Only the Options route can enter committed action history; rejected destinations preserve the previous state byte-for-byte.

## Contextual Escape

- Another frontmost closeable Window consumes Escape for its own declared close action; System Menu and unrelated Windows remain unchanged.
- Frontmost System Menu consumes Escape as `return to game`.
- If no visible closeable Window handles Escape, the Desktop opens or raises only System Menu while preserving its geometry and semantic state.
