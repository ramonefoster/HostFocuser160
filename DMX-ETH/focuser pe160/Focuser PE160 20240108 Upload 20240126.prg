;*************************
PRG 0
V33=20240108
V50=64
V49=64
V44=0
END

;*************************
SUB 0
V1=V46
V46=1
V30=0
V1=V1&255
V2=V31<<8
V2=V32&7936
V3=0
IF EO = 1
 V3=8192
ENDIF 
V4=V44&32
IF V4 > 0
 V3=V3+16384
ENDIF 
V5=V44&95
IF V5 > 0
 V3=V3+32768
ENDIF 
V11=MSTX
V5=V11&511
V5=V5<<16
V6=LTSX
V6=V6&3
V7=DO
V7=V7<<2
V7=V7+DI
V7=V7<<2
V7=V7+V6
V8=V7<<25
V9=V1+V2
V9=V9+V3
V9=V9+V5
V30=V9+V8
V46=0
ENDSUB 
;*************************
SUB 29
V46=1
V71=2165440
V74=8576
V1=V20
V2=EX
IF V1 <= 0
V46=172
SR0=0
ENDIF 
IF V1 > V71
V46=173
SR0=0
ENDIF 
IF V44 != V50
V46=176
SR0=0
ENDIF 
IF V1 = V2
V46=0
SR0=0
ENDIF 
ABS
EO=1
HSPD=250000
LSPD=10000
ACC=300
DEC=300
IF V1 < V2
V3=V1-V74
IF V3 <= V74
 JOGX-
 WAITX
 ECLEARX
 V11=MSTX
 V5=V11&16
 WHILE V5 > 0
  ZOMEX+
  WAITX
  V11=MSTX
  V5=V11&16
 ENDWHILE 
ELSE
 V10=10*V3
 XV10
 WAITX
ENDIF 
ENDIF 
V10=10*V1
XV10
WAITX
EO=0
V46=0
ENDSUB 
;*************************
SUB 30
V46=1
V44=0
EO=1
HSPD=250000
LSPD=10000
ACC=100
JOGX-
WAITX
ECLEARX
V11=MSTX
V5=V11&16
WHILE V5 > 0
ZOMEX+
WAITX
V11=MSTX
V5=V11&16
ENDWHILE 
V44=V50
EO=0
V46=0
ENDSUB 
;*************************
SUB 31
ECLEARX
ENDSUB 
END

