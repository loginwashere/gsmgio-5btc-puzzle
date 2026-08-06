V={c:i+1 for i,c in enumerate("abcdefghi")}
G="00110b0010110y 11b1001110b011 1101110b001001 0110b000011101 0b1000110y0110 100110y010y011 100b1100010y00 b11000000010y0 00011b0111110b 11b111y0110001 1101000y011011 11110010b01100 0b0111010y0110 01b0110110b011".split()
A="dbbibfbhccbegbihabebeihbeggegebebbgehhebhhfbabfdhbeffcdbbfcccgbfbeeggecbedcibfbffgigbeeeabe"
B="faedggeedfcbdabhhggcadcfeddgfdgbgigaaedggiafaecghggcdaihehahbahigceifgbfgefgaifabifagaegeacgbbeagfggeeggafbacgfcdbeiffaafcidahgdeefghhcggaegdebhhegeghcegadfbdiagefcicggifdcgaaggfbigaicfbhecaecbceiaicebgbgiecdeggfgegaedggfiiciiififhggcgfgdcdggefcbeeigefibgibggghhfbcgifdehedfdagicdbhicgaiedaehahghhcihdghfhbiicecbiichihiiigiddgehhdfdchcbafgfbhaheagegecafehgcfggggcagfhhghbaihidiehhfdeggdgcihggggghadahigigbgecgedfcdggaccdehiicigfbffhggaeidbbeibbeiifdgfdhieeeieeecifdgdahdiggfhegfiaffiggbcbcehceabfbedbiibfbfdedeehgigfaaiggagbeiichiedifbehgbccahhbiibibbibdcbahaidhfahiihic"
P=lambda n:n>1 and all(n%d for d in range(2,int(n**.5)+1))
pos=lambda ch:[(r+1,c+1,r*14+c+1) for r,row in enumerate(G) for c,x in enumerate(row) if x==ch]
blue=[p for *_,p in pos("b")]; yellow=[p for *_,p in pos("y")]
mod=lambda xs,m:{(x-1)%m+1 for x in xs}
def key(z=set()):
    M=[[0]*14 for _ in range(14)]; k=0
    for i in range(14):
        for j in range(i+1,14):
            M[i][j]=M[j][i]=0 if tuple(sorted((i+1,j+1))) in z else V[A[k]]; k+=1
    return [sum(r) for r in M]
def rows(z=lambda r,c,ch:0):
    return [sum(0 if z(i//15+1,i%15+1,ch) else V[ch] for i,ch in enumerate(B[j:j+15],j)) for j in range(0,len(B),15)]
dec=lambda R,K:''.join(chr(((R[i]^K[i%14])%26)+65) for i in range(38))

S=dec(rows(),key())
L=dec(rows(lambda r,c,ch:r in mod(blue,38) and c in mod(yellow,15) and ch in ''.join("abcdefghi"[i-1] for i in mod([p for p in blue if P(p)],9))),key())
H=dec(rows(),key({tuple(sorted((r,c))) for r,c,_ in pos("y")}))

print(S,L,H,sep="\n")