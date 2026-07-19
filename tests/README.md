# Blender Compatibility Tests

This directory preserves the compatibility work that was originally run from
temporary directories during the Blender 4.5 and 5.2 upgrade.

## Inventory

- `blender/smoke/`: 69 end-to-end or focused regression scripts.
- `blender/probes/`: 38 API discovery and diagnostic scripts.
- `fixtures/`: 6 reusable JSON configurations.

Smoke tests normally print a final `PME_*_RESULT OK` or a dictionary of checks.
Probes print API observations for comparison between Blender versions and do
not necessarily have a pass/fail result.

Generated output belongs in `tests/results/` or `tests/_work/`; both directories
are ignored. The release builder excludes the complete `tests/` directory from
the installable add-on ZIP.

## Local Blender Versions

The compatibility branch has been exercised with:

```text
D:\Blender\blender-4.5.8-windows-x64\blender.exe
D:\Blender\blender-5.2.0-windows-x64\blender.exe
```

To expose this checkout to either Blender while retaining factory preferences:

```powershell
$Repo = Resolve-Path .
$env:BLENDER_USER_SCRIPTS = Split-Path (Split-Path $Repo -Parent) -Parent
$Script = Join-Path $Repo "tests\blender\smoke\pme_lifecycle_smoke.py"
& "D:\Blender\blender-5.2.0-windows-x64\blender.exe" `
  --factory-startup --python $Script
```

Run the same script with the 4.5 executable for a two-version comparison.
Some UI and modal scripts require a normal window and intentionally terminate
Blender after printing their result.

## Release ZIP Install

Build the archive with Blender's bundled Python:

```powershell
& "D:\Blender\blender-5.2.0-windows-x64\5.2\python\bin\python.exe" `
  -P tools\build_release_zip.py --output _dist\pme-current.zip
```

Use isolated Blender state for the install test:

```powershell
$Root = Join-Path $env:TEMP "pme-release-smoke-52"
$env:BLENDER_USER_CONFIG = Join-Path $Root "config"
$env:BLENDER_USER_SCRIPTS = Join-Path $Root "scripts"
$env:PME_RELEASE_ZIP = (Resolve-Path "_dist\pme-current.zip")
& "D:\Blender\blender-5.2.0-windows-x64\blender.exe" `
  --factory-startup `
  --python tests\blender\smoke\pme_release_zip_install_smoke.py
```

The script derives the expected version from the repository's `bl_info`, then
checks install, discovery, enable, disable, and re-enable behavior.

## Fixtures And Private Data

Committed fixtures are synthetic or public community samples. The real
85-menu user configuration used for broad import/draw testing is deliberately
not committed. Supply it through `PME_ACTUAL_JSON` when running
`pme_actual52_import_draw.py`.

That script also expects:

```text
PME_ACTUAL_ROUNDTRIP
PME_ACTUAL_ERRORS
PME_EXPECTED_ADDON_ROOT
```

Optional third-party add-ons can be listed in `PME_DEPENDENCIES`, separated by
commas.

Comparison probes use explicit paths instead of machine-specific constants:

```text
PME_BASE_ERRORS / PME_TARGET_ERRORS
PME_OLD_EXPORT / PME_CURRENT_EXPORT
PME_BRUSH_ASSET_LIBRARY
```

## High-Signal Regression Set

The following scripts cover the most important shared behavior without trying
to build a complete Blender matrix:

```text
pme_release_zip_install_smoke.py
pme_lifecycle_smoke.py
pme_import_export_smoke.py
pme_community_config_smoke.py
pme_all_examples_draw_smoke.py
pme_modes_smoke.py
pme_editor_keymap_smoke.py
pme_user_keymap_cleanup_smoke.py
pme_panel_group_rebuild_smoke.py
pme_overlay_disable_smoke.py
pme_active_modal_disable_smoke.py
pme_modal_runtime_smoke.py
pme_hotkey_runtime_smoke.py
pme_layout_signature_smoke.py
pme_popup_header_async_smoke.py
pme_app_template_session_smoke.py
pme_third_party_operator_smoke.py
```

Run focused scripts next to a changed subsystem. Use the probes when a Blender
API difference must first be characterized.
