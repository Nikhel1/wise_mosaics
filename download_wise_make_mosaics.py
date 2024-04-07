import numpy as np
import glob
import subprocess
import shutil
import requests
from astropy.io import fits
from astropy.table import Table
from astroquery.ipac.irsa import Irsa
from astropy.wcs import wcs
from astropy.coordinates import SkyCoord
import astropy.units as u
import urllib
import os
import re
#import montage_wrapper as montage
from MontagePy.main import mProject, mAdd, mBgModel, mImgtbl, mMakeHdr, mDiffFitExec
from MontagePy.main import mDiff, mFitplane, mFitExec, mOverlaps, mBgExec, mProjExec


def download_file(url, local_filename=None, download_dir=''):
    """Download a file from a URL."""
    if local_filename is None:
        local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(download_dir+local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    #print(f"Downloaded {download_dir+local_filename}")
    return download_dir+local_filename

def filter_and_extract_fits(input_file, condition, columns):
    """Filter a FITS file and extract specific columns."""
    with fits.open(input_file) as hdul:
        data = Table(hdul[1].data)
        filtered_data = data[(data['dec'] > -1.6) & (data['dec'] < 1.6)]
        return filtered_data[columns]
        
def filter_and_extract_fits_within_corners(input_file, corners, columns):
    """Filter a FITS file to include only data within the polygon defined by corners and extract specific columns."""
    with fits.open(input_file) as hdul:
        data = Table(hdul[1].data)
        
        # Calculate the bounding box of the corners
        ra_values = [corner.ra.deg for corner in corners]
        dec_values = [corner.dec.deg for corner in corners]
        ra_min, ra_max = min(ra_values), max(ra_values)
        dec_min, dec_max = min(dec_values), max(dec_values)
        
        # Filter data within the bounding box
        filtered_data = data[(data['ra'] >= ra_min) & (data['ra'] <= ra_max) &
                             (data['dec'] >= dec_min) & (data['dec'] <= dec_max)]
        if (ra_max-ra_min)>=50:
            ra_min, ra_max = max(ra_values), min(ra_values)
            filtered_data = data[((data['ra'] >= ra_min) | (data['ra'] <= ra_max)) &
                                 (data['dec'] >= dec_min) & (data['dec'] <= dec_max)]
        return filtered_data[columns]

def download_images(coadd_ids, base_url, download_dir=''):
    """Download image files for each coadd_id."""
    for coadd_id in coadd_ids:
        dir1 = coadd_id[:3]
        url = f"{base_url}/{dir1}/{coadd_id}/unwise-{coadd_id}-w1-img-m.fits"
        if os.path.exists(f'{download_dir}unwise-{coadd_id}-w1-img-m.fits'):
            continue
        download_file(url, download_dir=download_dir)

def run_command(command):
    """Run a command using subprocess."""
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        print(output.decode())
    except subprocess.CalledProcessError as e:
        print("Error executing command:", e.output.decode())
        raise


# Main script
if __name__ == "__main__":
	tiles_url = "http://unwise.me/data/allwise/unwise-coadds/fulldepth/tiles.fits"
	base_url = "http://unwise.me/data/neo3/unwise-coadds/fulldepth"
	tiles_filename = download_file(tiles_url)

	EMU_filenames = glob.glob('./images/*.fits')
	for filename in EMU_filenames:
		#filename = './images/image.i.EMU_2359-04A.SB54097.cont.taylor.0.restored.conv.fits'
		mosaic_image = './images_wise/'+os.path.basename(filename)[:-5]+'_wise_mosaic.fits'
		if os.path.exists(mosaic_image):
			print (f'Mosaic image {mosaic_image} exists.')
			continue
		outdir = './images_wise/'+os.path.basename(filename)[:-5]+'_wise/'
		if not os.path.exists(outdir):
			os.mkdir(outdir)

		w = wcs.WCS(filename, naxis=2)
		corners = w.calc_footprint(fits.getheader(filename))
		cosdec = np.cos(w.wcs.crval[1]*np.pi/180)
		#Create a buffer around the image containing the target area.
		offsets = np.array([[+1/cosdec,-1],
						[+1/cosdec,+1],
						[-1/cosdec,+1],
						[-1/cosdec,-1]])*1.5
		corners = corners+offsets
		corners = [SkyCoord(ra=cc[0],dec=cc[1],unit='deg',frame='fk5') for cc in corners]

		coadd_ids = filter_and_extract_fits_within_corners(tiles_filename, corners, ["coadd_id"])
		print(f"Total number of files: ", len(coadd_ids))
		print(f"Downloading for {outdir}.")
		download_images(coadd_ids['coadd_id'], base_url, download_dir=outdir)
		print(f"All files in {outdir} have been downloaded.")
	
		# Mosaics with Montage
		# Create a directory for the reprojected images
		project_dir = outdir+'project'
		if not os.path.exists(project_dir):
			os.makedirs(project_dir)

		# Directory for the corrected images
		corr_dir = os.path.join(project_dir, 'corrected')
		if not os.path.exists(corr_dir):
			os.makedirs(corr_dir)
			
		diff_dir = os.path.join(project_dir, 'diff')
		if not os.path.exists(diff_dir):
			os.makedirs(diff_dir)

		# List of input FITS files
		fits_files = [f for f in os.listdir(outdir) if f.endswith('.fits')]

		# Generate an image metadata table
		raw_table = outdir+'rimages.tbl'
		mImgtbl(outdir, raw_table)

		# Generate a header template for the mosaic
		template_hdr = outdir+'template.hdr'
		mMakeHdr(raw_table, template_hdr)

		# Reproject the images
		print("Reprojecting images...")
		reprojected_table = os.path.join(project_dir, 'pimages.tbl')
		#mProjExec(outdir, raw_table, template_hdr, project_dir, quickMode=True)
		for file in fits_files:
			output_file = os.path.join(project_dir, file)
			mProject(outdir+file, output_file, template_hdr)

		# Generate a metadata table for the reprojected images
		mImgtbl(project_dir, reprojected_table)
		
		# Determine the overlaps between images (for background modeling).
		overlaps_table = os.path.join(project_dir, 'diff.tbl')
		mOverlaps(reprojected_table, overlaps_table)
		
		# Fit planes to difference images and compile fits into a table
		fits_table = os.path.join(project_dir, 'fits.tbl')
		mDiffFitExec(project_dir, overlaps_table, template_hdr, diff_dir, fits_table)

		# Model the background to match across images
		print("Modeling background...")
		bg_model_table = os.path.join(corr_dir, 'corrections.tbl')
		mBgModel(reprojected_table, fits_table, bg_model_table)

		# Apply the background models
		print("Applying background corrections...")
		mBgExec(project_dir, reprojected_table, bg_model_table, corr_dir)
		cimg_table = os.path.join(corr_dir, 'cimages.tbl')
		mImgtbl(corr_dir, cimg_table)
		
		# Create the final mosaic
		print("Creating final mosaic...")
		mAdd('./', cimg_table, template_hdr, mosaic_image, haveAreas=True, shrink=True)

		print("Mosaic created:", mosaic_image)


		# Attempt to open the FITS file
		try:
			with fits.open(mosaic_image) as hdul:
				print(f"Successfully opened {mosaic_image}")
				# Optionally, do something with the file, e.g., print header info
				#hdul.info()
				print(wcs.WCS(hdul[0].header))
				print('-------')
				print('Image shape: ',hdul[0].data.shape)
		except FileNotFoundError:
			print(f"Error: The file {mosaic_image} does not exist.")
		except OSError as e:
			print(f"Error opening {mosaic_image}: {e}")

		# Delete directory files and mosaic_area file
		dir_to_remove = outdir
		def delete_files_except_nfs(dir_path):
			for item in os.listdir(dir_path):
				item_path = os.path.join(dir_path, item)
				if os.path.isdir(item_path):
					# If item is a directory, recursively call this function
					delete_files_except_nfs(item_path)
				elif os.path.isfile(item_path) and not item.startswith('.nfs'):
					# If item is a file and not an .nfs file, delete it
					os.remove(item_path)
					#print(f"Removed file: {item_path}")
		delete_files_except_nfs(dir_to_remove)
		
		file_path_remove = f'{dir_to_remove[:-1]}_mosaic_area.fits'
		# Check if the file exists to avoid errors
		if os.path.isfile(file_path_remove):
			try:
				os.remove(file_path_remove)
				print(f"File '{file_path_remove}' has been removed successfully.")
			except Exception as e:
				print(f"Error removing file '{file_path_remove}': {e}")
		else:
			print(f"File '{file_path_remove}' does not exist.")
	
	# Delete all sub-directories in images_wise in the end.
	EMU_filenames = glob.glob('./images/*.fits')
	for filename in EMU_filenames:
		outdir = './images_wise/'+os.path.basename(filename)[:-5]+'_wise/'		
		dir_to_remove = outdir
		def onerror(func, path, exc_info):
			# Attempt to change the permission and delete the file again
			os.chmod(path, 0o777)
			func(path)
		if os.path.isdir(dir_to_remove):
			try:
				shutil.rmtree(dir_to_remove, onerror=onerror)
				print(f"Directory '{dir_to_remove}' has been removed successfully.")
			except Exception as e:
				print(f"Error removing directory '{dir_to_remove}': {e}")
		else:
			print(f"Directory '{dir_to_remove}' does not exist.")

