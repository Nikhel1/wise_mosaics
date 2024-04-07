# Download WISE Survey Images and Make Big Mosaics

This repository contains a back-to-back script that first downloads WISE (Wide-field Infrared Survey Explorer) survey images and then creates large mosaics, given the corners of a rectangle in the sky. The WISE survey comprises individual tiles of 1.5 square degrees each. The scripts provided here enable the downloading of these tiles for larger regions, for example, 30 square degrees, and subsequently create a single mosaic image using Montage.
If you use this, please cite our papers:

[Journal Paper](https://doi.org/10.1017/pasa.2023.64)
[Journal Paper](https://doi.org/10.1017/pasa.2024.25)

## Installation
First Install Montage (https://github.com/Caltech-IPAC/Montage.git) and the requirements.txt
```
git clone https://github.com/Caltech-IPAC/Montage.git
cd Montage
make
```
I attempted to install Montage on Linux, utilizing gcc-10.2.1 and Python 3.10.9, and faced not only the issues previously identified by other users (see issues int Montage github) but also encountered several new ones. Below is the list of adjustments I implemented to achieve a successful compilation of Montage.

### Update Makefile
Edit Makefile: Navigate to ~/Montage/Montage/ and update the Makefile.LINUX by adding -fcommon to CFLAGS:

makefile
Copy code
CFLAGS = -g -I. -I../lib/include -D_LARGEFILE_SOURCE -D_FILE_OFFSET_BITS=64 -std=c99 -fcommon
LIBS = -L../lib -lwcs -lcfitsio -lcoord -lmtbl -lsvc -lwww -lboundaries -lpixbounds -ltwoplane -lm
Remove -lnsl from the configuration.

Find and Replace -lnsl: If not using the development version, remove additional instances of -lnsl with:

bash
Copy code
find * -name 'Makefile.LINUX' | xargs sed -i 's/-lnsl//g'

### File Modifications
Make the following edits to specific files:

coord.h: In ~/Montage/lib/src/coord/coord.h, modify line 4 to:

c
Copy code
extern int coord_debug;
convertCoordinates.c: In ~/Montage/lib/src/coord/convertCoordinates.c, add at line 5:

c
Copy code
int coord_debug;
mMovingTarget.c: Adjust ~/Montage/util/MovingTarget/mMovingTarget.c by setting line 89 to:

c
Copy code
extern long nodeCount;
mSearch.c: Comment out line 75 in ~/Montage/util/Search/mSearch.c:

c
Copy code
/*long nodeCount; */
montageMakeHdr.c: Replace all instances (94) of input with hdr_input in ~/Montage/MontageLib/MakeHdr/montageMakeHdr.c.

montageSubimage.c: In ~/Montage/MontageLib/Subimage/montageSubimage.c, perform the following edits:

Change line 93 to:

c
Copy code
/* int haveBlank */
Insert at line 168:

c
Copy code
int haveBlank; // Inside the braces of struct mSubimageReturn
montageTANHdr.c: Modify ~/Montage/MontageLib/TANHdr/montageTANHdr.c as follows:

Change epoch to char_epoch:

Original	Change
char epoch[80];	char char_epoch[80];
strcpy(epoch, "");	strcpy(char_epoch, "");
strcpy(epoch, value);	strcpy(char_epoch, value);
if(haveEpoch) printf("epoch = [%s]\n", epoch);	if(haveEpoch) printf("epoch = [%s]\n", char_epoch);
sprintf(temp, "EPOCH = %s", epoch);	sprintf(temp, "EPOCH = %s", char_epoch);

With these adjustments, you should have a working version of Montage!

After this install rest of the dependencies
```
pip install -r requirements.txt
```
