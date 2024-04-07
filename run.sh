#!/bin/bash

# Define the path to the directory
images_wise_dir="./images_wise"

# Function to delete directories but keep files in the specified folder
cleanup_directories() {
    for item in "$images_wise_dir"/*; do
        if [ -d "$item" ]; then # If it's a directory
            rm -rf "$item" # Remove the directory
            echo "Removed directory: $item"
        fi
    done
}

# Function to run the Python script and handle failures
run_python_script() {
    python download_wise_make_mosaics.py
    exit_status=$?

    # Check if the script exited with a failure (non-zero exit status)
    if [ $exit_status -ne 0 ]; then
        echo "Script failed or was killed/stopped. Cleaning up..."
        cleanup_directories
        echo "Retrying..."
        run_python_script # Attempt to run the script again
    else
        echo "Script completed successfully."
    fi
}

# Initial call to the function
run_python_script


