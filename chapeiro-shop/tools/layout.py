# sheet -> list of (code, x0, x1, y0, y1) shirt-pair regions; split at midpoint into A/B
def grid(xs, ys, codes):
    out=[]; i=0
    for c in codes: out.append(c)
    return out
L={}
# row-major numbering (left,right per row)
def rowmajor(prefix,start,colx,rows):
    r=[];n=start
    for (y0,y1) in rows:
        for (x0,x1) in colx:
            r.append((f"{prefix}{n:02d}",x0,x1,y0,y1)); n+=1
    return r
def colmajor(prefix,start,colx,rows):
    r=[];n=start
    for (x0,x1) in colx:
        for (y0,y1) in rows:
            r.append((f"{prefix}{n:02d}",x0,x1,y0,y1)); n+=1
    return r
L['p1']=rowmajor('P',1,[(18,512),(522,1012)],[(140,362),(392,612),(652,892),(922,1146),(1188,1442)])
L['b1']=rowmajor('B',1,[(105,510),(622,1016)],[(150,388),(425,664),(700,938),(965,1198),(1235,1462)])
L['a1']=rowmajor('A',1,[(128,512),(636,1022)],[(140,365),(375,628),(640,882),(892,1138),(1148,1452)])
L['p2']=colmajor('P',11,[(122,516),(628,1016)],[(183,402),(420,652),(672,908),(922,1162),(1182,1442)])
L['a2']=colmajor('A',11,[(84,526),(588,1014)],[(168,392),(412,648),(668,902),(922,1172),(1192,1462)])
L['b2']=colmajor('B',11,[(8,512),(518,1016)],[(172,388),(428,648),(688,904),(948,1164),(1208,1462)])
