# All tracked GSMG blobs, decoded to hex

Companion to `tools/gsmg/cosmic_row_col_ascii_dump.md`. Every entry below is
the whole-blob base64 decode (concatenated first, per the same rule
confirmed for Cosmic Duality in `FINDINGS.md` Phase 143 -- there is no
per-row/per-column ambiguity for any of these, they are single continuous
base64 strings in `data.py`, not line-wrapped textareas).

All five decode cleanly to the OpenSSL `Salted__` + 8-byte-salt + AES-CBC
(block-aligned) format. `SALPHASEION`/`P32_TRAILING`/`URLBLOB`/`COSMIC` are
the four still-unsolved targets `cb_common.py` sweeps by default (URLBLOB is
quarantined, tested separately -- see `data.py` provenance comments).
`PHASE32_BLOB_B64` is included for contrast only: it is the one **already
publicly solved** blob (password = `SHA256("jacquefrescogiveitjustonesecond
heisenbergsuncertaintyprinciple")`), kept as this project's real
known-plaintext ground truth for the decrypt pipeline.

## SALPHASEION_BLOB_B64

- 96 bytes total, salt `3ab585348552415d`, 80-byte ciphertext (5 AES blocks)

```text
53616c7465645f5f3ab585348552415d75270543bb0b4f97e0a5169d6902be8652c5b443df036c19654779fbddaddf7342f5f4b7cbf78cf078a24a6ca7179b462eac13504c9791c8f1192ef8a7a352a4ef756397ea74234a97a95f01ae37f8c9
```

ASCII (non-printable bytes shown as `.`):

```text
Salted__:..4.RA]u'.C..O.....i...R..C..l.eGy....sB.......x.Jl...F...PL.........R..uc..t#J.._..7..
```

## P32_TRAILING_BLOB_B64

- 96 bytes total, salt `b45a5e3d827593ca`, 80-byte ciphertext (5 AES blocks)

```text
53616c7465645f5fb45a5e3d827593ca28a696ebbb577faf97bb2dd2052df6c583ccd2f10e694f32c0d28ae5b66b8eb380a9488bc69aa98e60a493cf1335b59fd9f7ff6eaab38cecb56b4f285f19b3f05334de08884878aaed7c99d0b4340bf8
```

ASCII (non-printable bytes shown as `.`):

```text
Salted__.Z^=.u..(....W....-..-.......iO2.....k....H.....`....5.....n.....kO(_...S4...Hx..|...4..
```

## URLBLOB_B64 (quarantined -- no README/solved-plaintext corroboration)

- 112 bytes total, salt `74c974e3f92e64b5`, 96-byte ciphertext (6 AES blocks)

```text
53616c7465645f5f74c974e3f92e64b59f7ea22a50dcb0d4289d176d4ce9dba7f99a695b8d0797b5c7791e65a8d2b68a5879f5d31ae5e8a2635205de31b851cf43b2534f58765696d3c2a01f7f3a41f7284fbbcc836517cbf7ba613c43a919d9dc669e4824baba6a5caeb77dfc3e0607
```

ASCII (non-printable bytes shown as `.`):

```text
Salted__t.t...d..~.*P...(..mL.....i[.....y.e....Xy......cR..1.Q.C.SOXvV......:A.(O...e....a<C....f.H$..j\..}.>..
```

## COSMIC_BLOB_B64

- 1344 bytes total, salt `2d3f6fe06dc950e6`, 1328-byte ciphertext (83 AES blocks)

```text
53616c7465645f5f2d3f6fe06dc950e6d359b83e2c8685776b1b9477c27c6b270608032861f8592b425e7074c3a5315e746261e122483faeaa46d5efa3b3d3a6fb088f03bca6b2e20bfb0d1ed87188632ea88acaa0edb6e2b3a2b0525980046273b3da24f9dee2769bf17085b95dcd6dfc465f60548cd91e7f9860ee7b2869d671d3c74dc94d9be9e89c896894beeec34804d214eec8141880333edd0ea2044cab8695300fe0498c41466b40db5f6c9b144404d6e95e5549bb590794459343be2329a1b2dceb407b14d01ba08efda79dd98e1210b11a2fe5a8adab2cd74e38bbad6069c0e910c36c52546adb608042e1d92671f9206909d6d21a3c4e6a9dbb97d14eca5d36af41d4e94c4575cb1b7d9d6eb53a9513236cf757a6431b6982dfba04f662b2297be09bf8126ae94430b7b9f9e4996c11f0d7ea54f20a8548860eee507e56237334fa0eb03dbcb419bb792893efd9babb51627aaab23e3d521c0417d19f51f97bb90626d14ba76ad5b8dc2dd9d6dc85446033007414152ea344277ebd91b2a1394eb138635c30c2480c285f633ec8cfa868442856f0f056422a4617c336e06611f8be1e95ee24b3c14b53db523ae0a06fd4bfba3c21ec924f81c1bfcfb928bc7b20a412f1fd643d9d9850c13ef17271d1c68562cf894b625d9b4a23266dc92447185dd284cce42f4738b893ee9d365274e5345935326f9f47cf1b970cf346906ff724507b0bb30f5ae16ce11ecaf3050453221a20f6c4e6fa4f8b917cc826215f4b34607f6e74a5bbe2146a10688165d424d03d3db0dbd0cb3fdd34e9b4a2962cb0c27c573a8af4dc79feecc24bdbb63179a1909f4b051a03f95f45f88e6def101916bed1783d99746d75992ef54bff34e7f3bfb6662feeecb03acba6f6caded854c92985e78e2f48daa576a201fddb48f7943c6cff7aef195ff3673b7db9f611b55f0a0455c19d0c1574361d00e3fa613c2474c79046d3853439e5804ffe5475cfe018cd134f616b133b3f0092ad9ac9e3df5392b2a59bf700fe0a876e618d89ae4cc9622844dd972072faaa7df657ab1424688ffcdeba3a259e0fb9b9a5d0f52702791d9a7042a5b0a56d93339a8dc42d9d04430b2f9091433109a246175ae27068a145bbcd73886fb5b16c4f531ebb7771d64fe6e02055f820b94344e1f64c37c01310385d4ac2e49497b61af8a12ae65503abae4a4580b0aeae306a3beb1a4fc18b3779474b8ed00d4bcddaebf17f7e1917d465ecef36d08e1f889f393c8e111d128825f633ecfe80e32a36e4529165b025b00191a878a9665fb738386b83e5cf85107fb69d81ef625f32d44fcae520edf54a1c8a8f17bb16c364ece1c3b2cc486903d4c671a43cec0996357a691235df3c3458fef54f15b2c2030d5318c0a32c1ca7e3734c793a5cd0d5fe924f4c42930c9d0c71c644a2b1142e32e87e9f57db207fd38f2bfeb9cfde11c7bdbe99fbd3ca2cd2863c58491a65b07f68b54e296ab97cae80f42ac5537d766862b617ccae9c5c19f504efce12a5a5bbef8377d32219a50629ddb67d7111a8d5a84402a5367d9be847a10f60fc59a0289623d4463901d0b6ff1693fdba723ddd3c20e8dc415c08fbdf89dcb6e9116f7904d3c47274957bd1e26cbc47ed17985b103e0769c1b1f69ce2b1a4b3eadf402a2b92a05eaea02b654c861ab727d9910038c20e7484026a4f29ce434f40ad11c4721b41ffbbaf599481189efece5cd118ac7df4fde80d90fe6390fc6e652cdcf57a167029f88452967b10ea10a193006841472781c7c64a4051be61a3b067ab7027ad451c0139f87d7db5f6aeec389b3458ac69f3f5e06d7a99095c34630facaf84d7d03024a49ba97dccc5b12af15bbf983669ed922eb12dff1dcc3f6fc6
```

ASCII (non-printable bytes shown as `.`; also available split by row/column
with statistical scoring in `tools/gsmg/cosmic_row_col_ascii_dump.md`):

```text
Salted__-?o.m.P..Y.>,..wk..w.|k'...(a.Y+B^pt..1^tba."H?..F...................q.c...........RY..bs..$...v..p..].m.F_`T.....`.{(i.q..M.M.....h....H........3>....L...0..I.AFk@._l..D...^UI.Y..E.C.#)....@{............../....,.N8..`i....lRTj.`.B..&q. i....<Nj....N.]6.A..LEu..}.n.:..#l.W.C.i.....b.){....j.D0.....l....T...H...P~V#s4...=....y(.....Qbz..>=R.....Q.{..&.K.j...-....D`3.t....D'~....9N.8c\0.H.(_c>...hD(V..VB*F..6.f......$..KS.R:..o...<!..O.....(.{ ....d=..P.>.rq...b..Kb].J#&m.$G.]..../G8....6Rt.4Y52o.G.....F.o.$P{...Z.l......S". ....O..|.&!_K4`.nt....j.h.e.$.==....?.4....,..|W:...y...K..1y...K...._E..m......x=.tmu...K.4....f/...:......T.).../H..v....H..<l.z.._.g;}...._..U....t6....a<$t..F..49..O.Tu.....Oak.;?.......S.........na...L.b(D.. r..}.W..$h....:%.......'.y..pB...m.3...-..C./..C1..F.Z.ph.E..s.o..lOS..wq.O.. U. .CD..L7...8]J........*.U...JE....0j;..O..7yGK...K.....~...e..6.....9<.....%.3....*6.R.e.%....x.f_.88k..........b_2.O.. ..J.......d.....Hi...q.<...5zi.5.<4X..O.....S...,...sLy:\....OLB....q.D....2.~.W. ...+............,..<XI.e..h.N)j.|...*.S}vhb.....\...........w."...)..}q....D..6}..G..`.Y.(.#.F9........r=.< ..A\........oy...rt.{..l.G...[.>.i..........@*+..^..+eL...'...8..t..jO).CO@...r.A...Y......\...}......c..ne,..z.p)..R.{......hAG'...J@Q.a..g.p'.E..9.}}....8.4X.i...mz..\4c......0$...}...*.[..6i....-...?o.
```

## PHASE32_BLOB_B64 (known-solved, ground truth -- not a live target)

- 2448 bytes total, salt `eefc4c5befc1656a`, 2432-byte ciphertext (152 AES blocks)
- password: `SHA256("jacquefrescogiveitjustonesecondheisenbergsuncertaintyprinciple")`
- plaintext prefix: `"I've been waiting for you. You have many questions,"`

```text
53616c7465645f5feefc4c5befc1656a1d1833bc8c57346282eff930a779306fddd589dcbf730895348c3c597a899b530f1ec92516d9619c26d7c2fd5d9da4dfeaa6ee03719a0ef36e0e10cfcae051efc4dd2e785ae0ccc7129c83bade7db8f653eba9b0b27bc01999935287c53d0ccd7bfbb5eb9bec6b8eab209d0a13ddd5d4527176b7395937a105a915cea73e604c335c01076878d5e69073d8f4a78b295bedcf374cdb8391c697cfb8e0abcc1e178d0d6bf0edd4b5f0d4cc2a75c8c78d99d91c0066f4cbc48d8bb31d1188621cc59cc248ede47594b43c2c8f94a49106b7532ed4961cbbccf8f81d4d70162affaeb7e18a6bc62b3d831e4eff6fda71ba4f083ff0e1513665c8dbd445396e731241fb673019d779486a233afdfe03cca6e4270932f6780838e75cb0f493a31ff116ffe307a65833a125a82b3e80a4a8d4bc2cbcf7b1728d7c56f7e07cee2f2e65816753dd82efe7528426ef55e6cc24e3523ca21fd7197fee22aa38c03e5feafe93f1f5320f99e8d60d3422fd3c37c2dbf65291badb53945912257bd6014a38485483d7a5b162529115f39022890e9574dd39f96702072679c0840114f0e7463792db80973d12a65567cb9af5db4770c4fc80a2070f21f67dfadfa3c849c3b536fd69507089bc24a3c49380365d355c0101ef0ace9669f9a7c9922d943b274c4e9413ef7f9764e93fab61138c979acaaddfa2d105d3f76cb73de9797010d0940d8312adb2aada8ac5119a14990d4b6bbc70a236341b24a30a3e69e64d83a7e92c1f4dd76744280586875f178f9236614b2f97dcf179b75d8d26c508cf4f27c149c04291a24ea397e266ef7db2d86abc3ae0071a4d08154144fd61360bb1a92dd1e733da4ddc8fabf8e4d870c67f5452a1323aa48d459be73aae5a3f07498c2c46bb4f6e78dab9ca96e08e64c8146fbe2e36603ea0bb4c58e8295c90da0a398c87e6595143b13dfab80eb31ac0245dc96c789998b83b67f616664c2f0a7c04751f716373d4ca31334f92bf0f6a9861c32d82c52061f443f56f59e356dc30e241293dcf35dc4e030132156a4dee11ad45577d0023f2cf676365813b162d8bcd5be5461d558927644227e2c2b5cef568eb68d5745e2c498228c6af32983cafef697c68f20ecb6e85e2e3f8292cddc6cce41fe3d8378a37e2d8c9e0e532faa94c06e238e85586bf755d8e7ee08866e8024569204b39aa67f4349b0b5b40d71b5451bfd1db3408387c5bc394738bfae15f07152c785c28c3a361e2e435310464e39c629592677cd36b3b5318db34edf84b36b8c70276e22db772ae42136c102a1885abc12a95b46a8f37efa47357c5d47ab15c3b96b24d8fc27e53b5616f5e8d454ac6a418c2536c34891172ac34eb72d557b00c190460ec9a8efb8c912f96aced663fa6304b3c940f34edea3c03c9674d14c9ccb31b1e7a9b25b3707d27cd8ea279dabed5aa1e9d37a32e77413d230ee86ca9bc23371a4c282113a2ea77920c632f59fcd5f9a921b82a1a8ce190ac9421fd1887115b464e2193a8a6fe46a2e939dc0dc4a43524c82fd64ae91ea316ea9087d27608bf227d929e9ed29efa05d1656365ccab9ec1dc49ea1124401e8920502144cb715dac1e27d03053823f308c63de9591c8dabf7f2ac7cb4589171cedc6f8644dbc1e8aa704f992b57216e226f763cf85e70296f209844026f8827c0bfc2f6ce53e387631b2fbbd20e5cd35183a7244e40958f5c056831a20516475b6b4d18d26350ae5f601689cb7217a89d82ae32d4b0114d7c00c4f473bf824426f648ada0c21876b22b40f55f13e63c801925dcd2d219195aca6f420803719f29b61f20b74a81493b0b91fd0d5b2e70037cfef83f5634cda06a4c3efd8051f9adbe3a858c894d05a9b53839f6e827e3d366c92fbafe0786aa89df2c8061c7f5d5711501e19d499e83448d8d00c4af75acf74649edb710d487ab6ead01c689dabb660d650ff755f9d0f539462719b0f51351a00eb4567f6b058d6a6c6f543d50097b9547a1e8dd763f62deb3f5359f4b55e357d335316d5b060aded38a10d519646b309a29be5cb0cd150cca5ec24dd46ee87560de5ee915205be6a9aafc7dece8a82df4e3ae601e0e8f2d4d9d1f46351f220a759ef9e5e73cc839a3479d7bfcebe7bd2fafddff8a83a84f7b4204394163c83a27faa2aafa22c5593c241557850ae3038d10ae2b507aef63cc7a8dd05fc598b30a9ca55c55dbd93963dfc3f0d6fe36a26a38b772c290c626b65a2827bc39fcdc8bf5e53ae275c20710b3d48a07f0f27e31cdb8ab8046375619525e6b1093c8caa5a10d247961099c58854280c4e66064fdd52d7cf718e421632267bfb3147b1b9254a7336c3f9a6fcb948375bb9eaa2a2add361ef8ca8c501841a219520bd7d1cdc463bef7785a544ceec2dbca2418d3945c21c97d0bdcd46be229403911feb169de4043347ed1479392e89ec7f3683c1fe8b959203517946a99ef76087e9220ceb30e4ff03f7359cbb2598a0376d59e922e68da589cfe1c3e7f1d45d852f7e896268f92285de70ca75baaec13bcc7b999e4b44e6592a8acc90be0795441e82593ac1d638fe6b1924bf5d3a4a1a091e2b222f5e1144251fca13a4e8e0cbba8c078a82524084a8d772aec6afc3b7a091bfd2de01967c13cbe04d9362b909c8b3cd01f90d02adee72e5076670d6f81b6fdbd81ec68273e834df0e4044f27a465c9ceb25879671024e8acd16adeda929a1bd232a0805bb07a4e289dd5d71a9420e3569925650a255d782d3c05f7ba37da8faf82364a1dea6b31930964bd7b04effaf0ee677a18edeb19f1e1cd10710bc46524b1f983a4031f8c8b9da81f1bb21960b40c3e532d9eb2ceabb45eeed5b45528069509d975fdcba5d61841f134bc01a6ed80870d453f55d52cecd254363e076836188e28dbaca74f9337a2a0ad662b634104a1c10a44bbb1ad142932b1be2d9dde4f0ed91b44dcb7fc86bbf180bb3bc75c4b2cefd56b6a6e34c2e03e2ba586e854d2b60241a56c2d461eff2c4b97a4a6a79d0a4947c8bb0dbd12bb4e688098d43fc53277944a3f1a1057ab545a4658e6a06ae3b68be8cd71bffee07e46ad012c1db6cf157c6d75ca76f2fb17e19192455d4313aaf40e730931ee05440f6c115b29ae3ff1f4c825a88330fefab904f932542bd8558ebd856c737ccd1b5b929630c51967eec3defdda874ef328468e2be4826c69799a01080473b741c0d37b3de44ecc8bb05c0f15f8c7bbecfba951b0353875712c7aadd85794a4c4fee947ad795b72c90227278efc42697b1df878cccaf43b8046dc863214437daf288ca17602a20b2313d70dbacf61952adc035346c88978abf6cf946094ea868550308172fcf2759c9cfcf58a717680d4036f4ff43bacc8b9f311f24d2e41ff7ae3a50f151aafba00c45de1511e5e2b5ec1b075e8bf023cd
```

ASCII (non-printable bytes shown as `.`) -- shown here only for consistency;
this is the already-solved blob, its real plaintext is `PHASE32_PLAINTEXT_PREFIX`
in `data.py`, not this raw ciphertext's byte pattern:

```text
Salted__..L[..ej..3..W4b...0.y0o.....s..4.<Yz..S...%..a.&...].......q...n.....Q....xZ........}..S....{....R..=..{.....k.. ......Rqv.9Y7......>`L3\..hx...s....)[..7L..............k.......*u.......f.........b....H..u..<,......S.........Mp.*.....k.+=..N.o.q.O.?..Q6e...E9ns.A.g0..yHj#:......'.2.x.8.\...........X3.%.+>.....,...r.|V..|./.e.gS....R.&.U..$.R<......".8.>_.....2.....4".<7...R...S.Y.%{..J8HT....bR...."...t.9.g..&y......F7....=..Ug....Gp......!.}....I..6.iPp..$....6]5\......i....-.;'LN.....d.?.a............l.=.yp.................Kk.p.64.$..>i.M...,.M.gD(..._...6aK/...y.].&...O'.I.B..N...f.}..j.:...M..AD.a6...-..3.M......p..TR.2:..E..:.Z?.I.,F.Onx......d..o..6`>..LX.)\...9...YQC.=......$].lx...;g..fL/.|.u.qcs..13O...j.a.-.. a.C.oY.V.0.A)=.5.N..2.jM...EW}.#..gce.;.-..[.F.U.'dB'.....h.h.t^,I.(..2.<..i|h...n....),.......7.7.....2..L..8.U..u].~..f..Ei K9.g.4..[@..TQ...4.8|[..s..._..,x\(..a..51.d..b..g|.k;S..4..K6...v.-.r.B.l.*....*..j.7..sW..z.\;..M..~S.ao^.EJ....Sl4..r.4.r.W....`....../...f?.0K<..4..<..gM......z.%.p}'...y......7..wA=#..l..#7.L(!...w..c/Y....!.*......!....[FN!....F..9....5$./.J........v.."}........ece.....I..$@.. P!D.q]..'.0S.?0.c.......*..E......dM........r..&.c........@&..|../l.>8v1... ..5.:rD..X..V.. Qdu....&5....h..!z..*.-K.....OG;.$Bod...!.k"..U.>c...].-!..... .7...a..t...........7....cL............X...Z.S..n.~=6l....xj.......]W.P.....4H...J.Z.td..q.Hz....h...`.P.u_..S.bq..Q5...Eg..X....C....Tz...c.-.?SY..^5}3S...`..8..Q.F........P...$.F..V....R..j........N:.........cQ. .Y..^s...4y....{......:... C..<....*..,U..AUxP.08.......<.....Y.0..U.]...=.?.o.j&..w,).bke..{.....^S.'\ q.=H...'......cua.%...<..Z..G.....T(.Nf.O.R..q.B.2&{.1G..%Js6.....H7[......a.......!. .}..F;.w..D..-..A.9E......F.".........3G..y9....6.......QyF...`.."..0....5..%..7mY."..........]./~.bh."..p.u...;.{..KD.Y*......D..Y:..8.k.$.]:J...+"/^.D%............R@...r............|...M.b...........r..fp...o.....s.4..@D.zF\..%..q.N......)..#*........]q.B.5i.VP.U...._{.}...#d.....0.K..N....w...........FRK..:@1.......!..@..2..,..E..[ER.iP.._..]a...K..n..p.S.]R..%Cc.v.a.....t.3z*..b.4.J...K...B.+.........M...k.....u....V...L....Xn.M+`$.V..a....zJjy...|....+.....C.S'yD....z.E.e.j..;h........j....l.W..\.o/.~..$U.1:.@.0...T@........L.Z.3....O.%B..X..V.7....)c.Q.~.=...t.2.h..H&......G;t..7..D......_.{......S.W.....yJLO..z...,."rx..&.......C..m.c!D7.....`* .1=p....R..54l....l.F.N.hU.../.'Y...X..h.@6..C....1.$.....:P.Q....E.........^..#.
```

## DBBI and FAED -- structurally different, not base64

These are the two undecoded strings from the SalPhaseIon page's 9-symbol
(`a`-`i`) alphabet, not base64-encoded AES blobs. There is no plain
base64-to-hex decode for them; they go through the checkerboard/keyed
-columnar pipeline in `cb_common.py` (`decode_9ary`, `chain_add`,
`autokey_dechain_9ary`, etc.) to first reduce them to a candidate
alphabet/passphrase, which is then tried against the blobs above.

- `DBBI`: 91 symbols, IoC 0.151 (structured / key-like)
- `FAED`: 570 symbols, IoC 0.118 (~uniform / high-entropy payload)

```text
dbbibfbhccbegbihabebeihbeggegebebbgehhebhhfbabfdhbeffcdbbfcccgbfbeeggecbedcibfbffgigbeeeabe
```

```text
faedggeedfcbdabhhggcadcfeddgfdgbgigaaedggiafaecghggcdaihehahbahigceifgbfgefgaifabifagaegeacgbbeagfggeeggafbacgfcdbeiffaafcidahgdeefghhcggaegdebhhegeghcegadfbdiagefcicggifdcgaaggfbigaicfbhecaecbceiaicebgbgiecdeggfgegaedggfiiciiififhggcgfgdcdggefcbeeigefibgibggghhfbcgifdehedfdagicdbhicgaiedaehahghhcihdghfhbiicecbiichihiiigiddgehhdfdchcbafgfbhaheagegecafehgcfggggcagfhhghbaihidiehhfdeggdgcihggggghadahigigbgecgedfcdggaccdehiicigfbffhggaeidbbeibbeiifdgfdhieeeieeecifdgdahdiggfhegfiaffiggbcbcehceabfbedbiibfbfdedeehgigfaaiggagbeiichiedifbehgbccahhbiibibbibdcbahaidhfahiihic
```
