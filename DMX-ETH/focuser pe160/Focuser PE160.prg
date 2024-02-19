;
; ===================
; PEDMX FOCUSER-PE160 
; ===================	
;
; RUN INSIDE DMX-ETH MOTOR OF FOCUS ON
; PERKIN&ELMER 1.6m TELESCOPE
;
; Current version number stored on V33.
;
; VERSION 20240127
; ================
; - HSPD NEW VALUE = 214400 (500 microns/s) 
; - INCLUDED STOP COMMAND (V42=1)
; - INCLUDED FOCUSOUT SUBROUTINE (SUB 20)
; - INCLUDED FOCUSOUT SUBROUTINE (SUB 21)
;
; INSTRUCTIONS
; ============
; NOTE: Every instruction sent to motor must be appended with
; a null ASCII character (hexadecimal 0).
; INIT/HOME: Moves mechanism to reference position.
; 	Instruction: 		GS30
; GOTO: Moves mechanism to target position (positive value)
;		Instructions:		V20=12345		-> Set target position (e.g. 12345)
;										GS29
; STOP: Stop any motor movement
;		Instructions: 	STOP
;										SR0=0
; STATUS: Read motor status (see comments of SUB 0 for details)
;		Instructions:		GS0
;										V30			(returns status)
; GET POSITION: returns a negative value, must be multiplied by -1
;		Instruction:		EX
; GET FLAG BUSY/ERROR Status of motor running condition
;		Instruction:		V46			(=0 for READY, =1 for BUSY, or ERROR code)
; GEY FLAG INIT DONE: if =0 blocks the GOTO instruction
;		Instruction:		V44
; - SUBROUTINES are used by Focus Controller.
; Subroutines are implicitly contained in Program 0 and 
; respond to commands SASTAT0 and SR0. 
;
; - The IF/ELSE/ELSEIF/ENDIF of DMX-ETH language
; is limited to 2 nested structures.
;
; - With normal polarity (POL=0): 
; When DO=0 (firmware), current flows to load.
; When an input is disconnected, firmware reads input_bit=0.
;
; - If LIM+/- inputs is actuated during a
; movement, SUB 31 clears its error flag.
;
; - The available memory (44.5 KB) for standalone programs is 7650 assembly lines
; and each line of pre-compiled code equates to 1-4 lines of assembly lines.
;
;
; INPUTS
; LIM-:		microswitch at focus IN limit, used as reference
; LIM+:		microswitch at focus OUT limit.
;
; DIRECTION OF MOVEMENT
; ---------------------
; With JOG- the mechanism moves towards LIM- switch
;
;***********************
;* GENERAL SUBROUTINES *
;***********************
; Subroutines are implicitly 
; contained in Program 0 and 
; respond to SASTAT0 and SR0. 
;
;****************************************
PRG 0	; HARDWARE MECHANISM IDENTIFICATION
;****************************************
; V44: INIT flag of all mechanisms.
; V45: Motor polarity, set by S4DMX, used by ICS to write motor POL register.
; V46: Running status. =0 for READY, =1 for BUSY, or error code otherwise.
; V50: Mechanism hardware ID, set by S4DMX.
; --------------------------------------------
	V33 = 20240127		; Current S4DMX version.
	V50 = 64					; Set ID=64 for unplugged motor
	V49 = 64					; ICS sets V49 = V50 to enable movements
	V71 = 2165440			; Maximum target position (encoder units)
	V74 = 5360				; # overtravel encoder displacement to eliminate backlash. (5/8 rev)
	HSPD = 250000			; Equivalent to 500 microns/second
	LSPD = 10000
	ACC = 300
	DEC = 300
	V44 = 0						; Clear INIT flag of all mechanisms
	; Testar conexao uswitchs ?
END									; End Program 0
;
;=====================
SUB 0	; STATUS REQUEST
;=====================
;
;	Insert into V30 some information about motor and mechanism
;
;	Resulting bit fields are:
;	struct	V30 {
;			int track :	 8		// original track and error codes of V46. = V46&255
;			int index	:  5		// free parameter, =(V11&32)<<10
;			int eo:      1		// motor driver state =(EO<<15)
;			int init:  	 2		// INIT done flag, =(GFOCinit OTHERSinit)<<29
;			int status:	 9		// motor status, =(MST&511)<<16
;			int latch:	 2		// latch status
;			int io:      4		// motor inputs&outputs states, =(DO2 DO1 DI2 DI1)<<25
;
;	100 calls to SUB 0 takes 25 seconds (DMX-ETH GUI running)
;--------------------
;
	V1 = V46					; Saves previous error code
	V46 = 1			 			; Set start SUB code
	V30 = 0						; Clear previous status
	V1 = V1 & 255			; Get tracking/error code (1st 8 bits)
	V2 = V31 << 8			; Predefined position index (bits 8-12)  
	V2 = V32 & 7936		; If V31=-1, V2 = 7936 (all bits 8-12 = 1).
	V3 = 0
	IF EO = 1
		V3 = 8192				; 8192 = 2^13 (bit 13)
	ENDIF
	V4 = V44 & 32			; Mask GFOC INIT done flag
	IF V4 > 0
		V3 = V3 + 16384	; GFOC INIT flag at bit 14
	ENDIF
	V5 = V44 & 95			; V44&95 is greater than zero if initialization was
	IF V5 > 0					; performed (except for GFOC). 
		V3 = V3 + 32768	; INIT done flag of others mechanisms at bit 15
	ENDIF
	V11 = MSTX
	V5 = V11 & 511		; Mask the 11 LSBs of motor status
	V5 = V5 << 16			; bits 16-26
	V6 = LTSX					; Get latch status (2 bits)
	V6 = V6 & 3
	V7 = DO
	V7 = V7 << 2
	V7 = V7 + DI
	V7 = V7 << 2
	V7 = V7 + V6
	V8 = V7 << 25			; Shift the two bits of INIT done, DO, and DI	
	V9 = V1 + V2
	V9 = V9 + V3
	V9 = V9 + V5
	V30 = V9 + V8
	V46 = 0			 			; Set end SUB code
ENDSUB
;
;
;=================
SUB 20	; FOCUSOUT
;=================
;			Unit: 					encoder units
;			Range:					1 - 2165440 (1 - 50700 um)
; 		SUB 31 REQUIRED
;--------------------
; V21: velocity (set by host controller)
; V42: Stop command placed by host controller. When V42=1, motor stops
; V44: flag bit (V44&1) initialization routine done
; V71: Maximum position in encoder units = 2165440 : 50700 um
; V74: overtravel pulses to eliminate backlash = 5360 encoder units (125 um)
;
	V46 = 1			 			; Set start SUB code
	V42 = 0						; Clear stop flag
	; Check for valid velocity range
	V1 = V21					; Velocity entry
	IF V1 <= 0
		; Out of range
		V46 = 120				; Set Parameter low value error code
		SR0 = 0					; End Sub (turn off Program 0)
	ENDIF
	IF V21 > 214400
		V21 = 214400
	ENDIF
	HSPD = V21				; Set velocity
	ABS								; Select absolute mode
	EO = 1						; Enable motor driver
	; Move in forward direction towards maximum position
	V10 = 10 * V71		; Convert encoder unit to step unit
	XV10							; Start movement
	; Wait end of movement or stop command
	V8 = 1
	WHILE V8 > 0
		V11 = MSTX	; Read status
		V8 = V11 & 3;	Motor moving bits
		IF V42 = 1	; Check stop command
			STOPX
			DELAY = 500	; Desacceleration time = 300
			V8 = 0			; Exit while loop
		ENDIF
	ENDWHILE
	EO = 0						; Disable motor driver
	HSPD = 214400			; Return velocity to defalt value
	V42 = 0						; Clear stop command
	V46 = 0			 			; Set end SUB code
ENDSUB 
;
;
;================
SUB 21	; FOCUSIN
;================
;			Unit: 					encoder units
;			Range:					1 - 2165440 (1 - 50700 um)
; 		SUB 31 REQUIRED
;--------------------
; V21: velocity (set by host controller)
; V42: Stop command placed by host controller. When V42=1, motor stops
; V44: flag bit (V44&1) initialization routine done
; V71: Maximum position in encoder units = 2165440 : 50700 um
; V74: overtravel pulses to eliminate backlash = 5360 encoder units (125 um)
;
	V46 = 1			 			; Set start SUB code
	V42 = 0						; Clear stop flag
	; Check for valid velocity range
	V1 = V21					; Velocity entry
	IF V1 <= 0
		; Out of range
		V46 = 121				; Set Parameter low value error code
		SR0 = 0					; End Sub (turn off Program 0)
	ENDIF
	IF V21 > 214400
		V21 = 214400
	ENDIF
	HSPD = V21				; Set velocity
	ABS								; Select absolute mode
	EO = 1						; Enable motor driver
	; Move in reverse direction. Using overtravel value
	; as target position to avoid re-INIT.
	V10 = 10 * V74		; Convert encoder unit to step unit
	XV10							; Start movement
	; Wait end of movement or stop command
	V8 = 1
	WHILE V8 > 0
		V11 = MSTX	; Read status
		V8 = V11 & 3;	Motor moving bits
		IF V42 = 1	; Check stop command
			STOPX
			DELAY = 500	; Desacceleration time = 300
			V8 = 0			; Exit while loop
		ENDIF
	ENDWHILE
	; Move overtravel value in foward direction to remove backlash
	V2 = EX						; Current motor position
	V3 = V2 + V74			; Adds overtravel
	V10 = 10 * V3			; Convert encoder unit to step unit
	XV10							; Move (forward)
	WAITX
	EO = 0						; Disable motor driver
	HSPD = 214400			; Return velocity to defalt value
	V42 = 0						; Clear stop command
	V46 = 0			 			; Set end SUB code
ENDSUB 
;
;
;===================
SUB 29	; FOCUS GOTO
;===================
;			Unit: 					encoder units
;			Range:					1 - 2165440 (1 - 50700 um)
; 		SUB 31 REQUIRED
;--------------------
; V20: target position (set by ICS)
; V42: Stop command placed by host controller. When V42=1, motor stops
; V44: flag bit (V44&1) initialization routine done
; V71: Maximum position in encoder units = 2165440 : 50700 um
; V74: overtravel pulses to eliminate backlash = 5360 encoder units (125 um)
;
	V46 = 1			 			; Set start SUB code
	V42 = 0						; Clear stop flag
	; Check for input position range
	V1 = V20					; Position entry
	V2 = EX						; Current motor position
	IF V1 < 0
		; Out of range
		V46 = 172				; Set Parameter low value error code
		SR0 = 0					; End Sub (turn off Program 0)
	ENDIF
	IF V1 > V71
		; Out of range
		V46 = 173				; Set Parameter high value error code
		SR0 = 0					; End Sub (turn off Program 0)
	ENDIF
	IF V44 != V50
		V46 = 176				; Set INIT not executed error code
		SR0 = 0					; End Sub (turn off Program 0)
	ENDIF
	IF V1 = V2
		; Current = Target position
		V46 = 0					; Set end SUB code
		SR0 = 0					; End Sub (turn off Program 0)
	ENDIF
	ABS								; Select absolute mode
	EO = 1						; Enable motor driver
	V9 = 0						; Clear isMoving flag
	IF V1 < V2				; V1 = target pos., V2 = initial position
		; Target position less than current position
		IF V1 <= V74
			; Target position near HOME position. Re-init and then go
			JOGX-					; Move until LIM- activation
			WAITX
			; HOME with Z index 
			ECLEARX				; Clear any motor error
			V5 = 1
			; Execute HOME to encoder index until LIM- is actuated
			WHILE V5 > 0
				ZOMEX+
				WAITX
				V11 = MSTX
				V5 = V11 & 16
			ENDWHILE
			V9 = 0				; Clear isMoving flag
		ELSE
			; Target position needs overtravel
			V3 = V1 - V74	; Adds overtravel to target position
			V10 = 10 * V3	; Convert encoder unit to step unit
			XV10					; Start movement
			V9 = 1				; Set isMoving flag
			; Wait for a displacement greater than overtravel 
			; in order to enable stop command
			V6 = 0
			WHILE V6 < V74
				V7 = EX
				V6 = V2 - V7	; V2 = initial position
			ENDWHILE
		ENDIF
	ENDIF
	IF V9 = 1
		; Motor is moving. Wait end of movement or stop command
		V8 = 1
		WHILE V8 > 0
			V11 = MSTX	; Read status
			V8 = V11 & 3;	Motor moving bits
			IF V42 = 1	; Check stop command
				STOPX
				DELAY = 500	; Desacceleration time = 300
				V1 = V74	; Set overtravel as target position
				V8 = 0		; Exit while loop
			ENDIF
		ENDWHILE
	ENDIF
	; Move to target position in forward direction
	V10 = 10 * V1			; Convert encoder unit to step unit
	XV10							; Start movement
	; Wait end of movement or stop command
	V8 = 1
	WHILE V8 > 0
		V11 = MSTX	; Read status
		V8 = V11 & 3;	Motor moving bits
		IF V42 = 1	; Check stop command
			STOPX
			DELAY = 500	; Desacceleration time = 300
			V8 = 0		; Exit while loop
		ENDIF
	ENDWHILE
	EO = 0						; Disable motor driver
	V42 = 0						; Clear stop command
	V46 = 0			 			; Set end SUB code
ENDSUB 
;
;
;===================
SUB 30	; FOCUS INIT
;===================
; 			SUB 31 REQUIRED
;
;				FOCUS PE 160:
;       -------------------
;				Reduction: 3125 um/ 134rev (~23.3 um/rev). 
;				Range: 0 to 50700 um  
;				Motor encoder range: 1 - 20240127 (50 ustep/step)
;				Measured Backlash: 4000 encoder units (~ 94 um)
;				Backward displacement to compensate for backlash: (5360 encoder units, ~ 125 um)
;--------------------
; V44: flag bit (V44&1) initialization routine done
; V46: OUTPUT: routine status, =1 during execution, =0 for normal finish, or error code.
;--------------------
;
	V46 = 1			 			; Set start SUB code
	V44 = 0						; Reset INIT flag

	; Moves towards reference position, cheking stop command (V42)
	EO = 1						; Enable motor driver
	V12 = EX					; Read current position
	V1 = V12 - V71		; Displacement to reach reference position
	V10 = 10 * V1			; converted to step units
	V42 = 0						; Clear stop flag
	XV10							; Start moving
	V2 = 0						; Enable while loop
	WHILE V2 = 0
		; Check LIM- sensor state
		V11 = MSTX			; Read motor status
		V2 = V11 & 16		; LIM- bit. If set exits from while loop
		; Check stop flag
		IF V42 > 0
			STOPX					; Stop motor
			V2 = 1				; Exit from while loop
		ENDIF
	ENDWHILE
	ECLEARX						; Clear any motor error
	; Read LIM- sensor 
	V11 = MSTX				; Read motor status
	V3 = V11 & 16			; LIM- bit. If set exits from while loop
	IF V3 > 0
		; HOME with Z index 
		WHILE V3 > 0
			ZOMEX+
			WAITX
			V11 = MSTX
			V3 = V11 & 16
		ENDWHILE 
		V44 = V50					; Set INIT executed flag
	ENDIF
	EO = 0						; Disable motor driver
	V42 = 0						; Clear stop flag
	V46 = 0			 			; Set end SUB code
ENDSUB
;
;
;=======================
SUB 31	; ERROR HANDLING
;=======================
	; Bit 12 of POL register (Jump to line 0 on error) must be cleared
	ECLEARX			 			; Clear error flag
ENDSUB
;
END
;