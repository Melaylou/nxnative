# The Witcher 3: Wild Hunt — Complete Edition (`0100A0800E9C4000`)

Update 4.04b (v458752), SDK 15. CD PROJEKT RED's REDengine 3 (Saber Interactive's Switch port) on NVN. Modules `main` and `sdk`. **Mac app and iPad (M4) IPA**; how to build both from the NSPs: [Build from scratch](#build-from-scratch).

## What it needs

| Setting | Where | Why |
|---|---|---|
| A 64 GiB alias region: `DM_ALIAS_SIZE=0x1000000000` (iPad: 50 GiB, below) | the build's environment file: `--env-file build/mac_env.txt` (iPad `build/ipad_env.txt`) | A `DT_INIT_ARRAY` constructor reserves a 48 GiB region at `main+0x89e8`, and later allocations use fixed offsets up to alias +48.97 GiB, so no smaller alias works. On the Mac it is only a virtual-address mapping and commits only touched pages. The game needs no code patches (no `patches.py`). The phone's 4.375 GiB layout stays unsuitable until the allocator is ported. |
| Shader containers | `dm/gfx/tools/shader_split.py` (RDHS / FZLC readers) | The game keeps its shaders in `content/*/shadernx.cache` (and each DLC's) and `content/content0/staticshadernx.cache`: 29,673 shaders, against the 621 the generic split found. |
| Tessellation | `dm/gfx/nvn/nvn_tess.inc`, `dm/gfx/tools/dmsh_tess.py` | Terrain and water are tessellated quad patches (7 hull and 13 domain shaders, fractional_even, cw; the hulls set inside = min of the edges). Replayed with adaptive subdivision in a hardware-style layout. |
| Bindless texture handles through phis | translator `BindlessElimination.TryResolveHandlePhi` | Restores 1,866 texture reads (including the deferred shadow resolve and the probe ambient) that were forced to 0. |
| `depth_mode zero` | `game.tsv` | The game selects near = 0 depth. Without it the pipeline archive bundled with the app is built for near = −w and goes unused, and a first launch builds all 25,330 pipelines (about 3.5 minutes). |
| Prewarm seed list | `pso_manifest.tsv` | 1,031 rows (588 shaders, 434 render pipelines, 9 compute) recorded in two Mac app sessions from a White Orchard save. The prepare step builds them before the first frame, so a first start no longer compiles them during play. Other regions are not covered yet. |
| `DM_PRESENT_LINK=0`, `DM_AUDIO=1` | `build/mac_env.txt` | Settings of the verified Mac runs. |
| iPad: a 50 GiB alias region and the extended-virtual-addressing entitlement | `build/ipad_env.txt`, `DM_ENTITLEMENTS=build/ipad.entitlements` | Without extended virtual addressing iPadOS grants about 6 GB of address space. With it, an M4 (16 GB) granted 50.6 GB but refused 64.6 GB; the game reaches alias +48.97 GiB, so 50 GiB (`0xC80000000`) fits. The plist also asks for the increased memory limit (the build's default). Keep both entitlements when re-signing. |

## Status (Mac)

- **Verified:**
  - startup videos, main menu and loading saves;
  - the Kaer Morhen bedroom (indoor) and White Orchard (road, hillside, lake shore) at 30 fps: 0 GPU faults, terrain and water complete;
  - a 19-minute scripted play session.
- **iPad (M4, 16 GB, iPadOS 27.2):** loads the White Orchard save and plays at 30 fps (60 with the toggle, MetalFX on), 4,200 frames without a crash, footprint up to 2.8 GB. One pipeline is refused there (the terrain material copy, shader `2dcecea911db30ef`, into an `R16Uint` target); distant terrain looks soft (open).
- **Not verified:** other regions (mountains, Novigrad, Skellige), combat and cutscenes, long free play, iPhone.
- **Open:**
  - 1,105 texture reads whose handle the game selects at run time still read 0 (`tex_dyn_slots` is off);
  - the tessellation path ignores a domain's declared spacing and handles quad domains only, which is enough for this game.
  - Startup audio underruns.

## Resolution and console mode

- **Console mode works.** The game asks only for the operation and performance modes (`nn::oe`), never for the display resolution. In handheld mode (`DM_OPMODE=0`) it switches to its larger handheld HUD layout and changes some scene detail (118 render passes in a White Orchard frame, against 132 docked).
- **Both modes render at 1280×720 by default.** This is the game's own choice: `/bin/config/platform/nx/rendering.ini` sets `[Viewport] Resolution="1280x720"` and `[Rendering] ForcedRendererResolutionWidth = 1280 / Height = 720`, with no docked or handheld variant. The game's dynamic resolution has separate docked and handheld minimums, but it lowers the resolution only when the GPU is late, which did not happen on an M1 Max. So a docked 720p internal resolution is correct, not a host fault.
- **Render size (current, 2026-11-10): any size and shape** with `DM_RENDER_SIZE` (the launcher's **Render size**: `auto` fits the screen's shape). Off by default: the game keeps its 1280×720.
  - **Why config alone fails:** the size is constants in code. `rendering.ini` through `DM_ROMFS_OVERLAY` crashes at graphics start-up (`main+0x85b00c`, `main+0x860f28`: NVN memory pools sized for 720p); with larger pools the scene passes still render 1280×720 and the menus are cropped.
  - **Code** (`patches.py`, frame-step stubs reading state `+0x40`): the dynamic-resolution cap (8 width / height pairs), the size getter, the size function and a viewport set, and the UI target's size.
  - **Tiled-lighting buffers:** `main+0x101f700` allocates two compute buffers for 720p tile counts (3,815,424 and 724,224 bytes). At a larger size their dispatches write past the end into the HUD's vertex buffer, and the HUD disappears. The stubs size them from the tile counts, with the same formula that gives the 720p constants.
  - **Vert+:** the FOV is vertical, so a narrower shape would lose its sides. For shapes narrower than 16:9 the stub at the main camera's setter call (`main+0x383ea8`) widens the FOV to keep the 16:9 width. Wider shapes show more at the sides (the game's own behaviour).
  - **Loader** (`dm_render_size_apply`): it scales the profile's `render_size_pools` (render targets 148 MB at 720p, the swap chain 16 MB) with the pixel count, and rewrites `render_size_ini`'s lines into an overlay.
  - **Tested** on the Mac, outdoor save: 1920×1080, 1440×1080 (4:3), 2560×1080 (21:9), 2336×1080 and 1080×1080 render every scene pass at full size, with the HUD and the menus; no crash. At 2048×1536 memory peaks at 3.1 GB resident.
  - **The UI has layouts for 16:9, 4:3 and 21:9;** other shapes keep a 16:9 area in the middle for the HUD and menus.
  - **Not yet checked:** an iPad run, cutscenes, long play.
- **For a sharper picture:** MetalFX upscaling (`DM_PRESENT_UPSCALE=metalfx`) costs about 1.5–2 ms of GPU per frame for 1280×720 → 4286×2411 on an M1 Max. A frame's GPU time is otherwise about 10–11 ms (p50), 14–16 ms (p95) of the 33.3 ms at 30 fps.

## Build from scratch

Inputs: the base NSP (v0) and update v458752 NSP in one folder (`<NSP folder>`), `prod.keys`, this repository, Xcode with the Metal toolchain, and a Python venv set up as in the top-level README. Run from the repository root; the work folder holds the extraction (about 35 GB), the shader store and the outputs.

```sh
G="$PWD/dm/games/0100A0800E9C4000/build"   # absolute: build_ipa.sh reads DM_ENTITLEMENTS from its own working folder
# Mac app
python3 scripts/build_ipa_from_nsp.py <NSP folder> -k <prod.keys> --platform mac-app --work-dir <work folder> \
  --allow-other-metal --env-file $G/mac_env.txt -o <out>/TheWitcher3.app --keep-extracted
# iPad IPA (game files pushed separately with scripts/push_romfs.sh, as the build prints)
DM_ENTITLEMENTS=$G/ipad.entitlements python3 scripts/build_ipa_from_nsp.py <NSP folder> -k <prod.keys> --platform ios \
  --romfs separate --gpu none --work-dir <work folder> --allow-other-metal --env-file $G/ipad_env.txt -o <out>/TheWitcher3_ipad.ipa --keep-extracted
```

- `--allow-other-metal`: the shaders were built and verified with Metal 32023.922 (Xcode 27.2), not the 32023.921 that `dmsh_chain.lock` records.
- The iPad IPA is ad-hoc signed; re-sign it for the device keeping both entitlements.
- Expected: 29,673 shaders, shader chain `20cee2f628fe`.
