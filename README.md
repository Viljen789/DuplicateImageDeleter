# Duplicate Image Deleter

This project is a Python-based application that identifies and removes duplicate images between two directories (e.g., Google Drive and OneDrive). The program uses a graphical interface to allow users to manually confirm deletion decisions or skip them.

## Features

1. **Directory Management:**
   - Automatically generates directories for specified years and months.
   - Fills these directories with random images from a `TestPhotos` directory.

2. **Image Comparison:**
   - Compares images between directories using Structural Similarity Index (SSIM) from `skimage.metrics`.
   - Images with a similarity score above a defined threshold (e.g., 0.95) are flagged as duplicates.

3. **GUI Interaction:**
   - Provides a Tkinter-based interface to view and decide on duplicate images.
   - Buttons to accept or delete an image, and an option to cancel the process.

4. **Configurable Options:**
   - Choose whether to delete images from Google Drive or OneDrive.
   - Enable or disable confirmation prompts before deletion.

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
     python CreateDirs.py
     ```
   - The GUI will appear for flagged duplicate images, allowing you to decide on each case.

3. **Configuration:**
   - Modify the following variables in the script to suit your needs:
     - `DeleteFromGoogle`: Set to `True` to delete images from Google, `False` to delete from OneDrive.
     - `confirm`: Set to `True` to enable confirmation prompts before deletion.

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

---

## Notes

- **Performance:**
  - Comparing large image sets may take time. Optimize by reducing the number of images or directories.
- **Error Handling:**
  - The program skips missing files and handles exceptions gracefully.

---

Feel free to modify and adapt the code to your specific use case!
