# Cosmic Duality row/column base64-decode ASCII dump

Non-printable bytes (outside 0x20-0x7e) are shown as `.`. See
tools/gsmg/FINDINGS.md Phase 143 for the tested/closed verdict on both axes.

## 28 rows (each independently base64-decoded; identical to the real
ciphertext chunked into 48-byte pieces -- row 0 is the true Salted__ header)

```text
row  0  z=  4.05  Salted__-?o.m.P..Y.>,..wk..w.|k'...(a.Y+B^pt..1^
row  1  z= -1.30  tba."H?..F...................q.c...........RY..b
row  2  z= -0.11  s..$...v..p..].m.F_`T.....`.{(i.q..M.M.....h....
row  3  z=  0.19  H........3>....L...0..I.AFk@._l..D...^UI.Y..E.C.
row  4  z= -0.71  #)....@{............../....,.N8..`i....lRTj.`.B.
row  5  z=  1.37  .&q. i....<Nj....N.]6.A..LEu..}.n.:..#l.W.C.i...
row  6  z=  0.19  ..b.){....j.D0.....l....T...H...P~V#s4...=....y(
row  7  z=  0.48  .....Qbz..>=R.....Q.{..&.K.j...-....D`3.t....D'~
row  8  z=  1.67  ....9N.8c\0.H.(_c>...hD(V..VB*F..6.f......$..KS.
row  9  z=  0.78  R:..o...<!..O.....(.{ ....d=..P.>.rq...b..Kb].J#
row 10  z=  1.67  &m.$G.]..../G8....6Rt.4Y52o.G.....F.o.$P{...Z.l.
row 11  z=  0.78  .....S". ....O..|.&!_K4`.nt....j.h.e.$.==....?.4
row 12  z= -0.41  ....,..|W:...y...K..1y...K...._E..m......x=.tmu.
row 13  z= -0.41  ..K.4....f/...:......T.).../H..v....H..<l.z.._.g
row 14  z=  1.08  ;}...._..U....t6....a<$t..F..49..O.Tu.....Oak.;?
row 15  z= -0.71  .......S.........na...L.b(D.. r..}.W..$h....:%..
row 16  z=  0.19  .....'.y..pB...m.3...-..C./..C1..F.Z.ph.E..s.o..
row 17  z=  0.48  lOS..wq.O.. U. .CD..L7...8]J........*.U...JE....
row 18  z= -0.41  0j;..O..7yGK...K.....~...e..6.....9<.....%.3....
row 19  z= -0.41  *6.R.e.%....x.f_.88k..........b_2.O.. ..J.......
row 20  z=  1.08  d.....Hi...q.<...5zi.5.<4X..O.....S...,...sLy:\.
row 21  z= -0.71  ...OLB....q.D....2.~.W. ...+............,..<XI.e
row 22  z= -0.41  ..h.N)j.|...*.S}vhb.....\...........w."...)..}q.
row 23  z= -0.71  ...D..6}..G..`.Y.(.#.F9........r=.< ..A\........
row 24  z= -0.11  oy...rt.{..l.G...[.>.i..........@*+..^..+eL...'.
row 25  z= -0.11  ..8..t..jO).CO@...r.A...Y......\...}......c..ne,
row 26  z=  0.78  ..z.p)..R.{......hAG'...J@Q.a..g.p'.E..9.}}....8
row 27  z=  0.48  .4X.i...mz..\4c......0$...}...*.[..6i....-...?o.
```

## 64 columns (each independently base64-decoded; vertical read across
the 28 lines at a fixed character position)

```text
col  0  z=  1.78  Q..#`d.BG......g[*nM.
col  1  z= -0.02  .n..#.f9.n..lA.9.....
col  2  z= -1.81  .........I]......V..Q
col  3  z= -1.36  ........s..m.>..*(...
col  4  z=  0.43  w.E.....A..f.~..;Q..k
col  5  z=  0.88  .#..(.La..8l>.i.E....
col  6  z=  0.43  T....m....1.R.E/..G.'
col  7  z=  0.88  ......9F..}c.s.0*e.Js
col  8  z= -0.47  \..@..........,JF.v..
col  9  z= -0.92  .....gO.a..5......$..
col 10  z= -1.81  ................)vT.A
col 11  z= -0.02  ...Q.*.. _a.t........
col 12  z=  0.43  =...a,\..9.l....:..9^
col 13  z= -0.02  ....9.....'*...0z.{).
col 14  z= -0.02  .p.....$......Fdp.&{$
col 15  z=  0.43  ..]..}.+...[....m!...
col 16  z= -0.92  n....TI4~....X.......
col 17  z= -0.02  s.j........pm.J..6.HC
col 18  z= -0.92  ....`..x...C..%..C...
col 19  z= -0.92  A3D........>..f.....c
col 20  z= -0.47  ....[.^.$.#Bn...W....
col 21  z=  0.43  ...w.....3.heO;d%...:
col 22  z=  0.88  6.n.Y.3..%..0..c.@.pr
col 23  z=  1.78  d..8....H/`..F..*(lJ/
col 24  z= -0.47  .5..)...I......{.%..!
col 25  z= -0.92  ....U.0.b.......z....
col 26  z= -0.47  ..@.L%..Ec.v..n......
col 27  z= -1.81  ....d{.....I...I.....
col 28  z=  0.43  ......h.RyS.,..5\.k..
col 29  z= -0.02  ..D.CP...h..g.\w..s..
col 30  z=  0.43  T.&.w.A.Q.Ds..>......
col 31  z= -0.47  .'..J..&`B...5.......
col 32  z=  1.33  h'...tW._..X@MD5...d.
col 33  z= -0.47  ..T)C......b.1...K..:
col 34  z= -0.47  ..Y....Ry..a....... e
col 35  z= -0.92  P.+.R..K......6.....}
col 36  z=  0.43  t~.-.ZT....7.....E.k.
col 37  z= -0.92  ...5.-....N.&..S..h..
col 38  z= -0.02  &.-v..#g.>5.......K..
col 39  z= -1.36  ...9....... .D/W.....
col 40  z=  1.78  j&.9..EA.^..2X..1..;.
col 41  z= -0.02  .gI-....F.w.@.e....Q.
col 42  z=  0.88  p.l.^w|G(].....#...7.
col 43  z= -0.47  ..T....... *.b2..}...
col 44  z= -0.02  ...b..7.....Di....(g/
col 45  z= -1.81  ....9m.}.......W.....
col 46  z=  0.88  2.S..2....~Yv)?3o....
col 47  z= -0.02  ..V.X...%...j..c..K.v
col 48  z= -0.02  b...G..F..'j....gz..Z
col 49  z=  0.43  |..G,.}....1..R).M..^
col 50  z= -1.36  .m.............2.1.|6
col 51  z=  0.88  gf.....Y.YH$.Wm.8...R
col 52  z= -1.36  +..o..........=.!..3.
col 53  z= -0.92  ....Z.....c.S..*&....
col 54  z=  1.78  $..%.._.6.=?Z.(.5#.8D
col 55  z= -0.02  z'.RoT........\.!...m
col 56  z=  0.88  r..i..%+6=.../br..M..
col 57  z=  0.88  .U..../l=f..^H..7x#..
col 58  z=  0.43  L....:<.C..h9c....`5.
col 59  z= -1.81  .....c...... .....k..
col 60  z= -0.02  ......Jn.mq.n..9'....
col 61  z= -1.36  L......E._....1....k.
col 62  z=  0.43  .../..>..X.8[....$}L?
col 63  z=  1.33  z ...>n8tf.....BTQf..
```
