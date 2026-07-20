# Blender 5 Compatibility Audit

Snapshot date: 2026-07-20

Target: Blender 5.2 LTS, with Blender 4.5 LTS retained as the compatibility
baseline.

Current local testing excludes release ZIP construction and installation. The
historical ZIP results below remain recorded, while the current remote release
flow is treated as user-verified.

## Current Count

- Repository commits including this audit snapshot: 111.
- Compatibility commits after the automated-release baseline (`0ec77a9`):
  108.
- Confirmed defect groups committed as `fix:`: 52.
- Feature, documentation, and test-infrastructure commits: 56.
- Preserved test scripts: 129 (90 smoke tests and 39 probes).
- Preserved reusable JSON fixtures: 6.

The conservative bug count is therefore **51 confirmed and fixed defect
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
| `ee82f74` | Popup state | Safely closing Blender 5 Popup Screens discarded public editor state and reran the open command on every reopen. |
| `5a2c470` | Side Area | Blender 5 Side Area resizing depended on the desktop cursor's active Screen state, and joined Areas invalidated the original main-area RNA reference. |
| `a3a0daf` | Side Area sizing | Replacing an oversized Side Area editor reclamped against the already-shrunken main area, reducing a half-window side area to roughly one quarter. |
| `cd1e497` | User keymaps | Malformed legacy PME KeyMapItems with missing or unreadable operator properties could abort empty-item cleanup instead of being removed. |

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
- The exact startup/Homefile preference failure reported in Blender Artists
  post 5503 is covered directly. `active_pie_menu_idx` and `tag_filter` remain
  registered RNA properties, stay readable, and preserve assigned values while
  an empty Homefile is loaded without disturbing menu data. The regression
  passes on Blender 4.5, 5.0, and 5.2 without relying on custom IDProperties.
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
- Empty PME user-keyconfig cleanup also tolerates missing or unreadable
  operator properties reported in the community keymap-cleaner discussion
  around posts 5518 and 5573-5579. Such unusable PME items are treated as
  empty, while valid PME properties and unrelated shortcuts remain untouched.
  Missing-property handling, normal removal, and idempotence pass on Blender
  4.5, 5.0, 5.1, and 5.2 at version 1.19.48.
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
- Persistent Popup Areas retain public scalar Space RNA, the editor type, and
  status-bar visibility across close/reopen on Blender 5.0, 5.1, and 5.2.
  Open commands execute once as on the 4.5 reused-Screen path. Cache timers and
  state are fully removed on add-on disable; explicit header arguments still
  override restored state. The four-version regression uses `center=False`.
- The community-reported Popup Asset Browser crash path now has a dedicated
  non-invasive regression. `area="ASSETS"` opens a real File Browser in Asset
  mode with initialized parameters and exact 900 by 600 dimensions, then
  closes without losing the source window or leaving the Popup state timer.
  It passes on Blender 4.5, 5.0, 5.1, and 5.2 with `center=False`. This covers
  the reports in Blender Artists posts 4942, 4944, and 5170; it is validated
  coverage rather than a new defect count because no additional code change
  was required at version 1.19.46.
- Side Area SHOW/HIDE uses coordinate-based public split/join operations
  without moving the system cursor. LEFT, RIGHT, TOP, and BOTTOM restore the
  expected layout or consume a deliberately reused neighbor on Blender 5.2;
  representative horizontal and vertical paths pass on Blender 4.5, 5.0,
  and 5.1. Reused Blender 5 Areas with a different requested size are rebuilt
  after join rather than using cursor-dependent `screen.area_move`. Pending
  rebuild callbacks are removed during add-on disable and remain clear after
  re-enable on Blender 5.0, 5.1, and 5.2.
- The UI scaling and separator-width behavior reported in Blender Artists post
  5523 is covered by the same non-invasive Side Area test. Real SHOW/HIDE
  cycles pass with 0.75/THIN, 1.0/AUTO, and 2.0/THICK settings on Blender 5.2;
  the 2.0/THICK vertical path also passes on Blender 4.5 and 5.0. Requested
  300 px sides measure 290-300 px, do not multiply Areas, and the test restores
  the original UI preferences before exit.
- The oversized Side Area sequence reported in Blender Artists posts 5673 and
  5681 is covered without cursor input. A requested 2000 px Asset Browser is
  clamped to half of the combined available area; after changing it to the
  Geometry Nodes editor and reopening the Asset Browser, the side size remains
  stable and the Area count does not grow. Before the fix the 5.2 reproducer
  changed from 1046 px to 518 px; version 1.19.47 remains 1046 px on both
  calls. LEFT and TOP pass on 5.2, LEFT passes on 5.0 and 5.1, and the 4.5
  legacy resize path remains unchanged and passes its focused regressions.
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
- The uninitialized `PME_OT_restore_pie_prefs.move_flag` errors reported in
  Blender Artists posts 5457 and 5532 are covered by the modal-priority smoke
  test. Both real PME helper operators enter their modal state, while the
  public handler completes RELEASE, TIMER removal, and `finish()` without the
  removed private field on Blender 4.5, 5.0, 5.1, and 5.2. This validates the
  existing `fd4a9fb` fix and is not counted as another defect.
- The fractional Modal Property Step report from Blender Artists post 5638 is
  covered across Blender 4.5, 5.0, 5.1, and 5.2. A Step of 0.3 survives the
  temporary editor RNA property, PMI encoding, float decoding, and runtime
  +1/-1 property updates. This is validated coverage at version 1.19.47, not
  an additional defect count.
- Tag-group collapse from Blender Artists post 5539 is covered on Blender 4.5
  and 5.2. The real tree-group operator hides only the selected tag's menu
  links, preserves the collapsed group across a tree rebuild, and restores the
  links on expansion. The regression disables tree-state file persistence, so
  it does not modify the repository or user tree state. This is validated
  coverage rather than an additional defect count.
- Panel Group rebuild, reorder, removal, and repeated unregister. The reorder
  now uses the real `pme.panel_item_move` operator and its `finish()` callback,
  matching the unregister failure reported in Blender Artists post 5650. Two
  registered panels remain valid, repeated removal is idempotent, and no
  unregister warning or class leak occurs on Blender 4.5 or 5.2.
- The app-template crash path from Blender Artists post 5655 passes on Blender
  4.5, 5.0, and 5.2. After `wm.read_homefile(app_template="Sculpting")`, PME
  preferences and menu data remain available, its preview collection remains
  alive, and both load handlers stay singly registered. The larger private
  configuration test additionally covers 85 menus, 759 items, and custom
  preview icons; that user fixture remains intentionally outside the repository.
- The released-preview `NoneType` failure reported in Blender Artists post
  5459 is covered on Blender 4.5, 5.0, 5.1, and 5.2. After explicitly releasing
  the preview collection, name, ID, reverse-ID, and membership queries all
  return safe empty values; refresh then rebuilds both existing and newly added
  icons. This is separate from the `9dc2e9d` new-file refresh fix.
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
- On Blender 5.0.1 and 5.1.0, the 40-menu community fixture imports, migrates,
  and draws its representative Object menu. All 11 bundled example files
  import into 16 menus; all 8 visible menus and 38 items draw without errors.
  The community fixture reports the same 13 unavailable third-party operators
  on both versions, with no additional Blender API failures.
- Direct operators, string-based operators, bundled example commands,
  `bpy.types`, `bpy.context`, `bpy.data`, UILayout signatures, and Preferences
  panel mappings were compared across Blender 4.5.8, 5.0.1, 5.1.0, and 5.2.0.
  UV mirror commands execute both directions through the 5.0/5.1 `direction`
  API and the 5.2 axis API. Sculpt color sampling accepts a stable `location`
  wrapper argument across the 5.0-to-5.1 operator transition.
- Full signatures for the 56 directly used Blender operators were compared
  across 4.5, 5.0, 5.1, and 5.2. `object.move_to_collection` is the only
  parameter-set difference: its index-to-session-UID wrapper passes all four
  nested collection targets by both representations on Blender 5.0 and 5.1.
- Brush curve migration, UI property selection, six preset mappings, and menu
  drawing pass on all four versions. The test now detects
  `curve_distance_falloff_preset` from Brush RNA instead of incorrectly
  assuming it first appeared in Blender 5.2; it is already present in 5.0.
- Blender 5.0.1 and 5.1.0 pass focused runtime tests for automasking, brush
  stroke methods, brush-asset switching, Geometry Nodes modifier inputs,
  palette/brush special UI, unified paint settings, wireframe paths, and all
  native UILayout parameters used by PME.
- Editor keymaps, empty user-keymap cleanup, short/hold/chord hotkey state,
  normal and no-area modal execution, mode entry, and disable while a modal is
  active pass on Blender 5.0.1 and 5.1.0. The four tests backed by committed
  fixtures now resolve those fixtures by default and still allow environment
  overrides, so a missing variable cannot strand a Blender test process.
- Panel Group rebuild/reorder/removal, right-side Header extensions and Poll
  errors, Overlay disable cleanup, Stack Key visibility/expiry, generated
  Macro proxies, the public Macro invocation API, and Developer Search across
  add-on re-enable pass on Blender 5.0.1 and 5.1.0.
- Version 1.19.43 adapts UV mirror calls to the operator's detected RNA
  properties. Version 1.19.44 removes the new `location` argument only when
  the installed legacy sculpt operator does not expose it. Focused migrated
  command, helper, and menu-call tests pass on Blender 4.5, 5.0, 5.1, and 5.2.
- Version 1.19.45 restores safe in-session Popup editor-state memory on
  Blender 5 without retaining or deleting Screen data-blocks. Outliner string
  and Boolean state, status-bar state, command de-duplication, header updates,
  exact sizing, early destruction, and disable cleanup pass across the focused
  four-version matrix.
- Version 1.19.46 rebuilds differently sized adjacent Side Areas through the
  public join/split API instead of cursor-dependent resize dispatch. Exact
  requested sizing, SHOW/HIDE, four directions, callback cleanup, and
  disable/re-enable pass in the focused Windows matrix.
- Version 1.19.47 clamps replacement Side Areas against the combined main and
  adjacent dimensions instead of the already-reduced main dimension. Oversize
  editor swaps retain a stable half-area layout horizontally and vertically,
  while normal four-direction, callback cleanup, and 4.5 baseline regressions
  continue to pass.
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

The test README marks Area Move, Dynamic Modes, and the legacy full Side Area
script as interactive-only because they use cursor warping or simulated input.
The non-invasive Side Area toggle and disable scripts are counted above.
Results from the interrupted mouse-driven batch are excluded from this audit.

The original temporary copies and generated output were not used as the source
of truth after this snapshot. Private configuration data, generated RNA/API
snapshots, `.blend` files, logs, and installed-release directories remain
outside version control.

## Remaining Gaps At Pause Point

- The full 85-menu configuration passes on Blender 4.5 and 5.2 at version
  1.19.39 with byte-identical exported JSON and equivalent captured error
  signatures.
- PME's hold and chord state machines are covered, but operating-system-level
  keyboard queue dispatch is not an automated interaction matrix. A discarded
  Blender `Window.event_simulate` experiment delivered F13/F14 to modal
  handlers but not to either PME or a minimal control keymap, so it was not
  accepted as end-to-end keymap evidence.
- Major installed third-party add-ons were enabled, representative menus were
  drawn, and one external operator was executed through PME, but every
  external operator was not executed.
- Area Move still needs an explicitly reserved interactive desktop session.
  Its implementation intentionally warps the cursor to invoke Blender's
  interactive edge-move operation, so its interrupted mouse-driven results are
  not counted as compatibility evidence.
- Blender 5 safely deletes a persistent Popup Screen when its window closes.
  PME now captures and restores its public scalar editor state, but multi-Area
  split geometry, pointer/collection RNA, and per-region view transforms are
  not reconstructed. Isolated probes confirmed that fake/extra users do not
  prevent child-window Screen deletion, cross-Workspace Screen assignment is
  rejected, and forced Screen/Workspace data-block removal is unsafe on
  Blender 5.0. No such deletion path is used by PME.

This pause point is suitable for auditing completed work. It is not a claim
that every PME workflow is fully compatible with Blender 5.2.
