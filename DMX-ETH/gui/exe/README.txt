SA Download Upload

1) Prepare "sa_download_uplaod_setup.txt" configuration file and then
   execute the .exe.

2) For upload operations output will be written into "UploadOut.txt"

3) For download/clear opearations output will be written into "DownloadOut.txt"

4) Explanation of configuration file: "sa_download_upload_setup.txt"

LIN: max # of stand-alone lines
COM: USB/Serial/ETHERNET
POR: Comport number(for Serial), Or Port for Ethernet
BAU: Baud rate (for Serial)
OPE: UPLOAD/DOWNLOAD/CLEAR
FIL: Name of text file to download
MOD: Arcus Model (PMX-4EX-SA, PMX-2EX-SA, etc)
IPA: 192.168.1.250

Example:

LIN:1785
COM:USB
POR:6
BAU:9600
DEV:00
OPE:UPLOAD
FIL:CompileOut.txt
MOD:PMX-4EX-SA