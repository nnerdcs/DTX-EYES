# DTX-EYES
Read and convert Lithtech .DTX and .SPR files to .DDS. Handles LZMA compression and gives header information.

Special thanks
	- Five-Damned-Dollarz - DTX Header Research
	  https://github.com/Five-Damned-Dollarz

Background
	This program is aimed at converting Lithtech DTX v2 image texture files to DDS format, while detecting and handling LZMA compression on its own. This program can also read .SPR Sprite files and convert their associated DTX files to DDS format.

How to use
  Just like any other command line tool. Please use Python 3 for best results. Open your command line and type 'pythonX' (X being your python version), followed by the path to where you saved this program, followed by the path to the file you are inputting.

  This program takes one input and outputs to the same location as your input file. 

Disclaimers and Warnings
  - Currently has only been tested on DTX v2 files from Crossfire's engine (Modified? Lithtech Jupiter EX)
  - DTX files have a flag for the type of DXT compression they use. A value of 4 means it uses DXT1 and a value of 6 means it uses DXT5. A DTX file with the value of 3 was found in crossfire's files. I am still looking into this.
  - The DTX files associated with an SPR file MUST be in the same directory as the DTX file!
