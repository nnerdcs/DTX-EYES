#DTX Eyes v2.02

# DTX Eyes - View DTX Files and their headers and convert them to other formats easily.
# Header reading based off of Five-Damned-Dollarz research as well as the DTXFormat.cpp and dtxmgr_lib.cpp from the source code files.
#
# Written by nnerd

import lzma
import re
import argparse

# Run program from command line
parser = argparse.ArgumentParser(description='Converts DTX files to DDS; handles SPR files and LZMA compression. Written by nnerd.')
parser.add_argument('input', metavar='input', type=str, help='Input a DDS file or an SPR file path. The DTX files associated with the SPR files must be in the same location as the SPR file.')
args = parser.parse_args()
user_input = args.input

class DTX():

    def __init__(self, input_dir,):

        #The basics
        self.input_dir = input_dir
        self.lzma_compressed = 'No'

        print('\n')

        # Check if its reading an SPR file or a DTX file
        if str.upper(self.input_dir[-3:]) == 'DTX':
            self.dtx_dir = self.input_dir
            self.handleDTX()
            self.outputLog()
        elif str.upper(self.input_dir[-3:]) == 'SPR':
            self.spr_dir = input_dir
            self.handleSPR()
            self.outputLog()
        else:
            print('ERROR - Input must be a DTX or SPR file!')


    #Handle Sprites
    def handleSPR(self):

        #Check for LZMA compression in the .SPR file and decompress if necessary
        with open(self.spr_dir, "rb") as spr_file:
            spr_lzma_check = int.from_bytes(spr_file.read(4), 'little', signed = 'False')

        if spr_lzma_check == 93: # seems to be the best way i've found for checking if its LZMA compressed. i pray a user doesnt have a 93 frame SPR.
            decompressed_spr = self.spr_dir[:-4] + '_Decompressed' + self.spr_dir[-4:]
            with open(self.spr_dir, "rb") as spr_file, open(decompressed_spr, "wb") as lzma_spr_file:
                spr_file.seek(0)
                lzma_spr_file.write(lzma.decompress(spr_file.read()))
            self.spr_dir = decompressed_spr
        else:
            pass

        #Read the SPR
        with open(self.spr_dir, "rb") as spr_file:
            spr_file.seek(0)

            #Read Header
            self.spr_length = int.from_bytes(spr_file.read(4), 'little', signed = 'False')      #Amount of images in the sprite
            self.spr_idk = int.from_bytes(spr_file.read(4), 'little', signed = 'False')         #Maybe framerate? !!!
            self.spr_padding = int.from_bytes(spr_file.read(12), 'little', signed = 'False')    #Padding
            spr_content = spr_file.read()

            #Regex the .SPR's DTX path format
            spr_content = str(spr_content.replace(b"\x00", b"\x40")) # replace 00 bytes with an @ and create list using @ as the sepearation
            spr_content = spr_content.split("@")
            del spr_content[0] #cleanup

            # Build a list of DTX file names
            spr_dtx_names = []
            idx = 0
            for spr_DTX in spr_content:
                spr_DTX = str(re.findall(r".*\\\\(.*?)d", spr_content[idx])) #hopefully this works on all sprites.
                spr_DTX = (str(spr_DTX))[2:-2:] + 'DTX'
                spr_dtx_names.append(spr_DTX)
                idx = idx + 1

            # Recursively convert each DTX file to DDS
            spr_dtx_destination = (str(re.findall(r"(.+)[/\\]", self.input_dir)))[2:-2:] + '\\' #location from file path without os library lol
            idx = 0
            for spr_DTX in spr_content:
                self.dtx_dir = spr_dtx_destination + spr_dtx_names[idx]
                print('Processing Sprite', idx, self.dtx_dir)
                self.handleDTX()
                idx += 1
            print(f'\nSprite {self.spr_dir} read successfully.')


    #Handle DTX Files
    def handleDTX(self):
        self.readDTXHeader()
        self.lzmaCheckDTX()
        self.convertDTXDDS()


    #Read the DTX Header
    def readDTXHeader(self):
        with open(self.dtx_dir, "rb") as dtx_file:
            dtx_file.seek(0)

            #Read
            self.dtx_type = int.from_bytes(dtx_file.read(4), 'little', signed = 'False')           # Unused for DTX v2. Likely used in DTX v1, research needed.
            self.dtx_version = int.from_bytes(dtx_file.read(4), 'little', signed = 'False')        # DTX Version. '-5' = DTX v2
            self.dtx_width = int.from_bytes(dtx_file.read(2), 'little', signed = 'False')          # Texture Height 
            self.dtx_height = int.from_bytes(dtx_file.read(2), 'little', signed = 'False')         # Texture Width
            self.dtx_num_mipmaps = int.from_bytes(dtx_file.read(4), 'little', signed = 'False')    # Number of Mipmaps in the file
            self.dtx_format_1 = int.from_bytes(dtx_file.read(4), 'little', signed = 'False')       # Pixel Formatting Flags - 0008 for uncomp. RGB, 0088 for uncomp. RGBA
            self.dtx_format_2 = int.from_bytes(dtx_file.read(4), 'little', signed = 'False')       # Secondary Formatting Metadata - Unsure what goes here.
            self.dtx_user = int.from_bytes(dtx_file.read(2), 'little', signed = 'False')           # Internal Material Flags
            self.dtx_comp_type = int.from_bytes(dtx_file.read(2), 'little', signed = 'False')      # Compression Type - 4 = DTX1/BC1, 6 = DTX5/BC3, 3 = unknown
            self.dtx_padding_1 = int.from_bytes(dtx_file.read(124), 'little', signed = 'False')    # Matadata Padding
            self.dtx_padding_2 = int.from_bytes(dtx_file.read(12), 'little', signed = 'False')     # Trailing Padding
            
    #Check for LZMA Compression in DTX Files
    def lzmaCheckDTX(self):
        if self.dtx_width == 0 or self.dtx_height == 0:   # ive found that the first 32 or so bytes of the lzma compressed files i've looked at have been
            self.lzma_compressed = 'Yes'                  # zero. this checks both the width and height just in case thats not the case for all lzma'd files.
            self.lzmaDecompress()                         # it is not perfect though, if there is random data in these bytes, there is a small chance it could
            self.readDTXHeader()                          # this test if they both had values.
    # I have no idea why, but returning True or false on this just would not work. I have no idea why. Ill use the self.lzma_compressed var instead.


    #Decompress LZMA to a new file
    def lzmaDecompress(self):
        decompressed_dtx = self.dtx_dir[:-4] + '_Decompressed' + self.dtx_dir[-4:]
        with open(self.dtx_dir, "rb") as dtx_file, open(decompressed_dtx, "wb") as lzma_dtx_file:
            lzma_dtx_file.write(lzma.decompress(dtx_file.read()))
        self.dtx_dir = decompressed_dtx


    #Convert DTX to DDS
    def convertDTXDDS(self):

        self.dds_dir = self.dtx_dir[:-3] + 'dds'

        with open(self.dtx_dir, "rb") as dtx_file, open(self.dds_dir, "wb") as dds_file:
        #Reset to the first byte of the file just in case.
            dtx_file.seek(0)

        #Write DDS Header

            #Subheader - Main Header
            dds_file.write(b'\x44\x44\x53\x20') #DDS ASCII
            dds_file.write(b'\x7c\x00\x00\x00') #124 in Hex - This is the header length after the DDS ASCII
            dds_file.write(b'\x00\x00\x00\x00') #Depth - Original value was \x07\x10\x0A\x00 (7), but this isnt a volumetric texture so that doesnt make sense.
            dds_file.write(self.dtx_height.to_bytes(4, byteorder='little')) #Height
            dds_file.write(self.dtx_width.to_bytes(4, byteorder='little')) #Width
            #
            # Pitch or the Linear Size of the top-level image layer in bytes. Original value was \x00\x00\x00\x00.
            #  Pitch       - Only used when a file is uncompressed. It is the number of bytes in one vertical row of pixels. This program wont do uncompressed files unless an uncompressed DTX is found. This is unlikely as PNG files are also used in Crossfire's files as specular, alpha, and normal maps.
            #  Linear Size - The total size of the 'Top Level' or largest image in bytes. It states how much memory should be allocated to read the main image
            #                before it hits the mipmaps. linear size = max(1, (width+3)/4) * max(1, (height+3)/4) * block size.
            #              - DXT1 block size: 8 bytes
            #              - DXT5 block size: 16 bytes
            if self.dtx_comp_type == 6:
                block_size = 16
            else:
                block_size = 8 # <-- I'm banking on other potential compression types having 8bpp
            #
            dds_file.write((int(max(1, (int(self.dtx_width + 3) / 4 * block_size)))).to_bytes(4, byteorder='little')) #Write the calculated linear size to the dds
            #
            dds_file.write(b'\x01\x00\x00\x00') #Depth. Its a 2D image so its always going to be 1
            dds_file.write(self.dtx_num_mipmaps.to_bytes(4, byteorder='little')) #Mipmap levels
            dds_file.write(bytes(44)) #Reserved for flags

            # Subheader - Format
            dds_file.write(b'\x20\x00\x00\x00') #Length of this Subheader - Must be 32!
            dds_file.write(b'\x04\x00\x00\x00') #Pixel Format - In our case, always FourCC. DX1 and DX5 always use FourCC, unless wrapped in a DX10 file, which has not been found in a DTX file yet.
            if self.dtx_comp_type == 6:
                dds_file.write(b'\x44\x58\x54\x35') #Compression Format ASCII - In this case its DXT5
            else:
                dds_file.write(b'\x44\x58\x54\x31') #Compression Format ASCII - In other cases its most likely DXT1. See comment on line 84
            #
            dds_file.write(b'\x00\x00\x00\x00') #BPP for Uncompressed Formats - This program wont do uncompressed formats. See comment on line 76 for why.
            dds_file.write(b'\x00\x00\x00\x00') #Red Bitmask - This and the following 3 lines are used for uncompressed formats. I'll explain it anyways below:
            dds_file.write(b'\x00\x00\x00\x00') #Green Bitmask      Think of it as a text based mask. For example: if RBM = 000000FF, GMB = 0000FF00,
            dds_file.write(b'\x00\x00\x00\x00') #Blue Bitmask       BBM = 00FF0000, and ABM = FF000000, then our colors are written as RGBA across the 
            dds_file.write(b'\x00\x00\x00\x00') #Alpha Bitmask      four byte section. (Its backwards because its little endian.)

            # Subheader - Capabilities, Unused Flags, and Reserved Bytes
            dds_file.write(b'\x08\x10\x40\x00') #Complexity Capabilities (ex. Minimaps) <-- probably a leftover value from SHOW.exe's conversion? needs work !!!
            dds_file.write(b'\x00\x00\x00\x00') #Additional Capabilities (ex. Cubemaps) 
            dds_file.write(b'\x00\x00\x00\x00') # Unused Capability Flag
            dds_file.write(b'\x00\x00\x00\x00') # Unused Capability Flag
            dds_file.write(b'\x00\x00\x00\x00') # Reserved

            # Write Color Data from DTX to DDS
            dtx_file.read(164) #Skip the DTX file header
            dds_file.write(dtx_file.read())

            print('Converted', self.dtx_dir, 'to DDS.\n')


    # Write any warnings and some of the header info to the console
    def outputLog(self):

        #Check if the DTX compression type is recognized
        if self.dtx_comp_type not in (4,6): # A compression type 3 has been found, it is unknown what it does differently though. !!!
            print("\nWarning! Unrecognized Compression Type! Bytes 0x1A-0x1B gave unknown value", self.dtx_comp_type, "\n")

        #Process the DTX File Header Information
        if self.dtx_version == -5:
            self.dtx_version = 2
        else:
            self.dtx_version = f"Unknown DTX Version - {self.dtx_version}"

        if self.dtx_format_1 == 8:
            self.dtx_format_1 = 'Uncompressed RGB'
        elif self.dtx_format_1 == 136:
            self.dtx_format_1 = 'Uncompressed RGBA'
        else:
            self.dtx_format_1 = f"Unknown Color Space - {self.dtx_format_1}"

        if self.dtx_comp_type == 4:
            self.dtx_comp_type = 'DXT1/BC1'
        elif self.dtx_comp_type == 6:
            self.dtx_comp_type = 'DXT5/BC3'
        else:
            self.dtx_comp_type = f"Unknown Compression Type - {self.dtx_comp_type}"

        print("\nDTX Header Information",
            "\nFile Type (Legacy):    ", self.dtx_type, 
            "\nDTX Version:           ", self.dtx_version, 
            "\nDimensions:            ", self.dtx_width, "x", self.dtx_height, 
            "\nMipmap Count:          ", self.dtx_num_mipmaps, 
            "\nPixel Format:          ", self.dtx_format_1,
            "\nDXT Compression Type:  ", self.dtx_comp_type,
            "\nLZMA Compressed File:  ", self.lzma_compressed
        )

DTX(user_input)