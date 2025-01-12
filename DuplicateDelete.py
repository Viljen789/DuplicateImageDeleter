import os
import tkinter as tk
import cv2
from PIL import Image, ImageTk
from skimage.metrics import structural_similarity as ssim


def click_accept(path, root):
    print(f"Beholder bildet: {path}")
    root.destroy()


def confirm_click(root):
    confirmwindow = tk.Toplevel(root)
    confirmwindow.title("Bekreft valg")
    confirmwindow.geometry("300x200")
    label = tk.Label(confirmwindow, text="Sikker på at du vil slette bildet?")
    label.pack(pady=10)
    result = tk.StringVar()

    def set_result(value):
        result.set(value)
        confirmwindow.destroy()
        root.destroy()

    acc = tk.Button(
        confirmwindow,
        text="Bekreft",
        command=lambda: set_result("Y")
    )
    rej = tk.Button(
        confirmwindow,
        text="Avbryt",
        command=confirmwindow.destroy
    )
    acc.pack(pady=10)
    rej.pack(pady=10)
    confirmwindow.mainloop()
    return result.get() == "Y"


def click_reject(path, root, delImg):
    global confirm, DeleteFromGoogle, ODImages, GImages
    result = True
    if confirm:
        result = confirm_click(root)

    if result or not confirm:
        if os.path.exists(path):  # Ensure file exists before attempting deletion
            os.remove(path)
            if DeleteFromGoogle:
                if delImg in GImages:  # Remove from GImages if it exists
                    GImages.remove(delImg)
            else:
                if delImg in ODImages:  # Remove from ODImages if it exists
                    ODImages.remove(delImg)
            print(f"Sletta bilde: {delImg}")
        else:
            print(f"Fil ikke funnet: {path}")
        root.destroy()


def stopdeleting(root):
    print("Avbryter sletting")
    global done
    done = True
    root.destroy()


def cancel(root):
    leavewindow = tk.Toplevel(root)
    leavewindow.title("Bekreft avbryting")
    leavewindow.geometry("300x200")
    label = tk.Label(leavewindow, text="Sikker på at du vil stikke?")
    label.pack(pady=10)
    accept = tk.Button(
        leavewindow,
        text="Forlat slettingen",
        command=lambda: stopdeleting(root),
    )
    reject = tk.Button(
        leavewindow,
        text="Avbryt",
        command=leavewindow.destroy,
    )
    accept.pack(pady=10)
    reject.pack(pady=10)
    leavewindow.mainloop()


def main(oneDriveMainPath, googleMainPath, DeleteFromGoogle, startyear, endyear):
    while os.path.exists(oneDriveMainPath) and os.path.exists(googleMainPath) and not done and startyear > endyear:
        dirs = [
            x
            for x in os.listdir(oneDriveMainPath)
            if os.path.isdir(os.path.join(oneDriveMainPath, x))
        ]
        dirs.sort(key=lambda x: monthsTest.index(x))  # Change to monthsEN or monthsNO for full months
        # dirs.sort(key=lambda x: monthsEN.index(x))
        # dirs.sort(key=lambda x: monthsNO.index(x))
        for dir in dirs:
            ODSearchPath = f"./OneDrive/{startyear}/{dir}"
            GSearchPath = f"./Google/{startyear}/{dir}"

            ODImages = [
                x
                for x in os.listdir(ODSearchPath)
                if os.path.isfile(os.path.join(ODSearchPath, x))
            ]
            GImages = [
                x
                for x in os.listdir(GSearchPath)
                if os.path.isfile(os.path.join(GSearchPath, x))
            ]
            for ODImage in ODImages:
                ODImageName = ODImage
                ODImagePath = f"./OneDrive/{startyear}/{dir}/{ODImage}"
                ODImage = cv2.imread(
                    f"./OneDrive/{startyear}/{dir}/{ODImage}", cv2.IMREAD_GRAYSCALE
                )
                for GImage in GImages:
                    GImageName = GImage
                    GImagePath = f"./Google/{startyear}/{dir}/{GImage}"
                    if not os.path.exists(ODImagePath) or not os.path.exists(GImagePath):
                        print(
                            f"Hopper over sammenligning siden minst en av filene: {ODImagePath} eller {GImagePath} mangler")
                        continue
                    GImage = cv2.imread(
                        f"./Google/{startyear}/{dir}/{GImage}", cv2.IMREAD_GRAYSCALE
                    )
                    try:
                        score, diff = ssim(ODImage, GImage, full=True)
                        if score > 0.95:
                            delImg = GImageName if DeleteFromGoogle else ODImageName
                            root = tk.Tk()
                            root.geometry("500x700+200+100")
                            root.title(f"{dir} {startyear} {GImageName} {ODImageName}")
                            Gpil_image = Image.open(GImagePath)
                            ODpil_image = Image.open(ODImagePath)
                            Gtk_image = ImageTk.PhotoImage(Gpil_image)
                            ODtk_image = ImageTk.PhotoImage(ODpil_image)
                            Glabel = tk.Label(root, image=Gtk_image)
                            ODlabel = tk.Label(root, image=ODtk_image)
                            Glabel.place(x=100, y=50)
                            ODlabel.place(x=100, y=300)

                            # Buttons with fixed placement
                            accept = tk.Button(
                                root,
                                text="Behold",
                                command=lambda: click_accept(GImagePath, root),
                            )
                            reject = tk.Button(
                                root,
                                text="Slett",
                                command=lambda: click_reject(GImagePath, root, delImg),
                            )
                            leave = tk.Button(
                                root, text="Forlat sletting", command=lambda: cancel(root)
                            )

                            # Place buttons at specific positions
                            accept.place(relx=0.4, rely=0.8, anchor="center")
                            reject.place(relx=0.6, rely=0.8, anchor="center")
                            leave.place(relx=0.5, rely=0.9, anchor="center")
                            root.mainloop()
                            if done:
                                return
                            # print(GImageName, ODImageName)
                            # print(f"Likhetsscore mellom {ODImageName} og {GImageName}: {score}")
                            print(GImages)
                    except:
                        pass
        startyear -= 1
        googleMainPath = f"./Google/{startyear}"
        oneDriveMainPath = f"./OneDrive/{startyear}"


done = False
ODImages = []
GImages = []
monthsNO = ["Januar", "Februar", "Mars", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November",
            "Desember"]
monthsEN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "Desember"]
monthsTest = [x[:3] for x in monthsEN[:4]]
startyear = 2025

endyear = 0  # Sett til 0 for å slette alle år, kan endres for å maks gå til og med ett bestemt år
DeleteFromGoogle = True  # True for å slette fra Google, False for å slette fra OneDrive
oneDriveMainPath = f"./OneDrive/{startyear}"  # Bytt ut alt fram til /startyear med "C:/Users/bruker/OneDrive" elns
googleMainPath = f"./Google/{startyear}"  # Samme som over,  "C:/Users/bruker/Google" elns

confirm = False  # Bekreftelse på sletting

main(oneDriveMainPath, googleMainPath, DeleteFromGoogle,
     startyear=startyear, endyear=endyear)
