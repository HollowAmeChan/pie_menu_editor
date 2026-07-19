# Blender 5 Compatibility Audit

Snapshot date: 2026-07-20

Target: Blender 5.2 LTS, with Blender 4.5 LTS retained as the compatibility
baseline.

## Current Count

- Repository commits including this audit snapshot: 81.
- Compatibility commits after the automated-release baseline (`0ec77a9`):
  78.
- Confirmed defect groups committed as `fix:`: 48.
- Feature, documentation, and test-infrastructure commits: 30.
- Preserved test scripts: 123 (84 smoke tests and 39 probes).
- Preserved reusable JSON fixtures: 6.

The conservative bug count is therefore **48 confirmed and fixed defect
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
| `0c0c33c` | Poll context | Scripted poll expressions read ambient `bpy.context` through `C` instead of the invocation context, producing stale mode and area decisions. |
| `5adee96` | Macro safety | Missing or later-unregistered operators could leave half-built native Macros and crash Blender in `WM_operator_poll`. |
| `0e24c41` | Stack Key overlay | Stack Key notifications ignored the `Use Overlay` preference and displayed even when explicitly disabled. |
| `46ca655` | Popup context | Popup drawing still rewrote private `bContext.wm.area/region` memory on Blender 5 even though public context values were already correct. |
| `6f1136a` | Pie layout helper | Public `keep_pie_open(layout)` still dereferenced the obsolete private `uiLayout` structure on Blender 5. |
| `6c62e49` | Re-enable persistence | Blender 5 discarded all menus and their order when PME was disabled and enabled again because preference backup was restricted to older Blender versions. |
| `1ec8c98` | Macro operator safety | Public generated Macro operator IDs exposed Blender's native Macro directly, allowing stale child operators to crash Blender 5.2 before Python poll guards ran. |
| `d157065` | Popup sizing | Blender 5's public area duplication ignored PME's requested Popup Area dimensions and opened an oversized window. |
| `c5d5d8d` | Property persistence | Dynamically registered Property Mode values reset to defaults after add-on disable/re-enable on both supported Blender versions. |
| `51cafc7` | Popup lifecycle | Clearing a live persistent Popup Screen's users caused a Blender 5.2 ID reference-count underflow when the window closed. |
| `d07f835` | UV editing | Blender 5.0/5.1 `uv.copy_mirrored_faces` still used `direction`, while Blender 5.2 replaced it with `mesh_axis` and `uv_axis`. |
| `7fddb17` | Sculpt paint | Blender 5.0 retained `sculpt.sample_color` but rejected the `location` argument required by the Blender 5.1/5.2 replacement. |

## Validated Coverage

The following areas were tested without being counted as additional bugs:

- Add-on source enable/disable/re-enable on Blender 4.5 and 5.2.
- Core operator calls, string-based operator references, `bpy.types`,
  `bpy.context`, `bpy.data`, `UILayout` wrapper arguments, and all bundled
  example calls were re-audited against Blender 4.5 and 5.2. Reported missing
  symbols are confined to version-gated compatibility branches or deliberate
  legacy migration aliases.
- Blender 5.2 adds `ACTIONZONE_REGION_QUAD` but removes no event identifiers
  present in 4.5. PME keymap route names have the same missing legacy fallback
  set on both versions.
- Header extensions with PME's `_right` suffix register on the underlying
  Blender Header type, draw only in the right-aligned region, and remove their
  callback when the menu is deleted on Blender 4.5 and 5.2. False and failing
  Poll scripts suppress the extension without leaking exceptions into the
  Header draw callback.
- Property Mode values are removed with their runtime RNA property instead of
  reviving when a same-named property is recreated. Values configured not to
  persist also reset to their default during menu initialization on Blender
  4.5 and 5.2, including Blender 5's separate system-property storage.
- Disabling and re-enabling PME preserves exact menu order, mode-specific slot
  data for all ten supported modes, and non-default scalar preferences on
  Blender 4.5 and 5.2. Before the fix, the focused Blender 5.2 reproducer
  returned an empty menu list after re-enable.
- Loading an empty Homefile preserves exact menu order, all mode-specific data
  and slots for all ten modes, and scalar preferences on Blender 4.5 and 5.2.
- Bool, Int Vector, Float Vector, String, Enum, and Enum Flag Property Mode
  values survive both empty-Homefile loading and add-on disable/re-enable on
  Blender 4.5 and 5.2.
- Command Editor Apply updates the command editor's RNA value and the final
  stored menu item on Blender 4.5 and 5.2. This ruled out a suspected Blender
  5 system-property storage regression for the statically registered
  `PMIData.cmd` property.
- Existing generated `bpy.ops.pme.macro_*` IDs now resolve to ordinary
  operator proxies that validate the menu, Poll, and dependencies before
  entering an internal native Macro. A dependency removed after registration
  returns `CANCELLED`, stops later slots, removes the unsafe native type, and
  leaves the public proxy available on Blender 4.5 and 5.2.
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
- Scripted poll globals (`C` and PME's `bpy.context` proxy) follow the context
  passed by Blender and restore the previous context after both successful and
  failing polls on Blender 4.5 and 5.2.
- Macro operator dependencies are checked before native Macro registration and
  before every PME execution. Direct, post-build removal, and nested missing
  dependencies stop the complete Macro safely, while disabling the bad slot
  restores normal execution on Blender 4.5 and 5.2. Before the fix, the focused
  reproducer terminated Blender 5.2 with an access violation in
  `WM_operator_poll`.
- Scripts can invoke stored Macros through
  `bpy.ops.pme.invoke_macro(menu_name="...")`. The wrapper checks menu type,
  enabled state, poll conditions, missing dependencies, and explicit Macro
  cancellation before entering the native Macro path on Blender 4.5 and 5.2.
- Stack Key notifications stay hidden when `Use Overlay` is disabled or a
  specific slot is requested, display during normal cycling when enabled, and
  remove their handler and running state after expiry on Blender 4.5 and 5.2.
- Popup operators retain the legacy private context path on Blender 4.5 but
  make zero `c_utils.set_area/set_region` calls on Blender 5.2. Popup draw
  `context`, `bpy.context`, and PME's `C` still resolve to the source View3D
  area and region on both versions.
- Non-invasive Popup Area tests use `center=False` and therefore do not move
  the system cursor. Requested 320 by 240 client dimensions, synchronous
  creation, header visibility/position updates, automatic closing, and a
  header callback after early window destruction pass on Blender 4.5 and 5.2.
- Closing a persistent Popup Area before its asynchronous header update no
  longer produces a Blender 5.2 Screen user-count error. The callback detects
  the destroyed window, returns safely, and leaves PME enabled.
- `keep_pie_open(layout)` retains its legacy flag behavior and returns `True`
  on Blender 4.5. On Blender 5.2 it performs zero private layout accesses and
  returns `False`, allowing user scripts to detect that Blender exposes no
  supported keep-open API.
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
- All bundled examples drawing under the compatibility layer.
- Version 1.19.32 source tests cover poll routing, all menu mode entries,
  hold/chord hotkeys, popup area synchronization, and all bundled example
  draws on Blender 4.5 and 5.2; its release ZIP passes the full isolated
  install/enable/disable/re-enable lifecycle on both versions.
- Version 1.19.33 passes normal and missing-dependency Macro execution, dynamic
  Macro search lifecycle, add-on lifecycle, exact synthetic import/export, the
  40-menu community fixture, and isolated release ZIP installation on Blender
  4.5 and 5.2.
- Version 1.19.34 passes Stack Key visibility, normal overlay expiry, active
  overlay disable cleanup, normal script/Stack Key execution, and isolated
  release ZIP installation on Blender 4.5 and 5.2.
- Version 1.19.35 passes popup context routing, Popup Dialog mode, embedded
  panel popups, user and add-on Preferences popups, and isolated release ZIP
  installation on Blender 4.5 and 5.2.
- Version 1.19.36 passes the keep-open version contract, layout memory guard,
  normal menu UI, all bundled example draws, and isolated release ZIP
  installation on Blender 4.5 and 5.2.
- Version 1.19.37 passes safe external Macro invocation for valid, missing,
  wrong-mode, disabled, poll-blocked, explicitly stopped, and missing-operator
  targets; normal Macro execution, F3 search lifecycle, and isolated release
  ZIP installation also pass on Blender 4.5 and 5.2.
- Version 1.19.38 preserves all ten menu modes and scalar preferences across
  add-on disable/re-enable. Lifecycle, Property Editor, exact synthetic
  import/export, the 40-menu community fixture, app-template switching, and
  isolated release ZIP installation pass on Blender 4.5 and 5.2.
- Version 1.19.39 routes generated public Macro operator IDs through safe
  proxies. Direct valid and stale-dependency calls, missing and nested
  dependencies, the supported `invoke_macro` API, all menu modes, F3 search,
  add-on lifecycle, and isolated release ZIP installation pass on Blender 4.5
  and 5.2.
- Version 1.19.40 restores exact Popup Area client sizing on Blender 5.2 while
  retaining the Blender 4.5 path. Version 1.19.41 preserves six representative
  dynamic Property Mode value types across Homefile and add-on lifecycle
  changes. Version 1.19.42 closes persistent Popup windows without Blender 5.2
  Screen reference-count errors. Its isolated release ZIP lifecycle passes on
  Blender 4.5 and 5.2.
- Blender 5.0.1 and 5.1.0 pass the focused source/API set: add-on lifecycle,
  all ten menu modes, exact import/export, empty-Homefile persistence, six
  dynamic Property Mode value types, exact Popup Area sizing, and safe Popup
  destruction before the asynchronous header callback.
- Direct operators, string-based operators, bundled example commands,
  `bpy.types`, `bpy.context`, `bpy.data`, UILayout signatures, and Preferences
  panel mappings were compared across Blender 4.5.8, 5.0.1, 5.1.0, and 5.2.0.
  UV mirror commands execute both directions through the 5.0/5.1 `direction`
  API and the 5.2 axis API. Sculpt color sampling accepts a stable `location`
  wrapper argument across the 5.0-to-5.1 operator transition.
- Version 1.19.43 adapts UV mirror calls to the operator's detected RNA
  properties. Version 1.19.44 removes the new `location` argument only when
  the installed legacy sculpt operator does not expose it. Focused migrated
  command, helper, and menu-call tests pass on Blender 4.5, 5.0, 5.1, and 5.2.
- Real user configuration: 85 menus, 759 items, 70 visible menus, and 408
  drawn items, with byte-identical 4.5/5.2 round-trip JSON and identical
  normalized signatures for all 144 captured layout/script reports at version
  1.19.39.
- Eight installed third-party dependencies enabled together with the real
  configuration, reducing missing-operator layout reports from 98 to 51.
- A MACHIN3tools operator executed through a PME script menu and changed
  Blender from Object Mode to Edit Mode.

## Evidence Location

- Durable regression scripts: `tests/blender/smoke/`
- API discovery and one-off diagnostic probes: `tests/blender/probes/`
- Synthetic and community fixtures: `tests/fixtures/`
- Execution and data-handling notes: `tests/README.md`

The test README marks Area Move, Dynamic Modes, and Side Area scripts as
interactive-only because they use cursor warping or simulated input. Results
from the interrupted mouse-driven batch are excluded from this audit.

The original temporary copies and generated output were not used as the source
of truth after this snapshot. Private configuration data, generated RNA/API
snapshots, `.blend` files, logs, and installed-release directories remain
outside version control.

## Remaining Gaps At Pause Point

- The full 85-menu configuration passes on Blender 4.5 and 5.2 at version
  1.19.39 with byte-identical exported JSON and equivalent captured error
  signatures.
- PME's hold and chord state machines are covered, but operating-system-level
  keyboard queue dispatch is not an automated interaction matrix.
- Major installed third-party add-ons were enabled, representative menus were
  drawn, and one external operator was executed through PME, but every
  external operator was not executed.
- Area Move and Side Area still need a non-invasive automation harness or an
  explicitly reserved interactive desktop session. Their recent mouse-driven
  results are not counted as compatibility evidence.
- Blender 5.2 safely deletes a persistent Popup Screen when its window closes;
  unlike the 4.5 legacy path, per-Screen layout state is therefore not cached
  for a later reopen. Restoring that memory requires explicit state capture
  rather than manipulating Blender's ID user count.

This pause point is suitable for auditing completed work. It is not a claim
that every PME workflow is fully compatible with Blender 5.2.
