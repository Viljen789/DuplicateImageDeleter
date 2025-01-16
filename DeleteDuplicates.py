import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from skimage.metrics import structural_similarity as ssim
import threading
import queue

# Adjust these variables as necessary
similarityThreshold = 0.5  # Can change to make it more/less sensitive
resizeSize = (512, 512)  # Size for SSIM calculation
displayMaxSize = (300, 300)  # GUI size

monthsEN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
monthsNO = [
    "Januar", "Februar", "Mars", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Desember"
]
monthsTest = [x[:3] for x in monthsEN[:4]]  # ["Jan","Feb","Mar","Apr"]

resizedCache = {}  # Dict from path -> grayscale image
done = False

def readAndResizeImageForSSIM(path, size=resizeSize):
    global resizedCache
    if path in resizedCache:
        return resizedCache[path]

    if not os.path.exists(path):
        return None

    try:
        pilImg = Image.open(path)
        pilGray = pilImg.convert("L")
        pilGray = pilGray.resize(size, resample=Image.Resampling.LANCZOS)
        arr = np.array(pilGray)
        resizedCache[path] = arr
        return arr
    except Exception as e:
        print(f"Error reading/resizing '{path}': {e}")
        return None


def rescaleImageForDisplay(pilImage, maxWidth=300, maxHeight=300):
    width, height = pilImage.size
    if width > maxWidth or height > maxHeight:
        ratio = min(maxWidth / width, maxHeight / height)
        newW = int(width * ratio)
        newH = int(height * ratio)
        return pilImage.resize((newW, newH), Image.Resampling.LANCZOS)
    return pilImage


class ImageComparatorApp:
    def __init__(
            self,
            root,
            startYear,
            endYear,
            oneDriveBase,
            googleBase,
            deleteFromGoogle=True,
            confirmDelete=False
    ):
        self.root = root
        self.startYear = startYear
        self.endYear = endYear
        self.oneDriveBase = oneDriveBase
        self.googleBase = googleBase
        self.deleteFromGoogle = deleteFromGoogle
        self.confirmDelete = confirmDelete
        self.done = False

        self.imagePairs = []
        self.currentIndex = 0
        self.currentPair = None
        self.currentPairPath = None
        self.currentDelImg = None

        self.setupGui()
        self.queue = queue.Queue()

        self.precomputeThread = threading.Thread(target=self.precomputePairs)
        self.precomputeThread.daemon = True
        self.precomputeThread.start()

        self.root.after(100, self.checkQueue)

    def setupGui(self):
        self.root.geometry("700x600+200+100")

        self.topLabelText = tk.StringVar(value="No image pairs loaded.")
        self.topLabel = tk.Label(self.root, textvariable=self.topLabelText, font=("Helvetica", 14))
        self.topLabel.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=500, mode='determinate')
        self.progress.pack(pady=10)
        self.progress['value'] = 0

        self.frameImages = tk.Frame(self.root)
        self.frameImages.pack(pady=5)
        self.gLabel = tk.Label(self.frameImages)
        self.gLabel.grid(row=0, column=0, padx=10)
        self.odLabel = tk.Label(self.frameImages)
        self.odLabel.grid(row=0, column=1, padx=10)

        self.btnAccept = tk.Button(self.root, text="Keep", width=12, command=self.onAccept, state=tk.DISABLED)
        self.btnReject = tk.Button(self.root, text="Delete", width=12, command=self.onReject, state=tk.DISABLED)
        self.btnLeave = tk.Button(self.root, text="Stop Deleting", width=15, command=self.onLeave,
                                  state=tk.DISABLED)
        self.btnAccept.place(relx=0.4, rely=0.9, anchor="center")
        self.btnReject.place(relx=0.6, rely=0.9, anchor="center")
        self.btnLeave.place(relx=0.5, rely=0.95, anchor="center")

    def precomputePairs(self):
        curYear = self.startYear

        while os.path.exists(self.oneDriveBase) and os.path.exists(
                self.googleBase) and not self.done and curYear >= self.endYear:
            dirs = [
                x for x in os.listdir(self.oneDriveBase)
                if os.path.isdir(os.path.join(self.oneDriveBase, x))
            ]
            dirs.sort(key=lambda x: monthsTest.index(x[:3]) if x[:3] in monthsTest else 9999)

            for d in dirs:
                odSearchPath = os.path.join(self.oneDriveBase, d)
                gSearchPath = os.path.join(self.googleBase, d)

                if not os.path.exists(odSearchPath) or not os.path.exists(gSearchPath):
                    print(f"Skipping directories: {odSearchPath} or {gSearchPath} does not exist.")
                    continue

                odImages = [
                    x for x in os.listdir(odSearchPath)
                    if os.path.isfile(os.path.join(odSearchPath, x))
                ]
                gImages = [
                    x for x in os.listdir(gSearchPath)
                    if os.path.isfile(os.path.join(gSearchPath, x))
                ]

                for odImage in odImages:
                    odImagePath = os.path.join(odSearchPath, odImage)
                    odImageName = odImage

                    odGray = readAndResizeImageForSSIM(odImagePath)
                    if odGray is None:
                        continue

                    for gImage in gImages:
                        gImagePath = os.path.join(gSearchPath, gImage)
                        gImageName = gImage

                        if not os.path.exists(odImagePath) or not os.path.exists(gImagePath):
                            print(
                                f"Skipping comparison since at least one file is missing: {odImagePath} or {gImagePath}")
                            continue

                        gGray = readAndResizeImageForSSIM(gImagePath)
                        if gGray is None:
                            continue

                        try:
                            score, _ = ssim(odGray, gGray, full=True)
                            if score >= similarityThreshold:
                                delImg = gImageName if self.deleteFromGoogle else odImageName
                                self.queue.put((odImagePath, gImagePath, odImageName, gImageName, score, delImg))
                        except Exception as e:
                            print(f"Error calculating SSIM between '{odImagePath}' and '{gImagePath}': {e}")
                            continue

            curYear -= 1
            self.oneDriveBase = os.path.join("./OneDrive", str(curYear))
            self.googleBase = os.path.join("./Google", str(curYear))

        self.queue.put(None)

    def checkQueue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item is None:
                    self.progress['value'] = 100
                    print("Precomputation finished.")
                    break
                odImagePath, gImagePath, odImageName, gImageName, score, delImg = item
                self.imagePairs.append((odImagePath, gImagePath, odImageName, gImageName, score, delImg))
                self.progress['value'] += 1
                self.progress.update()
                if len(self.imagePairs) == 1 and not self.done:
                    self.currentPair = self.imagePairs[0]
                    self.currentIndex = 1
                    self.currentPairPath = self.currentPair[1] if self.deleteFromGoogle else self.currentPair[0]
                    self.currentDelImg = self.currentPair[5]
                    self.loadPair(self.currentPair)
        except queue.Empty:
            pass
        finally:
            if not self.done:
                self.root.after(100, self.checkQueue)

    def loadNextPair(self):
        if self.done:
            return

        if self.currentIndex >= len(self.imagePairs):
            self.topLabelText.set("No more image pairs to compare.")
            self.gLabel.config(image="")
            self.odLabel.config(image="")
            self.btnAccept.config(state=tk.DISABLED)
            self.btnReject.config(state=tk.DISABLED)
            self.btnLeave.config(state=tk.DISABLED)
            self.root.title("Image Comparison")
            return

        self.currentPair = self.imagePairs[self.currentIndex]
        odImagePath, gImagePath, odImageName, gImageName, score, delImg = self.currentPair
        self.currentPairPath = gImagePath if self.deleteFromGoogle else odImagePath
        self.currentDelImg = delImg

        self.loadPair(self.currentPair)
        self.currentIndex += 1

    def loadPair(self, pair):
        odImagePath, gImagePath, odImageName, gImageName, score, delImg = pair

        self.root.title(f"{odImageName} vs {gImageName} — SSIM: {score:.3f}")
        self.topLabelText.set(
            f"{'/'.join(odImagePath.split('/')[-3:-1])} {odImageName} vs {gImageName} — SSIM: {score:.3f}")

        try:
            gPilImage = Image.open(gImagePath)
            odPilImage = Image.open(odImagePath)
            gPilImage = rescaleImageForDisplay(gPilImage, *displayMaxSize)
            odPilImage = rescaleImageForDisplay(odPilImage, *displayMaxSize)
            gTkImage = ImageTk.PhotoImage(gPilImage)
            odTkImage = ImageTk.PhotoImage(odPilImage)

            self.gLabel.config(image=gTkImage)
            self.gLabel.image = gTkImage
            self.odLabel.config(image=odTkImage)
            self.odLabel.image = odTkImage

            self.btnAccept.config(state=tk.NORMAL)
            self.btnReject.config(state=tk.NORMAL)
            self.btnLeave.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Error loading images for display: {e}")
            self.gLabel.config(image="")
            self.odLabel.config(image="")

    def onAccept(self):
        if self.currentPairPath:
            print(f"Keeping image: {self.currentPairPath}")
        self.loadNextPair()

    def onReject(self):
        if not self.currentPairPath:
            return

        result = True
        if self.confirmDelete:
            result = self.confirmClick()

        if result or not self.confirmDelete:
            if os.path.exists(self.currentPairPath):
                try:
                    os.remove(self.currentPairPath)
                    print(f"Deleted image: {self.currentDelImg}")
                    self.removeAllPairsWithPath(self.currentPairPath)
                except Exception as e:
                    print(f"Error deleting '{self.currentPairPath}': {e}")
            else:
                print(f"File not found: {self.currentPairPath}")
            self.loadNextPair()

    def onLeave(self):
        self.stopDeleting()

    def confirmClick(self):
        confirmWindow = tk.Toplevel(self.root)
        confirmWindow.title("Confirm Choice")
        confirmWindow.geometry("300x200")
        confirmWindow.transient(self.root)
        confirmWindow.grab_set()

        label = tk.Label(confirmWindow, text="Are you sure you want to delete the image?")
        label.pack(pady=10)
        result = tk.StringVar()

        def setResult(value):
            result.set(value)
            confirmWindow.destroy()

        acc = tk.Button(confirmWindow, text="Confirm", command=lambda: setResult("Y"))
        rej = tk.Button(confirmWindow, text="Cancel", command=lambda: setResult("N"))
        acc.pack(pady=10)
        rej.pack(pady=10)

        self.root.wait_window(confirmWindow)
        return result.get() == "Y"

    def removeAllPairsWithPath(self, path):
        originalLength = len(self.imagePairs)
        self.imagePairs = [pair for pair in self.imagePairs if pair[0] != path and pair[1] != path]
        removedCount = originalLength - len(self.imagePairs)
        print(f"Removed {removedCount} pairs containing '{path}'.")

    def stopDeleting(self):
        print("Stopping deletion")
        self.done = True
        self.root.quit()


# Adjust these variables as necessary
startYear = 2025
endYear = 0  # Set to 0 to delete all years, can change to limit up to a specific year
deleteFromGoogle = True  # True to delete from Google, False to delete from OneDrive
odMainPath = f"./OneDrive/{startYear}"  # Replace with "C:/Users/user/OneDrive" etc.
gMainPath = f"./Google/{startYear}"  # Same as above, e.g., "C:/Users/user/Google"

confirm = True  # Set to True to require confirmation before deletion

root = tk.Tk()
root.geometry("700x600+200+100")
root.title("Image Comparison")

app = ImageComparatorApp(
    root,
    startYear=startYear,
    endYear=endYear,
    oneDriveBase=odMainPath,
    googleBase=gMainPath,
    deleteFromGoogle=deleteFromGoogle,
    confirmDelete=confirm
)

root.mainloop()
