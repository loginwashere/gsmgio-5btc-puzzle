# First-Piece Spiral Variant Comparison

Variant names are `start-first_move-turn`. For Ulam centers, `TL`, `TR`, `BL`, and `BR` mean `(6,6)`, `(6,7)`, `(7,6)`, and `(7,7)` respectively (zero-based).

Corner labels are zero-based traversal positions (`0..195`), matching the established FEFE position 163. Ulam labels are true one-based infinite-spiral numbers; they may have gaps where the path lies outside the 14x14 window. `ASCII` is the number of printable bytes among the first 24 bytes. `Colors` includes FEFE as `F`. Cell bits use the authenticated mapping: black/blue = 1; white/yellow/FEFE = 0.

Large-integer columns use a fixed 16-base Miller-Rabin probable-prime screen; the two reported hits were independently confirmed with `sympy.isprime`.

Exact target decodes: `TL-D-CCW`.
Fully printable candidates: `TL-D-CCW`.
Best Ulam printability: 17/24 bytes (`TR-D-CW`).
Exact FEFE clue location (character 21, bit 4): `TL-D-CCW`.
Ulam paths exactly reversing a corner path (8): `TL-R-CW, TL-D-CCW, TR-D-CW, TR-L-CCW, BL-U-CW, BL-R-CCW, BR-U-CCW, BR-L-CW`.
Full-grid integer probable-prime hits: `TR-U-CCW`.
Prime-labeled-cell integer probable-prime hits: `TR-L-CW` (descriptive across the declared family, not standalone evidence).

## Corner-inward spirals (8 variants)

| Variant | Corner relation | Decode (first 192 bits) | ASCII | Colors | Match | Blue labels | Yellow labels | FEFE label; stream location | Full probable prime | Prime-label bits probable prime |
|---|---|---|---:|---|---|---|---|---|---|---|
| TL-D-CCW | authenticated | `gsmg.io/theseedisplanted` | 24/24 | `BBBBYBBBYYBBBBYBBYYBFYYBY` | forward | `7,15,23,31,47,55,63,87,95,103,111,127,135,159,183` | `39,71,79,119,143,151,167,175,191` | `163; char 21 bit 4` | False | False (44 cells) |
| TL-R-CW | corner dihedral | `4\xb3\xa75\xb6w>u0\xb1w\xa7t\xb15541\xb0v1s\xb15` | 16/24 | `BYBBBBBBYYBBBYBBBYYBYYFYB` | no | `5,21,29,37,45,53,61,85,93,101,117,125,133,157,189` | `13,69,77,109,141,149,165,173,181` | `177; char 23 bit 2` | False | False (44 cells) |
| TR-L-CCW | corner dihedral | `4\xb3;\x9bk9z\xe7\xe5\xee\x8d\x0cK\xb2\xb2\xb2<&\xe0\xd83s\xa8\xac` | 10/24 | `YBBBBBBBBBYYBBBYBBYYYFYYB` | no | `8,20,28,36,44,54,62,66,74,100,112,120,138,142,186` | `0,82,90,128,150,158,160,172,182` | `168; char 22 bit 1` | False | False (44 cells) |
| TR-D-CW | corner dihedral | `t\xe6\xb6\xce\xe6ii\x85\x8b\xbd?:bjjn\x98\xd8;!.vi\xa8` | 14/24 | `YBBBBBYYBBBBYBBBYYBBYYFBY` | no | `8,16,24,32,44,74,82,86,94,108,116,128,150,154,186` | `0,58,66,100,134,142,160,168,190` | `172; char 22 bit 5` | False | False (44 cells) |
| BR-U-CCW | corner dihedral | `\x9c\xb9\xa5\x99\xdc\xdbZ\x19\x5c\xfc\xbd\xd1\x91\xa5\xd9Y[\x18M\xc1\xd1\x9b\x99\x15` | 5/24 | `BYBBBBYBBBBYYBBBYBBYYFYYB` | no | `5,21,33,41,49,65,73,77,85,109,121,129,145,149,189` | `13,57,93,101,137,157,165,177,185` | `173; char 22 bit 6` | False | False (44 cells) |
| BR-L-CW | corner dihedral | `\xd6\xd9\xdc\xcd,\xe9\xcc]\xe9\xf9\xd4\xc2\xd4\xd4\xdd,L\x1d\x90\xc6\xce\xcc]D` | 6/24 | `BBBBYBYBBBBYBBBYYBBYYFYBY` | no | `3,11,19,31,47,63,71,75,83,99,107,119,143,147,183` | `39,55,91,127,135,155,163,175,187` | `167; char 21 bit 8` | False | False (44 cells) |
| BL-R-CCW | corner dihedral | `m\xac\xe5\xcd,\xce\xeb\xa3C+\x9f\x97\xca\xc8\xd2\xec\xa860\x9b\xce\x8c\xdb"` | 7/24 | `BBBYBBBYYBBBBYBBYYBBYYFBY` | no | `2,10,18,34,46,52,76,84,88,102,118,130,152,156,180` | `26,60,68,110,136,144,162,170,188` | `178; char 23 bit 3` | False | False (44 cells) |
| BL-U-CW | corner dihedral | `;\x99\xa5\x9d9\xad\xbfO\xce\xa6\x16.\xa9\xbaX\x9a\x9e\xc8c\x60\xd9\x8b\x9a&` | 8/24 | `BBYBBBBBBBYYBBYBBBYYFYYBY` | no | `6,18,34,42,50,52,60,64,72,98,110,126,136,140,180` | `26,80,88,118,148,156,170,178,184` | `162; char 21 bit 3` | False | False (44 cells) |

## Center-out Ulam spirals (32 variants)

| Variant | Corner relation | Decode (first 192 bits) | ASCII | Colors | Match | Blue labels | Yellow labels | FEFE label; stream location | Full probable prime | Prime-label bits probable prime |
|---|---|---|---:|---|---|---|---|---|---|---|
| TL-U-CCW | distinct | `\x10f\xd9\x04\xdet\x97eA\xb1\xdc\xfc\xbeVFifw]\x1a\x196\xd6r` | 12/24 | `YFBBBYYBBYYBBBBYBBBYYBBBY` | no | `18,30,34,52,64,82,90,94,108,128,140,146,200,208,216` | `2,40,48,70,78,116,154,162,224` | `16; char 2 bit 8` | False | False (42 cells) |
| TL-U-CW | distinct | `\x014\xdbB\x5c\xf6t\xc6\xc1SgLMO\xa7\xb4\xb4\xc2\xc5\xd7s:s[` | 13/24 | `YBFBYYBBYYBBBYBBBYYBBYBBB` | no | `20,26,46,54,74,82,90,104,118,126,156,162,192,200,208` | `2,32,40,60,68,96,140,148,184` | `22; char 3 bit 6` | False | False (43 cells) |
| TL-R-CCW | distinct | `\x04\x16m\xd2\x13y\xb1\x97eA\x91\x97?/\x95\xa1\x96\x96gu\xd1\x9c\xb9\xb6` | 8/24 | `YFBYBBYYBBYYBBBBYBBBYBYBB` | no | `22,36,40,60,72,92,100,104,118,140,152,158,174,214,222` | `4,30,46,54,78,86,126,166,182` | `20; char 3 bit 4` | False | False (43 cells) |
| TL-R-CW | reverse of BL-R-CCW | `\x04M\xb3\x17=\x90\xc6\xc1St\xb15>\x9f\x9dL,]w3K:s[` | 15/24 | `YBFYYBBYYBBYBBBBYYBBBYBBB` | no | `16,40,44,66,78,94,108,112,120,144,150,162,178,186,194` | `8,26,34,52,60,86,128,136,170` | `18; char 3 bit 2` | False | False (44 cells) |
| TL-D-CCW | reverse of TR-D-CW | `\x01Yf\xe7HM\xc1\xb1\x97eede\xcf\xcb\xdd\x1a\x19ifw6\xd6r` | 13/24 | `YBFYYBBYYBBBYBBBBYYBBBBBY` | no | `10,42,46,68,80,88,102,110,114,122,152,164,172,180,188` | `6,28,36,54,62,96,130,138,196` | `24; char 3 bit 8` | False | False (44 cells) |
| TL-D-CW | distinct | `\x10[4\xcfd%\xc1St\xc6\xd4\xfa~t\xc4\xc5\xd7s4\xb4\xc2\xd6\xd9\xd3` | 10/24 | `YBFYBBYYBBYBBBBYYBBBYBBYB` | no | `12,34,38,58,70,84,98,102,110,132,138,150,172,180,220` | `6,28,44,52,76,116,124,164,212` | `14; char 2 bit 6` | False | False (43 cells) |
| TL-L-CCW | distinct | `@m\x967\x9d!eA\xb1\x97r\xf9Y\x19s\xe7u\xd1\xa1\x96\x966\xd6r` | 12/24 | `YFBBYYBBYYBBBYBBBBYYBBBBY` | no | `14,28,48,56,76,84,98,112,120,128,134,164,186,194,202` | `8,34,42,62,70,106,142,150,210` | `12; char 2 bit 4` | False | False (43 cells) |
| TL-L-CW | distinct | `@3M\xd9\x09s\xd3t\xc6\xc1i\xf9\xd3\x13S\xf73KL,]:s[` | 15/24 | `YFBBBYYBBYYBBBYBBBYYBYBBB` | no | `24,28,32,50,62,88,92,100,114,126,138,168,206,214,222` | `4,38,46,68,76,106,152,160,198` | `10; char 2 bit 2` | False | False (42 cells) |
| TR-U-CCW | distinct | `\x00\xb2\xbaB\xdc\xd8\xcb\x9b\x83#.l\xac\xad\x0c\xb4\xb7\x97\xba3\x973\xb9\xb6` | 6/24 | `YBYBFYYBBYYBBBBYBBBYBYBBB` | no | `17,31,53,61,83,91,99,107,129,137,145,161,191,199,207` | `3,25,39,47,69,77,115,153,169` | `35; char 5 bit 3` | True | False (43 cells) |
| TR-U-CW | distinct | ` b\xea\x066v\xe9b\x60\xec\xce\xa6\x16\xa6\xa6\xe9gNb\xefOkl\xee` | 12/24 | `YYBYYFBBYYBBYBBBBYBYBBBBB` | no | `21,49,53,77,89,105,113,121,125,141,157,165,201,209,217` | `9,13,33,41,61,69,97,133,149` | `45; char 6 bit 5` | False | False (42 cells) |
| TR-R-CCW | distinct | ` #+\xe3\x0bs#K\x9b\x83C+\x9b++9sKy{\xa33\xb9\xb6` | 16/24 | `YYBYBFYYBBYYBBBBBYBBBYBBB` | no | `21,37,61,69,93,101,109,117,125,141,149,157,205,213,221` | `5,13,29,45,53,77,85,133,165` | `41; char 6 bit 1` | False | False (42 cells) |
| TR-R-CW | distinct | `\x00\xae\xa6\x0d\x9d\xa1\xe2\x60\xec\xe9\x18Z\x9a\x9b:\xf4\xe6.\xf4\xf6\x96kl\xee` | 6/24 | `YBYYYFBYYBBYBBBBBYBBBYBBB` | no | `17,43,69,77,95,103,111,119,129,145,153,161,187,195,203` | `7,25,27,35,53,61,87,137,169` | `39; char 5 bit 7` | False | False (43 cells) |
| TR-D-CCW | distinct | `\x08:2\xcd\x8c-\x83#K\x9b\xca\xd0\xca\xe6\xca\xba3\x974\xb7\x97\xed\xad\x9d` | 7/24 | `YYBYYBFYYBBBYBBBYBYBBBBBB` | no | `25,43,69,77,87,103,111,119,137,153,161,169,171,179,219` | `7,17,27,35,53,61,95,129,145` | `47; char 6 bit 7` | False | False (43 cells) |
| TR-D-CW | reverse of TL-D-CCW | `\x02jb\xe7hc\x60\xec\xe9bjjl\xeaab\xefOigNkl\xee` | 17/24 | `YBYYFBYYBBYBBBBYYBBBYBBBB` | reverse | `13,37,61,69,85,93,101,109,133,141,149,165,173,181,189` | `5,21,29,45,53,77,117,125,157` | `33; char 5 bit 1` | False | False (44 cells) |
| TR-L-CCW | reverse of BR-L-CW | `\x02+\xa3760\x9b\x83#K\xb2\xb2\xb42\xb9\xf9{\xa39sK3\xb9\xb6` | 12/24 | `YBYFYYBBYYBBBYBBBBYBYBBBB` | no | `13,49,53,77,89,97,113,121,125,133,149,165,177,185,193` | `9,21,33,41,61,69,105,141,157` | `29; char 4 bit 5` | False | False (44 cells) |
| TR-L-CW | distinct | `\x08&.\xda\x18\xd9\xec\xe9b\x60\xa9\xb3\xa9\x85\xa9\xf4\xf6\x96t\xe6.\xbb\x9b[` | 7/24 | `YYBFBYYBBYYBBBYBBBYBYBBBB` | no | `25,31,53,61,83,91,99,115,129,137,153,169,175,215,223` | `3,17,39,47,69,77,107,145,161` | `27; char 4 bit 3` | False | True (43 cells) |
| BL-U-CCW | distinct | `*\x0d\xcc\xb1\xb8:B\xca\xca\xd8\xcb\xb9{\xa3#.\x7c\xeem\xad\x0c\xb4\xb2r` | 9/24 | `BYFYBYYBBBYBBBYYBBBBBYBBY` | no | `5,33,55,63,71,85,93,101,123,131,139,147,155,177,217` | `11,19,41,49,79,109,117,163,225` | `15; char 2 bit 7` | False | False (43 cells) |
| BL-U-CW | reverse of BR-U-CCW | `\x0a\x89\x9d\x98\xb8;!\x8d\xa9\xa9\xbaX\x98\xbb\xd3\xf3\xa9\x85\xad\xb3\xb9\x9aY\xd3` | 4/24 | `BYYFYYBBYBBBYYBBBBYBBBBYB` | no | `7,47,51,67,75,87,111,119,123,131,147,155,163,175,191` | `11,19,31,39,59,95,103,139,183` | `23; char 3 bit 7` | False | False (44 cells) |
| BL-R-CCW | reverse of TL-R-CW | `\x0a\xc8\xdc\xe8\xc6\xe0\xd8\xc2\xca\xca\xc8\xd2\xee^\xe8\xd0\xca\xe7\xce\xe6\xda\xce\x5c\xd2` | 2/24 | `BYFYYBYYBBBYBBBYYBBBBBBYB` | no | `7,39,63,71,79,95,103,111,135,143,151,159,167,175,191` | `15,23,31,47,55,87,119,127,183` | `19; char 3 bit 3` | False | False (44 cells) |
| BL-R-CW | distinct | `*\x19\xd8\xae\x0e\xc6\x0d\xa9\xa9\xa1\xe2b\xefN\xe9\x18Z\xdb;\x9f:\xf4\xe4\xd2` | 6/24 | `BYFYYBYYBBBYYBBBYBBBBBBBY` | no | `5,41,59,67,75,101,109,117,135,143,151,159,167,177,217` | `15,23,33,49,51,85,93,127,225` | `19; char 3 bit 3` | False | False (43 cells) |
| BL-D-CCW | distinct | `"\xcc\x8d\x83\xa3\x1b\xca\xd8\xc2\xca\xba24\xbb\x97\xed\xad\x0c\xae\x7c\xeeN\x5c\xd2` | 6/24 | `BYYFYYBBYBBYYBBBBBYBBBBYB` | no | `9,45,55,71,79,105,113,121,123,131,147,155,163,189,205` | `11,19,29,37,63,89,97,139,197` | `23; char 3 bit 7` | False | False (43 cells) |
| BL-D-CW | distinct | `(\x9d\x89\x83\xb1\x8b\xa9\xa9\xa1\x8d\x8b\xbd;\xa5\x89\xad\xb3\xb9\xf3\xa9\x85\x9aY\xd3` | 3/24 | `BYFYYBYBBBYYBBBYBBBBBYBYB` | no | `3,35,51,59,67,91,99,107,123,131,139,147,155,203,219` | `11,19,27,43,75,83,115,163,211` | `15; char 2 bit 7` | False | False (42 cells) |
| BL-L-CCW | distinct | `(\xdc\xc8\xee\x0e\x8cJ\xca\xd8\xc2\xe5\xee\x8c\x8d.\xce\xe6\xda\xd0\xca\xe7\xce\x5c\xd2` | 4/24 | `BFYYBYYBBYBBBYYBBBBYBBBYB` | no | `3,27,55,63,79,83,91,115,127,135,143,159,167,203,219` | `15,23,35,43,71,99,107,151,211` | `11; char 2 bit 3` | False | False (42 cells) |
| BL-L-CW | distinct | `"\xd8\x99\xecb\xe0\xa9\xa1\x8d\xa9\xf4\xee\x96&.\xbb\x9f:\x98Z\xdb\x1aY\xd3` | 7/24 | `BFYYBYYBBYBBBYYBBBBYBBBYB` | no | `9,29,51,59,75,89,97,121,127,135,143,159,167,189,205` | `15,23,37,45,67,105,113,151,197` | `11; char 2 bit 3` | False | False (43 cells) |
| BR-U-CCW | reverse of BL-U-CW | `\x06E\x9d\x19\xb0la7\x95\x91\xa5\xd9WF\x86W?/\xdbY\xcb\x9aY\x9d` | 11/24 | `YBYYFYYBBBYBBYYBBBBBBBYBB` | no | `16,56,60,70,86,98,124,132,136,144,146,154,162,178,190` | `12,18,26,40,48,78,108,116,170` | `34; char 5 bit 2` | False | False (44 cells) |
| BR-U-CW | distinct | `\x0c\x15\xcd0l\x1bC\xc4\xd4\xf6t\x8c,]Sg^\x9c\xd6\xdf\xa7\xb4\xb0\xee` | 9/24 | `YYBYYYFBYBBBYYBBBBBBBBBYB` | no | `22,50,68,78,86,114,122,130,140,148,156,158,166,174,218` | `10,20,30,32,40,60,96,104,182` | `46; char 6 bit 6` | False | False (43 cells) |
| BR-R-CCW | distinct | `\x01\xd4Y\xb0f\xc1\x91\xe17\x95\xa1\x89vU\xd1\x9c\xbds\xf2\xfd\xb5\x9aY\x9d` | 7/24 | `YBYYYFYYBBBYBBYBBBBBBBYBB` | no | `20,64,68,78,96,108,126,136,144,148,156,158,166,192,204` | `16,22,30,32,46,54,86,118,184` | `40; char 5 bit 8` | False | False (43 cells) |
| BR-R-CW | distinct | `0\x5c\xd1\x1b\x06\xccD\xd4\xf6C\xb0\xb1uM\xd2i\xcdm\xfa~u\x9d\xcc\xd2` | 10/24 | `YBYYYFYYBBBYYBBBBBBBBBBBY` | no | `18,60,70,74,104,116,128,136,144,146,154,158,166,204,216` | `16,22,26,34,48,52,86,94,224` | `40; char 5 bit 8` | False | False (42 cells) |
| BR-D-CCW | distinct | `\x60\x1dE\x86\xc1\x9b\x15\x91\xe17\xf4hb]\x95[Y\xcb\xd7?/\x9aY\x9d` | 11/24 | `YYBYYYFBYBBYYBBBBBBBBBYBB` | no | `24,54,72,76,106,118,122,130,138,148,156,160,168,206,218` | `10,20,28,36,38,62,88,96,198` | `46; char 6 bit 6` | False | False (42 cells) |
| BR-D-CW | distinct | `@\xcd\x15\xc1\xb3\x06\xd4\xf6C\xc4\xc5\xd57H\xc2\xd6\xdf\xa7\xe7^\x9c\x9d\xcc\xd2` | 5/24 | `YBYYFYYBBBYYBBYBBBBBBBBBY` | no | `14,52,62,66,94,106,124,132,134,142,146,154,164,190,202` | `12,18,28,42,44,76,84,116,210` | `34; char 5 bit 2` | False | False (43 cells) |
| BR-L-CCW | distinct | `\x18Y\xd4l\x1b\x067\x95\x91\xe1e]\x1a\x18\x97r\xfd\xb5\x9c\xbds\xe7p\xd2` | 8/24 | `BYYFYYYBBYBBYYBBBBBBBBBYB` | no | `12,52,62,80,88,116,124,132,134,142,150,160,168,176,220` | `14,24,34,42,44,70,98,106,212` | `28; char 4 bit 4` | False | False (43 cells) |
| BR-L-CW | reverse of TR-L-CCW | `\x03Q\x5c\xec\xc1\xb0vC\xc4\xd4\xd4\xdd#\x0b\x17z~u\xe9\xcdm\x9d\xcc\xd2` | 9/24 | `BYYFYYYBBYBBBYYBBBBBBBBBY` | no | `10,54,58,76,84,96,122,130,134,142,152,160,168,176,188` | `14,24,36,38,46,68,106,114,196` | `28; char 4 bit 4` | False | False (44 cells) |

## Reproduction

```bash
python3 tools/gsmg/first_piece_spiral_variant_comparison.py --self-test
python3 tools/gsmg/first_piece_spiral_variant_comparison.py
```
