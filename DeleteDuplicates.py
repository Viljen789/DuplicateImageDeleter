import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from skimage.metrics import structural_similarity as ssim
import threading
import queue

# Adjust these variables as needed
similarity_threshold = 0.5  # Can adjust for more/less sensitivity
resize_size = (512, 512)  # Size for SSIM calculation
display_max_size = (300, 300)  # GUI size

months_en = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
months_no = [
    "Januar", "Februar", "Mars", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Desember"
]
months_test = [x[:3] for x in months_en[:4]]  # ["Jan","Feb","Mar","Apr"]

resized_cache = {}  # Dict from path -> grayscale image

def read_and_resize_image_for_ssim(path, size=resize_size):
    global resized_cache
    if path in resized_cache:
        return resized_cache[path]

    if not os.path.exists(path):
        return None

    try:
        pil_image = Image.open(path)
        pil_gray = pil_image.convert("L")
        pil_gray = pil_gray.resize(size, resample=Image.Resampling.LANCZOS)
        arr = np.array(pil_gray)
        resized_cache[path] = arr
        return arr
    except Exception as e:
        print(f"Error reading/resizing '{path}': {e}")
        return None

def rescale_image_for_display(pil_image, max_width=300, max_height=300):
    width, height = pil_image.size
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        return pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return pil_image

class ImageComparatorApp:
    def __init__(
            self,
            root,
            start_year,
            end_year,
            onedrive_base,
            google_base,
            delete_from_google=True,
            confirm_delete=False
    ):
        self.root = root
        self.start_year = start_year
        self.end_year = end_year
        self.onedrive_base = onedrive_base
        self.google_base = google_base
        self.delete_from_google = delete_from_google
        self.confirm_delete = confirm_delete
        self.done = False

        self.image_pairs = []
        self.current_index = 0
        self.current_pair = None
        self.current_pair_path = None
        self.current_del_img = None

        self.setup_gui()
        self.queue = queue.Queue()

        self.precompute_thread = threading.Thread(target=self.precompute_pairs)
        self.precompute_thread.daemon = True
        self.precompute_thread.start()

        self.root.after(100, self.check_queue)

    def setup_gui(self):
        self.root.geometry("700x600+200+100")

        self.top_label_text = tk.StringVar(value="No image pairs loaded.")
        self.top_label = tk.Label(self.root, textvariable=self.top_label_text, font=("Helvetica", 14))
        self.top_label.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=500, mode='determinate')
        self.progress.pack(pady=10)
        self.progress['value'] = 0

        self.frame_images = tk.Frame(self.root)
        self.frame_images.pack(pady=5)
        self.google_label = tk.Label(self.frame_images)
        self.google_label.grid(row=0, column=0, padx=10)
        self.onedrive_label = tk.Label(self.frame_images)
        self.onedrive_label.grid(row=0, column=1, padx=10)

        self.btn_accept = tk.Button(self.root, text="Keep", width=12, command=self.on_accept, state=tk.DISABLED)
        self.btn_reject = tk.Button(self.root, text="Delete", width=12, command=self.on_reject, state=tk.DISABLED)
        self.btn_leave = tk.Button(self.root, text="Stop Deletion", width=15, command=self.on_leave,
                                   state=tk.DISABLED)
        self.btn_accept.place(relx=0.4, rely=0.9, anchor="center")
        self.btn_reject.place(relx=0.6, rely=0.9, anchor="center")
        self.btn_leave.place(relx=0.5, rely=0.95, anchor="center")

    def precompute_pairs(self):
        current_year = self.start_year

        while os.path.exists(self.onedrive_base) and os.path.exists(
                self.google_base) and not self.done and current_year >= self.end_year:
            dirs = [
                x for x in os.listdir(self.onedrive_base)
                if os.path.isdir(os.path.join(self.onedrive_base, x))
            ]
            dirs.sort(key=lambda x: months_test.index(x[:3]) if x[:3] in months_test else 9999)

            for d in dirs:
                onedrive_search_path = os.path.join(self.onedrive_base, d)
                google_search_path = os.path.join(self.google_base, d)

                if not os.path.exists(onedrive_search_path) or not os.path.exists(google_search_path):
                    print(f"Skipping directories: {onedrive_search_path} or {google_search_path} does not exist.")
                    continue

                onedrive_images = [
                    x for x in os.listdir(onedrive_search_path)
                    if os.path.isfile(os.path.join(onedrive_search_path, x))
                ]
                google_images = [
                    x for x in os.listdir(google_search_path)
                    if os.path.isfile(os.path.join(google_search_path, x))
                ]

                for onedrive_image in onedrive_images:
                    onedrive_image_path = os.path.join(onedrive_search_path, onedrive_image)

                    onedrive_gray = read_and_resize_image_for_ssim(onedrive_image_path)
                    if onedrive_gray is None:
                        continue

                    for google_image in google_images:
                        google_image_path = os.path.join(google_search_path, google_image)

                        if not os.path.exists(onedrive_image_path) or not os.path.exists(google_image_path):
                            print(
                                f"Skipping comparison as one of the files: {onedrive_image_path} or {google_image_path} is missing")
                            continue

                        google_gray = read_and_resize_image_for_ssim(google_image_path)
                        if google_gray is None:
                            continue

                        try:
                            score, _ = ssim(onedrive_gray, google_gray, full=True)
                            if score >= similarity_threshold:
                                del_img = google_image if self.delete_from_google else onedrive_image
                                self.queue.put((onedrive_image_path, google_image_path, score, del_img))
                        except Exception as e:
                            print(f"Error calculating SSIM between '{onedrive_image_path}' and '{google_image_path}': {e}")
                            continue

            current_year -= 1
            self.onedrive_base = os.path.join("./OneDrive", str(current_year))
            self.google_base = os.path.join("./Google", str(current_year))

        self.queue.put(None)


# Adjust these variables as needed
start_year = 2025
end_year = 0  # Set to 0 to delete all years, can adjust to stop at a specific year

delete_from_google = True  # True to delete from Google, False for OneDrive
onedrive_main_path = f"./OneDrive/{start_year}"
google_main_path = f"./Google/{start_year}"

confirm_delete = True
root = tk.Tk()
root.geometry("700x600+200+100")
root.title("Image Comparison")

app = ImageComparatorApp(
    root,
    start_year=start_year,
    end_year=end_year,
    onedrive_base=onedrive_main_path,
    google_base=google_main_path,
    delete_from_google=delete_from_google,
    confirm_delete=confirm_delete
)

root.mainloop()
