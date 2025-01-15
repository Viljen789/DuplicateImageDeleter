# Duplicate Image Deleter

This project is a Python-based application that identifies and removes duplicate images between two directories (e.g., Google Drive and OneDrive). The program uses a graphical interface to allow users to manually confirm deletion decisions or skip them.

## Features

### **Enhanced Features:**
1. **Multi-Year and Multi-Month Directory Support:**
   - Handles directories for multiple years and months dynamically, ensuring a comprehensive comparison process.

2. **Preprocessing for Performance:**
   - Precomputes image pairs and caches resized grayscale versions for faster SSIM calculations.

3. **Flexible Threshold:**
   - Configurable similarity threshold for SSIM-based image comparison, enabling sensitivity adjustments.

4. **Modernized GUI:**
   - Displays both images flagged as duplicates side-by-side with options to keep, delete, or cancel.
   - Enhanced user interface with progress bars and dynamic updates.

5. **Threaded Preprocessing:**
   - Uses multithreading for preprocessing image pairs, ensuring the main application remains responsive during calculations.

6. **Improved Logging and Error Handling:**
   - Logs detailed error messages during image loading, resizing, or SSIM calculation.

7. **Configurable Deletion Behavior:**
   - Allows users to select whether to delete duplicates from Google Drive or OneDrive.
   - Option to enable or disable confirmation prompts for deletion actions.

---

## Requirements

- Python 3.8 or later
- Libraries:
  - `os`
  - `tkinter`
  - `cv2` (OpenCV)
  - `Pillow`
  - `skimage`
  - `shutil`
  - `random`

Install required packages:
```bash
pip install pillow opencv-python scikit-image
```

---

## How It Works

### **Step 1: Setup Directories**
The `CreateDirs` script creates year/month subdirectories under `./Google` and `./OneDrive` and populates them with random images from a `TestPhotos` directory.

### **Step 2: Compare Images**
- The program iterates through the specified year and month directories.
- For each pair of images, SSIM is used to calculate their similarity.
- If the similarity exceeds a threshold (default: 0.95), the images are flagged as duplicates.

### **Step 3: User Interaction**
- The user is presented with both images in a Tkinter window.
- Options include:
  - **Keep** one of the images.
  - **Delete** one of the images.
  - **Cancel** the deletion process.

---

## Usage

1. **Setup Your Files:**
   - Place the `TestPhotos` folder with sample images in the root directory.
   - The script will populate `./Google` and `./OneDrive` directories with random subsets of these images.

2. **Run the Program:**
   - Start the script by running:
     ```bash
     python DuplicateDelete.py
     ```
   - The GUI will appear for flagged duplicate images, allowing you to decide on each case.

3. **Configuration:**
   - Modify the following variables in the script to suit your needs:
     - `delete_from_google`: Set to `True` to delete images from Google, `False` to delete from OneDrive.
     - `confirm_delete`: Set to `True` to enable confirmation prompts before deletion.

---

## File Structure

```
.
├── CreateDirs.py          # Script to create and populate directories
├── DuplicateDelete.py     # Main script for detecting and deleting duplicate images
├── Google/                # Google Drive simulation folder
├── OneDrive/              # OneDrive simulation folder
├── TestPhotos/            # Source folder containing sample images
├── README.md              # Project documentation (this file)
```

---

## Example Output

1. **Folder Structure:**
   After running `CreateDirs.py`, the directories are organized as:
   ```
   Google/
   ├── 2025/
   │   ├── Jan/
   │   ├── Feb/
   │   └── ...
   ├── 2024/
   └── ...
   OneDrive/
   ├── 2025/
   │   ├── Jan/
   │   ├── Feb/
   │   └── ...
   ├── 2024/
   └── ...
   ```

2. **GUI Window:**
   - Displays both images flagged as duplicates.
   - Options to **keep**, **delete**, or **cancel**.

3. **Progress Bar:**
   - Real-time progress updates during image preprocessing and SSIM calculations.

---

## Notes

- **Performance:**
  - Comparing large image sets may take time. Optimize by reducing the number of images or directories.
- **Error Handling:**
  - Provides detailed error logs for missing files or calculation issues.

---

Feel free to modify and adapt the code to your specific use case!

