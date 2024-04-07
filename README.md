# Download WISE Survey Images and Make Big Mosaics

This repository contains a back-to-back script that first downloads [WISE (Wide-field Infrared Survey Explorer) survey images](http://unwise.me/data/neo3/unwise-coadds/fulldepth) and then creates large mosaics, given the corners of a rectangle in the sky. The WISE survey comprises individual tiles of 1.5 square degrees each. The scripts provided here enable the downloading of these tiles for larger regions, for example, 30 square degrees, and subsequently create a single mosaic image using Montage.
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

**Update Makefile**
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

**File Modifications**
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

After this, install rest of the dependencies
```
pip install -r requirements.txt
```

## Make directories
You'll need two directories
```
mkdir images
mkdir images_wise
```
Download the FITS image file, for which you want to generate a corresponding WISE survey mosaic image, into the `./images` directory. I conducted tests using EMU radio survey tiles, approximately 30 square degrees in size, which are available for download from CASDA: https://data.csiro.au/domain/casdaObservation. It's possible to download and incorporate multiple files from CASDA into your project. Example: `./images/image.i.EMU_2359-04A.SB54097.cont.taylor.0.restored.conv.fits`

If your project requires generating a mosaic for specific rectangular areas in the sky, you can input these coordinates into `download_wise_make_mosaics.py`. Additionally, should you wish to retain area files for the mosaic, this functionality can be preserved by deactivating the remove command within `download_wise_make_mosaics.py`.


## Running the script
Given the possibility of filesystem interruptions or the termination of the job due to .nfs load issues, it is advisable to initiate the downloading and mosaicing process through the bash script instead of directly using download_wise_make_mosaics.py. The bash script is designed to automatically restart the process in case it is unexpectedly terminated for any reason.
```
bash run.sh
```
That's it your big WISE mosaics are ready!
