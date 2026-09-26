# Analysis tooling — third-party notices

`tools/decode_reference_assets.py` contains an **altered Python implementation**,
not the original blast.c, based on the format documentation and canonical tables
in Mark Adler's `madler/zlib/contrib/blast/blast.c`, version 1.3 (24 Aug 2013).
The reference test vector is retained as a decoder self-test.

Source: https://github.com/madler/zlib/tree/develop/contrib/blast
Header blob read: `c5ef7ab5e6676ccbf3fb60ea09453a14c79a03c5`.

Copyright (C) 2003, 2012, 2013 Mark Adler

This software is provided 'as-is', without any express or implied
warranty. In no event will the author be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
claim that you wrote the original software. If you use this software
in a product, an acknowledgment in the product documentation would be
appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.

Mark Adler — madler@alumni.caltech.edu

Local analysis dependencies also include Pillow, pefile and Capstone, with their
own upstream licenses. They are not bundled into a Racing Bois runtime by this audit.
The legacy reference game/assets remain separately sourced material; extraction
does not alter their provenance or confer release rights.

## Optional private DirectDraw compatibility experiment

cnc-ddraw v7.1.0.0, https://github.com/FunkyFr3sh/cnc-ddraw/tree/v7.1.0.0,
is used only in an opt-in private legacy-reference launch, never bundled in the
new game or committed as a binary. Its tag-matched LICENSE is preserved beside
the temporary DLL. Archive SHA-256 measured locally:
`0b13ab89a64c9918189b1dadd449ef6ed3cb3b7b19cabd96d8adbd95505bb908`.

MIT License

Copyright (c) 2022 github.com/FunkyFr3sh

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
