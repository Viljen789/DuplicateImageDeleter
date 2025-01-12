import tkinter as tk
from PIL import Image, ImageTk

# Create the main Tkinter window
root = tk.Tk()
root.title("Display Image")

# Load the image using Pillow
image_path = "./Google/2025/Jan/Dog1.jpeg"
pil_image = Image.open(image_path)

# Convert the Pillow image to a Tkinter PhotoImage
tk_image = ImageTk.PhotoImage(pil_image)

# Create a label widget to display the image
label = tk.Label(root, image=tk_image)
label.pack()

# Run the Tkinter event loop
root.mainloop()
