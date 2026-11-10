# The Witcher 3: Wild Hunt — Complete Edition (0100A0800E9C4000): the rewriter's patches of this game's own builds. dm/tools/patch_nso.py loads every profile's patches.py and applies
# those of a module's NSO build ID (FRAME_STEP as described there: stubs in the patch area that read the state page the loader writes).
#
# Render size. The game renders 1280x720 by its own choice: the size is fixed in code (no 1280/720 pair exists in main's data). Every site that fixes it reads the host's size from the
# state page instead, so the loader can render any size and shape (loader.c dm_render_size_apply, DM_RENDER_SIZE). With the size at 0 (no setting) every stub runs the original
# instructions, so the game keeps its 1280x720. The pools and rendering.ini are the loader's part, from the profile's render_size_pools / render_size_ini rows (game.tsv). This build's
# fixups table carries RENDER_SIZE, which turns that part and the launcher setting on.
#   state +0x40 u32 width, +0x44 u32 height (the pair also as one u64), +0x48 / +0x4c the same as floats (bits); written by the loader
# Sites (4.04b main):
#   - the dynamic-resolution cap, 8 width / height pairs in main+0x85df6c..0x861290: movz wN,#0x44a0,lsl 16 (1280.0) / #0x4434 (720.0), then fmov;
#   - integer output sizes: the size getter main+0x85bbd0 / 0x85bbd8, the size function main+0x3880 / 0x3888, the viewport set main+0xfee3f0 / 0xfee3f4;
#   - the UI target's size, a 64-bit constant 1280 | 720 << 32 built at main+0x1026124..0x102612c (menus cropped to 1280x720 without it);
#   - the tiled-lighting compute buffers (main+0x101f700): fixed 720p sizes 3,815,424 (81 x 23 tiles x 2,048) and 724,224 (41 x 23 x 768) bytes. At a larger size their dispatches
#     (main+0x1022c34, main+0x1022d18) write past the end, into the HUD's vertex buffer: the HUD disappears;
#   - Vert+: the main camera's perspective setter call main+0x383ea8 (bl 0x1ec864: x0 camera, s0 vertical FOV in degrees, s1 aspect = width / height). The game's FOV is vertical, so a
#     narrower picture loses its sides. For an aspect narrower than 16:9 the stub widens the FOV to 2 atan(k tan(FOV / 2)), k = (16/9) / aspect, so the picture keeps the 16:9 width and
#     shows more above and below; at 16:9 or wider it changes nothing (wider shapes get more at the sides, the game's own Hor+)
import struct
from nso_asm import ADRP, B, STP_PRE, LDP_POST

s_w, s_h, s_wh, s_wf, s_hf = 0x40, 0x44, 0x40, 0x48, 0x4c

def ldrw(t, n, off): return 0xb9400000 | ((off // 4) << 10) | (n << 5) | t
def ldrx(t, n, off): return 0xf9400000 | ((off // 8) << 10) | (n << 5) | t
def cbnzw(t, skip): return 0x35000000 | ((skip & 0x7ffff) << 5) | t   # skip in instructions
def cbzw(t, skip): return 0x34000000 | ((skip & 0x7ffff) << 5) | t
def addwi(d, n, imm): return 0x11000000 | (imm << 10) | (n << 5) | d
def lsrwi(d, n, sh): return 0x53007c00 | (sh << 16) | (n << 5) | d
def mulw(d, n, m): return 0x1b007c00 | (m << 16) | (n << 5) | d
def cbnzx(t, skip): return 0xb5000000 | ((skip & 0x7ffff) << 5) | t
def bl(frm, to): return B(frm, to) | 0x80000000
def movzw(t, imm, sh=0): return 0x52800000 | ((sh // 16) << 21) | (imm << 5) | t
def movkw(t, imm, sh): return 0x72800000 | ((sh // 16) << 21) | (imm << 5) | t
def movzx(t, imm, sh=0): return 0xd2800000 | ((sh // 16) << 21) | (imm << 5) | t
def movkx(t, imm, sh): return 0xf2800000 | ((sh // 16) << 21) | (imm << 5) | t
def hexw(*ws): return b''.join(struct.pack('<I', w) for w in ws).hex()

# Vert+ stub (assembled with clang): saves the setter's arguments (x0-x3, s1-s4), k = (16/9) / s1; when k > 1, s0 = atan(k tan(s0 pi / 360)) 360 / pi with the game's tanf / atanf;
# restores and tail-branches to the setter (x30 keeps the caller's return). Words 18, 21 and 32 are the branches, placed by their targets below
vertplus = [
    0xd10143ff,   #  0 sub sp, sp, #0x50
    0xa9047bfd,   #  1 stp x29, x30, [sp, #0x40]
    0xa90007e0,   #  2 stp x0, x1, [sp]
    0xa9010fe2,   #  3 stp x2, x3, [sp, #0x10]
    0x2d040be1,   #  4 stp s1, s2, [sp, #0x20]
    0x2d0513e3,   #  5 stp s3, s4, [sp, #0x28]
    0x5291c730,   #  6 mov w16, #0x8e39              16/9
    0x72a7fc70,   #  7 movk w16, #0x3fe3, lsl #16
    0x1e270205,   #  8 fmov s5, w16
    0x1e2118a5,   #  9 fdiv s5, s5, s1               k
    0x1e2e1006,   # 10 fmov s6, #1.0
    0x1e2620a0,   # 11 fcmp s5, s6
    0x540001cd,   # 12 b.le +14 (word 26)            16:9 or wider: unchanged
    0xbd0033e5,   # 13 str s5, [sp, #0x30]
    0x529f46b0,   # 14 mov w16, #0xfa35              pi / 360
    0x72a781d0,   # 15 movk w16, #0x3c0e, lsl #16
    0x1e270206,   # 16 fmov s6, w16
    0x1e260800,   # 17 fmul s0, s0, s6
    0,            # 18 bl tanf
    0xbd4033e5,   # 19 ldr s5, [sp, #0x30]
    0x1e250800,   # 20 fmul s0, s0, s5
    0,            # 21 bl atanf
    0x5285dc30,   # 22 mov w16, #0x2ee1              360 / pi
    0x72a85cb0,   # 23 movk w16, #0x42e5, lsl #16
    0x1e270206,   # 24 fmov s6, w16
    0x1e260800,   # 25 fmul s0, s0, s6
    0xa94007e0,   # 26 ldp x0, x1, [sp]
    0xa9410fe2,   # 27 ldp x2, x3, [sp, #0x10]
    0x2d440be1,   # 28 ldp s1, s2, [sp, #0x20]
    0x2d4513e3,   # 29 ldp s3, s4, [sp, #0x28]
    0xa9447bfd,   # 30 ldp x29, x30, [sp, #0x40]
    0x910143ff,   # 31 add sp, sp, #0x50
    0,            # 32 b setter
]
tanf, atanf, setter, vp_site = 0x1f793b0, 0x1f79bd0, 0x1ec864, 0x383ea8   # tanf / atanf: main's import stubs (jump slots)


def render_size(ctx):
    def stub(site, origs, rd, field, wide=False, keep=(), at_site=None):
        # site: origs (asserted) replaced by a branch to: adrp xrd, state; ldr rd, [xrd, #field]; cbnz rd, +n; origs; keep; b back. rd is the origs' destination, dead before
        # them; keep = original instructions among the replaced ones that must still run (relocatable, no rd use); at_site = all replaced words in their order at the site
        ctx.site(site, hexw(*(at_site or [*origs, *keep])))
        start = ctx.here()
        ctx.emit(ADRP(rd, ctx.here(), ctx.state)); ctx.emit((ldrx if wide else ldrw)(rd, rd, field))
        ctx.emit((cbnzx if wide else cbnzw)(rd, len(origs) + 1))
        for w in origs: ctx.emit(w)
        for w in keep: ctx.emit(w)
        ctx.emit(B(ctx.here(), site + 4 * (len(origs) + len(keep))))
        return start
    # Dynamic-resolution cap: (site, register) of the width (1280.0) and height (720.0) moves
    caps_w = [(0x85df80, 10), (0x85e0b0, 8), (0x85e424, 9), (0x85e584, 9), (0x85e7c8, 9), (0x85e8ec, 10), (0x85ee0c, 9), (0x86125c, 10)]
    caps_h = [(0x85df6c, 11), (0x85e0d4, 8), (0x85e410, 10), (0x85e570, 10), (0x85e7b4, 10), (0x85e8d8, 11), (0x85edf8, 10), (0x861290, 10)]
    for sites, field, imm, what in ((caps_w, s_wf, 0x44a0, 'width'), (caps_h, s_hf, 0x4434, 'height')):
        for off, rd in sites:
            ctx.put(off, [B(off, stub(off, [movzw(rd, imm, 16)], rd, field))], f'dynamic-resolution cap {what} from the host size (state +{field:#x})')
    # Integer output sizes
    for off, rd, field, imm, what in ((0x85bbd0, 8, s_w, 1280, 'size getter width'), (0x85bbd8, 8, s_h, 720, 'size getter height'),
                                      (0x3880, 8, s_w, 1280, 'size function width'), (0x3888, 8, s_h, 720, 'size function height'),
                                      (0xfee3f0, 1, s_w, 1280, 'viewport width'), (0xfee3f4, 2, s_h, 720, 'viewport height')):
        ctx.put(off, [B(off, stub(off, [movzw(rd, imm)], rd, field))], f'{what} from the host size (state +{field:#x})')
    # UI target size: movz x8,#1280; mov w1,#1; movk x8,#720,lsl 32 → x8 = the width | height << 32 pair
    ctx.put(0x1026124, [B(0x1026124, stub(0x1026124, [movzx(8, 1280), movkx(8, 720, 32)], 8, s_wh, wide=True, keep=[movzw(1, 1)],
                                          at_site=[movzx(8, 1280), movzw(1, 1), movkx(8, 720, 32)]))],
            'UI target size (width | height << 32) from the host size (state +0x40)')
    # Tiled-lighting buffers: count (w8, stored at sp+0x18) and size (w0, the allocation) of each, movz + movk pairs, from the tile counts of the host size. The 720p constants are
    # exactly A = 2048 bytes x (ceil(W/16) + 1) x ceil(H/32) = 81 x 23 x 2048 and B = 768 x (ceil(W/32) + 1) x ceil(H/32) = 41 x 23 x 768 (count = bytes / 4); the stub computes the
    # same from the state's size. x9 / x10 are saved on the stack around it
    for off, rd, tile, sh, mult, orig, what in ((0x101f768, 8, 16, 4, 512, 3815424 // 4, 'buffer A count'), (0x101f774, 0, 16, 4, 2048, 3815424, 'buffer A size'),
                                                (0x101f7a0, 8, 32, 5, 192, 724224 // 4, 'buffer B count'), (0x101f7ac, 0, 32, 5, 768, 724224, 'buffer B size')):
        origs = [movzw(rd, orig & 0xffff), movkw(rd, orig >> 16, 16)]
        ctx.site(off, hexw(*origs))
        start = ctx.here()
        body = [STP_PRE(9, 10, 31, -16), 0, ldrw(9, rd, s_w), ldrw(10, rd, s_h), cbzw(9, 11),
                addwi(9, 9, tile - 1), lsrwi(9, 9, sh), addwi(9, 9, 1), addwi(10, 10, 31), lsrwi(10, 10, 5), mulw(rd, 9, 10), movzw(9, mult), mulw(rd, rd, 9),
                LDP_POST(9, 10, 31, 16), 0,
                LDP_POST(9, 10, 31, 16), *origs, 0]   # not set: the original constants
        for i, w in enumerate(body):
            here = ctx.here()
            ctx.emit(ADRP(rd, here, ctx.state) if i == 1 else B(here, off + 8) if i in (14, len(body) - 1) else w)
        ctx.put(off, [B(off, start)], f'tiled-lighting {what} from the tile counts of the host size (720p constants in the original)')
    # Vert+
    ctx.site(vp_site, hexw(bl(vp_site, setter)))
    start = ctx.here()
    for i, w in enumerate(vertplus):
        here = ctx.here()
        ctx.emit(bl(here, tanf) if i == 18 else bl(here, atanf) if i == 21 else B(here, setter) if i == 32 else w)
    ctx.put(vp_site, [bl(vp_site, start)], 'main camera FOV: Vert+ for aspects narrower than 16:9 (exact, 2 atan(k tan(FOV/2)))')
    ctx.render_size = 1


BINDING = [
    {'what': 'The Witcher 3 render size and Vert+: the fixed 1280x720 size sites, the tiled-lighting buffer sizes and the main camera FOV read the host size (DM_RENDER_SIZE)',
     'now': 'build', 'goal': 'build', 'purpose': 'rendering',
     'checked': 'Mac, 4.04b: 1280x720 (unset), 1920x1080, 1440x1080, 2560x1080 and the screen shape, outdoor save, 2026-11-10',
     'why': "the size is constants in this build's code (no size in its data or config the host could set; rendering.ini's size alone leaves the scene passes at 720p), "
            'and the tiled-lighting buffers are sized from 720p tile counts at their allocation'},
]
FRAME_STEP = {'d27fd8a515077f340c66cec23b13c0fa': render_size}
