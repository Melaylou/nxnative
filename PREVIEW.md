# The Witcher 3 preview branch

This branch, `witcher3-preview`, is a **preview** of the changes that bring **The Witcher 3: Wild Hunt — Complete Edition** (`0100A0800E9C4000`, version 4.04b) to nxnative on Apple-silicon Macs and M-series iPads. It's published so people can test it while the changes are discussed with nxnative's maintainer. It is experimental, not a replacement for [upstream nxnative](https://github.com/seedds/nxnative).

- **Base:** upstream `5474c6f3`, which is older than current upstream `main`. Upstream fixes made since then are **not** here.
- **Plan:** each general change will be proposed upstream separately, ported onto current `main`. This branch stays a test build and won't be merged as it is.
- **Discussion:** the proposal issue in [seedds/nxnative](https://github.com/seedds/nxnative/issues).

## What it adds
- **Shader containers:** readers for REDengine's shader containers (`shadernx.cache`, `staticshadernx.cache`): 29,673 shaders instead of 621.
- **Bindless fix:** a translator fix for bindless texture handles that reach the read through phis (1,866 reads that were returned as 0).
- **Tessellation:** adaptive tessellation without a Metal tessellator (a compute hull kernel, a ring-stitched expansion kernel, and the domain shader as a vertex function). It restores outdoor terrain and water.
- **60 fps toggle:** a "60 fps" option in the settings for games capped only by their present interval.
- **Deferred encoding fix:** the recorder now handles `setThreadgroupMemoryLength:atIndex:`, which fixes an iPad crash with the encode thread on.
- **The Witcher 3 profile:** shader tables, a prewarm seed list, `depth_mode zero`, and the build inputs in `dm/games/0100A0800E9C4000/build/`.

## Building
You need your **own** copy of the game: the base game (v0) and update v458752 NSPs, plus your own `prod.keys`. This repository holds no game files, and none will be shared, so please don't ask for builds or game files.

Set up the tools as in the [README](README.md), then follow the commands in [the profile's "Build from scratch"](dm/games/0100A0800E9C4000/README.md#build-from-scratch).
- **Tested hardware:** an M1 Max with macOS 27.2, and an M4 iPad Pro (16 GB) with iPadOS 27.2.
- **Metal version:** the shaders were built with Metal 32023.922 (Xcode 27.2), hence `--allow-other-metal`.
- **Machine load:** a full shader build takes about an hour and uses every CPU core. Don't play games on the same Mac while it runs.
- **iPad IPA:** it's ad-hoc signed. Re-sign it for your device and keep both entitlements in `dm/games/0100A0800E9C4000/build/ipad.entitlements`.
- **Other versions:** only 4.04b (base game + update) has been tested.

## Known limits
- **Resolution:** the game caps itself at 1280×720. MetalFX can upscale it.
- **Distant terrain:** looks soft on both platforms.
- **iPad:** one terrain copy pipeline (`R16Uint` target) is refused.
- **Texture reads:** 1,105 texture reads chosen at run time still read 0.
- **Tested areas:** White Orchard and Kaer Morhen. Other regions, combat and long play are untested.

Details: [the game's note](dm/games/0100A0800E9C4000/README.md).

## Reporting problems
Report problems with this branch in **this fork's issues, not upstream's**, since upstream doesn't have these changes yet. Include:
- the commit;
- the device and OS;
- the build command;
- the whole log (`~/Library/Logs/nxnative/0100A0800E9C4000.log` on the Mac).

Never attach game files or keys.
