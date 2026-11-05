# The Witcher 3: Wild Hunt — Complete Edition (`0100A0800E9C4000`)

Update 4.04b (v458752), SDK 15. CD PROJEKT RED's REDengine 3 (Saber Interactive's Switch port) on NVN. Modules `main` and `sdk`. **Mac only so far.**

## What it needs

| Setting | Where | Why |
|---|---|---|
| A 64 GiB alias region: `DM_ALIAS_SIZE=0x1000000000` | the build's environment file (`--env-file`) | A `DT_INIT_ARRAY` constructor reserves a 48 GiB region at `main+0x89e8`, and later allocations use fixed offsets up to alias +48.97 GiB, so no smaller alias works. On the Mac it is only a virtual-address mapping and commits only touched pages. The game needs no code patches (no `patches.py`). The phone's 4.375 GiB layout stays unsuitable until the allocator is ported. |
| Shader containers | `dm/gfx/tools/shader_split.py` (RDHS / FZLC readers) | The game keeps its shaders in `content/*/shadernx.cache` (and each DLC's) and `content/content0/staticshadernx.cache`: 29,673 shaders, against the 621 the generic split found. |
| Tessellation | `dm/gfx/nvn/nvn_tess.inc`, `dm/gfx/tools/dmsh_tess.py` | Terrain and water are tessellated quad patches (7 hull and 13 domain shaders, fractional_even, cw; the hulls set inside = min of the edges). Replayed with adaptive subdivision in a hardware-style layout. |
| Bindless texture handles through phis | translator `BindlessElimination.TryResolveHandlePhi` | Restores 1,866 texture reads (including the deferred shadow resolve and the probe ambient) that were forced to 0. |
| `depth_mode zero` | `game.tsv` | The game selects near = 0 depth. Without it the pipeline archive bundled with the app is built for near = −w and goes unused, and a first launch builds all 25,330 pipelines (about 3.5 minutes). |
| Prewarm seed list | `pso_manifest.tsv` | 1,031 rows (588 shaders, 434 render pipelines, 9 compute) recorded in two Mac app sessions from a White Orchard save. The prepare step builds them before the first frame, so a first start no longer compiles them during play. Other regions are not covered yet. |
| `DM_WINDOW=1 DM_PRESENT_LINK=0` | environment | Settings of the verified Mac runs. |

## Status (Mac)

- **Verified:**
  - startup videos, main menu and loading saves;
  - the Kaer Morhen bedroom (indoor) and White Orchard (road, hillside, lake shore) at 30 fps: 0 GPU faults, terrain and water complete;
  - a 19-minute scripted play session.
- **Not verified:** other regions (mountains, Novigrad, Skellige), combat and cutscenes, long free play, iPhone / iPad.
- **Open:**
  - 1,105 texture reads whose handle the game selects at run time still read 0 (`tex_dyn_slots` is off);
  - the tessellation path ignores a domain's declared spacing and handles quad domains only, which is enough for this game.
  - Startup audio underruns.
