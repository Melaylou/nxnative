"""Integer entry points for integer colour outputs (dmsh_build.py fs_uint): automatic for shaders that write integer bits or constants,
forced by the fact "uint_entry": true for a shader that writes floats it computed (The Witcher 3's terrain material array copy 2dcecea911db30ef)."""
import ast
from pathlib import Path
import re
import unittest

path = Path(__file__).resolve().parents[1] / 'tools/dmsh_build.py'
node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'fs_uint')
scope = {'re': re}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
fs_uint = scope['fs_uint']

HEAD = 'struct main0_out\n{\n    float4 m_26 [[color(0)]];\n};\n\n'
COPY = HEAD + ('fragment main0_out main0(main0_in in [[stage_in]], texture2d<float> t [[texture(0)]], sampler s [[sampler(0)]])\n{\n    main0_out out = {};\n'
               '    float4 _54 = t.sample(s, float2(0.5), level(0.0));\n    out.m_26.x = _54.x;\n    out.m_26.y = _54.y;\n    out.m_26.z = _54.z;\n    out.m_26.w = _54.w;\n    return out;\n}\n')
BITS = HEAD + ('fragment main0_out main0(main0_in in [[stage_in]])\n{\n    main0_out out = {};\n    out.m_26.x = as_type<float>(7u);\n    return out;\n}\n')


class FsUint(unittest.TestCase):
    def test_float_copy_gets_none_by_default(self):
        self.assertEqual(fs_uint(COPY), (None, 0))

    def test_integer_bits_get_main0_u(self):
        out, mask = fs_uint(BITS)
        self.assertIn('fragment main0_out_u main0_u(', out); self.assertEqual(mask, 0)

    def test_forced_copy_gets_main0_u(self):
        out, mask = fs_uint(COPY, True)
        self.assertEqual(mask, 0)
        self.assertTrue(out.startswith(COPY))   # main0 itself is unchanged: the float uses keep their entry point
        u = out[len(COPY):]
        self.assertIn('struct main0_out_u\n{\n    uint4 m_26 [[color(0)]];\n};', u)
        self.assertIn('fragment main0_out_u main0_u(', u)
        self.assertIn('return main0_out_u{as_type<uint4>(out.m_26)};', u)   # the bits, nothing converted


if __name__ == '__main__':
    unittest.main()
