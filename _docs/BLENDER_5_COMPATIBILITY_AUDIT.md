# Blender 5 Compatibility Audit

Snapshot date: 2026-07-20

Target: Blender 5.2 LTS, with Blender 4.5 LTS retained as the compatibility
baseline.

## Current Count

- Repository commits including this audit snapshot: 49.
- Compatibility commits after the automated-release baseline (`0ec77a9`):
  46.
- Confirmed defect groups committed as `fix:`: 36.
- Documentation and test-infrastructure commits: 10.
- Preserved test scripts: 108 (70 smoke tests and 38 probes).
- Preserved reusable JSON fixtures: 6.

The conservative bug count is therefore **36 confirmed and fixed defect
groups**. A fix commit may update several related call sites, so this is a
lower-bound issue count rather than a raw count of changed lines or API names.
Tests that passed without requiring a code change are recorded as validated
coverage, not counted as bugs.

## Fix Ledger

| Commit | Area | Confirmed issue |
| --- | --- | --- |
| `ecb6447` | Preferences UI | Legacy preference panel identifiers no longer resolved on modern Blender. |
| `ee42b1b` | Area handling | Blender 5 could not safely use the legacy `ScrArea` space swap path. |
| `1737333` | Modal timers | Delayed modal callbacks could execute more than once. |
| `67c58d9` | Examples | The camera-view example used an obsolete operator command. |
| `d22849a` | Editor UI | Header menu types changed and could not be resolved on Blender 5. |
| `0683899` | UI hooks | Button context-menu hooks were left registered during lifecycle changes. |
| `9dc2e9d` | Custom icons | Icons added after startup were not loaded by refresh. |
| `1ead3d3` | Paint UI | Palette templates changed in Blender 5.2. |
| `ac1cb94` | Paint brushes | Paint controls still assumed legacy local brush data instead of brush assets. |
| `8ca3b04` | Imports | Removed operators caused legacy pie slots to collapse instead of preserving layout. |
| `259ab38` | Mesh selection | Multi-loop selection operator commands were removed. |
| `2bf3273` | UV editing | Mirrored UV operator commands were removed. |
| `ec26b66` | Sculpt paint | Sculpt color sampling operator commands changed. |
| `fc255fd` | Collections | Collection move operator commands changed. |
| `7bcb5dc` | Sculpt | Automasking properties moved away from the legacy brush paths. |
| `75589e5` | Brush falloff | Curve preset and curve mapping controls changed. |
| `d8b1e17` | Paint input | Input sample controls moved to new RNA paths. |
| `3c57d5b` | Geometry Nodes | Modifier input access changed from legacy generated properties. |
| `263c734` | Examples | The bmesh edge-property example used an obsolete property. |
| `d2cb4e8` | Area handling | Direct Blender 5 area-memory mutation was unsafe. |
| `5d5fa88` | Layout internals | Private `UILayout` memory access was invalid on Blender 5. |
| `fd4a9fb` | Modal operators | Modal priority moved to the supported operator API. |
| `ceeb394` | Popup UI | Popup window header options were lost on the modern area path. |
| `6bd41c3` | Paint settings | Unified paint setting properties moved. |
| `08dc443` | Brush strokes | Brush stroke-method properties changed. |
| `2ba2a97` | Viewport | Wireframe display RNA paths changed. |
| `c71fd4b` | Persistence | Menu backup filenames could collide during rapid writes. |
| `0637e00` | Installation | Add-on refresh during `enable_on_install` could unregister a partial initialization. |
| `c5560d0` | Lifecycle | Idle wait operators remained registered after disable. |
| `2aeddc6` | Overlay lifecycle | Active overlay draw handlers and timers survived add-on disable. |
| `eaf32d8` | Modal context | Timer/script invocation with no area crashed while constructing an overlay. |
| `5518e51` | Modal lifecycle | Active modal overlays and removed RNA pointers survived add-on disable. |
| `aa04526` | Layout wrappers | PME's panel layout wrapper rejected Blender 5.2 UILayout keywords. |
| `e164837` | User keymaps | Empty legacy PME user-keyconfig overrides accumulated and could not invoke a menu. |
| `0256811` | Menu polling | Scripts, previews, nested calls, and runtime menu draws bypassed menu poll checks; poll errors also escaped operators. |
| `5d9aab1` | Scripted menu calls | `open_menu` reported unavailable menus as successful, allowed disabled execution, and leaked kwargs after invalid Stack Key slots. |

## Validated Coverage

The following areas were tested without being counted as additional bugs:

- Add-on source enable/disable/re-enable on Blender 4.5 and 5.2.
- Release ZIP install, discovery, enable, disable, and re-enable in isolated
  Blender user directories.
- All supported PME modes: pie, regular menu, dialog, script, macro, modal,
  sticky, panel, hidden panel, and property.
- Legacy JSON migration and exact synthetic import/export round trips.
- Public community 5.1-era configuration import and representative UI draws.
- Editor keymap registration, including `3D View` and `3D View Generic`.
- Empty/default PME user-keyconfig overrides are removed without changing
  valid PME overrides or unrelated Blender shortcuts on Blender 4.5 and 5.2.
- Menu poll checks are consistent across hotkeys, scripts, previews, nested
  calls, embedded draws, and runtime menu classes; runtime poll errors cancel
  safely on Blender 4.5 and 5.2.
- F3 operator search opens before and after PME re-enable with Developer Extras
  enabled and a dynamic PME Macro registered on Blender 4.5 and 5.2.
- `open_menu` rejects missing, disabled, poll-blocked, and invalid Stack Key
  targets while clearing temporary execution locals on Blender 4.5 and 5.2.
- Autorun, register, unregister, and cached script lifecycle tests are
  self-contained, parallel-safe across Blender versions, and leave no files.
- Complete native `UILayout` parameter coverage for PME's panel wrapper on
  Blender 4.5 and 5.2, including version-specific compatibility parameters.
- Short-press fallback, long-hold activation, chord matching, chord timeout,
  and active-operator cleanup on Blender 4.5 and 5.2.
- Panel Group rebuild, reorder, removal, and repeated unregister.
- App-template reload with preference data and custom preview icons.
- Overlay drawing, normal expiration, and disable while active.
- Modal normal execution, no-area cancellation, and disable while active.
- Side-area show/hide through public APIs.
- All bundled examples drawing under the compatibility layer.
- Real user configuration: 85 menus, 759 items, 70 visible menus, and 408
  drawn items, with exact 4.5/5.2 round-trip and error-set comparisons at
  version 1.19.31.
- Eight installed third-party dependencies enabled together with the real
  configuration, reducing missing-operator layout reports from 98 to 51.
- A MACHIN3tools operator executed through a PME script menu and changed
  Blender from Object Mode to Edit Mode.

## Evidence Location

- Durable regression scripts: `tests/blender/smoke/`
- API discovery and one-off diagnostic probes: `tests/blender/probes/`
- Synthetic and community fixtures: `tests/fixtures/`
- Execution and data-handling notes: `tests/README.md`

The original temporary copies and generated output were not used as the source
of truth after this snapshot. Private configuration data, generated RNA/API
snapshots, `.blend` files, logs, and installed-release directories remain
outside version control.

## Remaining Gaps At Pause Point

- The full 85-menu configuration passes on Blender 4.5 and 5.2 at version
  1.19.31 with identical exported JSON and equivalent captured error sets.
- PME's hold and chord state machines are covered, but operating-system-level
  keyboard queue dispatch is not an automated interaction matrix.
- Major installed third-party add-ons were enabled, representative menus were
  drawn, and one external operator was executed through PME, but every
  external operator was not executed.
- Platform coverage is Windows only.
- Blender versions other than 4.5 and 5.2 are not part of the current matrix.

This pause point is suitable for auditing completed work. It is not a claim
that every PME workflow is fully compatible with Blender 5.2.
