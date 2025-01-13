import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from skimage.metrics import structural_similarity as ssim
import threading
import queue

# Konfigurasjon
similarityThreshold = 0.5  # Kan endre om den skal være meir/mindre sensitiv
resizeSize = (512, 512)  # Størresle for SSIM-beregning
displayMaxSize = (300, 300)  # GUI størrelse
monthsEN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
monthsNO = [
    "Januar", "Februar", "Mars", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Desember"
]
monthsTest = [x[:3] for x in monthsEN[:4]]  # ["Jan","Feb","Mar","Apr"]

resizedCache = {}  # Dict fra path -> grayscale bilde


def lesOgResizeBildeForSsim(path, size=resizeSize):
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
        print(f"Feil ved lesing/resizing av '{path}': {e}")
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

        self.topLabelText = tk.StringVar(value="Ingen bildepar lastet.")
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

        self.btnAccept = tk.Button(self.root, text="Behold", width=12, command=self.onAccept, state=tk.DISABLED)
        self.btnReject = tk.Button(self.root, text="Slett", width=12, command=self.onReject, state=tk.DISABLED)
        self.btnLeave = tk.Button(self.root, text="Forlat slettingen", width=15, command=self.onLeave,
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
                ODSearchPath = os.path.join(self.oneDriveBase, d)
                GSearchPath = os.path.join(self.googleBase, d)

                if not os.path.exists(ODSearchPath) or not os.path.exists(GSearchPath):
                    print(f"Hopper over mapper: {ODSearchPath} eller {GSearchPath} finnes ikke.")
                    continue

                ODImages = [
                    x for x in os.listdir(ODSearchPath)
                    if os.path.isfile(os.path.join(ODSearchPath, x))
                ]
                GImages = [
                    x for x in os.listdir(GSearchPath)
                    if os.path.isfile(os.path.join(GSearchPath, x))
                ]

                for ODImage in ODImages:
                    ODImagePath = os.path.join(ODSearchPath, ODImage)
                    ODImageName = ODImage

                    odGray = lesOgResizeBildeForSsim(ODImagePath)
                    if odGray is None:
                        continue

                    for GImage in GImages:
                        GImagePath = os.path.join(GSearchPath, GImage)
                        GImageName = GImage

                        if not os.path.exists(ODImagePath) or not os.path.exists(GImagePath):
                            print(
                                f"Hopper over sammenligning siden minst en av filene: {ODImagePath} eller {GImagePath} mangler")
                            continue

                        gGray = lesOgResizeBildeForSsim(GImagePath)
                        if gGray is None:
                            continue

                        try:
                            score, _ = ssim(odGray, gGray, full=True)
                            if score >= similarityThreshold:
                                delImg = GImageName if self.deleteFromGoogle else ODImageName
                                self.queue.put((ODImagePath, GImagePath, ODImageName, GImageName, score, delImg))
                        except Exception as e:
                            print(f"Feil ved beregning av SSIM mellom '{ODImagePath}' og '{GImagePath}': {e}")
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
                    print("Prekomputering ferdig.")
                    break
                ODImagePath, GImagePath, ODImageName, GImageName, score, delImg = item
                self.imagePairs.append((ODImagePath, GImagePath, ODImageName, GImageName, score, delImg))
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
            self.topLabelText.set("Ingen flere bildepar å sammenligne.")
            self.gLabel.config(image="")
            self.odLabel.config(image="")
            self.btnAccept.config(state=tk.DISABLED)
            self.btnReject.config(state=tk.DISABLED)
            self.btnLeave.config(state=tk.DISABLED)
            self.root.title("Image Comparison")
            return

        self.currentPair = self.imagePairs[self.currentIndex]
        ODImagePath, GImagePath, ODImageName, GImageName, score, delImg = self.currentPair
        self.currentPairPath = GImagePath if self.deleteFromGoogle else ODImagePath
        self.currentDelImg = delImg

        self.loadPair(self.currentPair)
        self.currentIndex += 1

    def loadPair(self, pair):
        ODImagePath, GImagePath, ODImageName, GImageName, score, delImg = pair

        self.root.title(f"{ODImageName} vs {GImageName} — SSIM: {score:.3f}")
        self.topLabelText.set(
            f"{"/".join(ODImagePath.split("/")[-3:-1])} {ODImageName} vs {GImageName} — SSIM: {score:.3f}")

        try:
            GpilImage = Image.open(GImagePath)
            ODpilImage = Image.open(ODImagePath)
            GpilImage = rescaleImageForDisplay(GpilImage, *displayMaxSize)
            ODpilImage = rescaleImageForDisplay(ODpilImage, *displayMaxSize)
            GtkImage = ImageTk.PhotoImage(GpilImage)
            ODtkImage = ImageTk.PhotoImage(ODpilImage)

            self.gLabel.config(image=GtkImage)
            self.gLabel.image = GtkImage
            self.odLabel.config(image=ODtkImage)
            self.odLabel.image = ODtkImage

            self.btnAccept.config(state=tk.NORMAL)
            self.btnReject.config(state=tk.NORMAL)
            self.btnLeave.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Feil ved lasting av bilder for visning: {e}")
            self.gLabel.config(image="")
            self.odLabel.config(image="")

    def onAccept(self):
        if self.currentPairPath:
            print(f"Beholder bildet: {self.currentPairPath}")
        self.loadNextPair()

    def onReject(self):
        if not self.currentPairPath:
            return

        resultat = True
        if self.confirmDelete:
            resultat = self.confirmClick()

        if resultat or not self.confirmDelete:
            if os.path.exists(self.currentPairPath):
                try:
                    os.remove(self.currentPairPath)
                    print(f"Sletta bilde: {self.currentDelImg}")
                    self.removeAllPairsWithPath(self.currentPairPath)
                except Exception as e:
                    print(f"Feil ved sletting av '{self.currentPairPath}': {e}")
            else:
                print(f"Fil ikke funnet: {self.currentPairPath}")
            self.loadNextPair()

    def onLeave(self):
        self.stopDeleting()

    def confirmClick(self):
        confirmWindow = tk.Toplevel(self.root)
        confirmWindow.title("Bekreft valg")
        confirmWindow.geometry("300x200")
        confirmWindow.transient(self.root)
        confirmWindow.grab_set()

        label = tk.Label(confirmWindow, text="Sikker på at du vil slette bildet?")
        label.pack(pady=10)
        resultat = tk.StringVar()

        def settResultat(verdi):
            resultat.set(verdi)
            confirmWindow.destroy()

        acc = tk.Button(confirmWindow, text="Bekreft", command=lambda: settResultat("Y"))
        rej = tk.Button(confirmWindow, text="Avbryt", command=lambda: settResultat("N"))
        acc.pack(pady=10)
        rej.pack(pady=10)

        self.root.wait_window(confirmWindow)
        return resultat.get() == "Y"

    def removeAllPairsWithPath(self, path):
        originalLength = len(self.imagePairs)
        self.imagePairs = [pair for pair in self.imagePairs if pair[0] != path and pair[1] != path]
        removedCount = originalLength - len(self.imagePairs)
        print(f"Fjernet {removedCount} par som inneholdt '{path}'.")

    def stopDeleting(self):
        print("Avbryter sletting")
        self.done = True
        self.root.quit()


# Juster disse variablene etter behov
startYear = 2025
endYear = 0  # Sett til 0 for å slette alle år, kan endres for å maks gå til og med ett bestemt år
deleteFromGoogle = True  # True for å slette fra Google, False for å slette fra OneDrive
ODMainPath = f"./OneDrive/{startYear}"  # Bytt ut med "C:/Users/bruker/OneDrive" elns.
GMainPath = f"./Google/{startYear}"  # Samme som over, f.eks. "C:/Users/bruker/Google"

confirm = False  # Sett til True for å kreve bekreftelse før sletting
done = False
root = tk.Tk()
root.geometry("700x600+200+100")
root.title("Image Comparison")

app = ImageComparatorApp(
    root,
    startYear=startYear,
    endYear=endYear,
    oneDriveBase=ODMainPath,
    googleBase=GMainPath,
    deleteFromGoogle=deleteFromGoogle,
    confirmDelete=confirm
)

root.mainloop()
