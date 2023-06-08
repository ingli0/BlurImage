import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk


class ImageBlurrer:
    def __init__(self, root):
        self.root = root
        self.image_path = ""
        self.image = None
        self.blur_spots = []
        self.spot_sizes = {}   
        self.is_erasing = False   
        self.draw_spot_size = tk.DoubleVar(value=10.0)
        self.blur_types = ["Gaussian", "Median"]
        self.selected_blur_type = tk.StringVar(value=self.blur_types[0])
        self.display_camera = False
        
        self.canvas = tk.Canvas(root, width=400, height=400)
        self.canvas.pack()

        self.button_load = tk.Button(root, text="Load Image", command=self.load_image)
        self.button_load.pack()

        self.button_done = tk.Button(root, text="Done", command=self.blur_image)
        self.button_done.pack()

        self.button_erase = tk.Button(root, text="Toggle Erase Mode", command=self.toggle_erase_mode)
        self.button_erase.pack()

        self.size_slider = ttk.Scale(root, from_=5, to=50, orient="horizontal", variable=self.draw_spot_size)
        self.size_slider.set(self.draw_spot_size.get())
        self.size_slider.pack()

        self.blur_type_dropdown = ttk.Combobox(root, values=self.blur_types, textvariable=self.selected_blur_type,
                                               state="readonly")
        self.blur_type_dropdown.pack()

        self.button_open_camera = tk.Button(root, text="Open Camera", command=self.open_camera)
        self.button_open_camera.pack()

        self.button_close_camera = tk.Button(root, text="Close Camera", command=self.close_camera)
        self.button_close_camera.pack()

        self.button_take_photo = tk.Button(root, text="Take Photo", command=self.take_photo)
        self.button_take_photo.pack()

        self.button_close_photo = tk.Button(root, text="Close Photo", command=self.close_photo, state=tk.DISABLED)
        self.button_close_photo.pack()
        self.button_load.pack(side="left")
        self.button_erase.pack(side="right")
        self.button_open_camera.pack(side="left")
        self.button_take_photo.pack(side="left")
        self.button_close_camera.pack(side="right")
        self.button_close_photo.pack(side="right")
        self.button_done.pack(side="left")
        self.button_reverse = tk.Button(root, text="Reverse Image", command=self.reverse_image)
        self.button_reverse.pack(side="left")

        self.blur_intensity = tk.DoubleVar(value=1.0)
        self.intensity_slider = ttk.Scale(root, from_=0.1, to=5.0, orient="horizontal", variable=self.blur_intensity)
        self.intensity_slider.pack()

        
        self.canvas.bind("<Button-1>", self.draw_spot)
        self.canvas.bind("<B1-Motion>", self.draw_spot)

    def load_image(self):
        self.image_path = filedialog.askopenfilename(
            filetypes=(("Image files", "*.jpg;*.jpeg;*.png"), ("All files", "*.*")))
        if self.image_path:
            self.image = cv2.imread(self.image_path)
            self.display_image()

    def reverse_image(self):
        if self.image is not None:
            self.image = cv2.flip(self.image, 1)   
            self.display_image()

    def display_image(self):
        if self.image is not None:
            img = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
            img = Image.fromarray(img)

            max_width = self.canvas.winfo_width()
            max_height = self.canvas.winfo_height()
             
            width_ratio = max_width / img.width
            height_ratio = max_height / img.height
            scale_ratio = min(width_ratio, height_ratio)

            new_width = int(img.width * scale_ratio)
            new_height = int(img.height * scale_ratio)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)

            img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img
             
            for spot in self.blur_spots:
                x, y = spot
                spot_size = self.spot_sizes[spot]
                self.draw_spot_oval(x, y, spot_size * self.blur_intensity.get())


    def draw_spot(self, event):
        if self.image is not None and not self.display_camera:
            x = int((event.x / self.canvas.winfo_width()) * self.image.shape[1])
            y = int((event.y / self.canvas.winfo_height()) * self.image.shape[0])

            if self.is_erasing:
                
                if self.blur_spots:
                    closest_spot = min(self.blur_spots,
                                       key=lambda spot: np.sqrt((spot[0] - x) ** 2 + (spot[1] - y) ** 2))
                    self.blur_spots.remove(closest_spot)
                    del self.spot_sizes[closest_spot]
            else:
                spot_size = self.draw_spot_size.get()
                self.blur_spots.append((x, y))
                self.spot_sizes[(x, y)] = spot_size

            self.canvas.delete("all")
            self.display_image()
            for spot in self.blur_spots:
                x, y = spot
                spot_size = self.spot_sizes[spot]
                self.draw_spot_oval(x, y, spot_size)

    def draw_spot_oval(self, x, y, spot_size):
        spot_size = int(spot_size)
        img_width = self.canvas.winfo_width()
        img_height = self.canvas.winfo_height()
        img_ratio = min(img_width / self.image.shape[1], img_height / self.image.shape[0])

        x_pos = int((x * img_ratio) - spot_size)
        y_pos = int((y * img_ratio) - spot_size)
        width = int(spot_size * 2 * img_ratio)
        height = int(spot_size * 2 * img_ratio)
        self.canvas.create_oval(x_pos, y_pos, x_pos + width, y_pos + height, fill="red")


    def toggle_erase_mode(self):
        self.is_erasing = not self.is_erasing
        if self.is_erasing:
            self.button_erase.configure(text="Disable Erase Mode")
        else:
            self.button_erase.configure(text="Enable Erase Mode")

    def blur_image(self):
        if self.image is not None:
            blur_intensity = self.intensity_slider.get()

            blurred_image = self.image.copy()

            for spot in self.blur_spots:
                x, y = spot
                spot_size = self.spot_sizes[spot]

                x_start = int(max(0, x - spot_size / 2))
                x_end = int(min(self.image.shape[1], x + spot_size / 2))
                y_start = int(max(0, y - spot_size / 2))
                y_end = int(min(self.image.shape[0], y + spot_size / 2))

                kernel_size = int(spot_size / 4)

                if self.selected_blur_type.get() == "Gaussian":
                    blurred_image[y_start:y_end, x_start:x_end] = cv2.GaussianBlur(
                        blurred_image[y_start:y_end, x_start:x_end], (kernel_size, kernel_size), 0)
                elif self.selected_blur_type.get() == "Median":
                    blurred_image[y_start:y_end, x_start:x_end] = cv2.medianBlur(
                        blurred_image[y_start:y_end, x_start:x_end], kernel_size)

            img = cv2.cvtColor(blurred_image, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
            img = Image.fromarray(img)

            max_width = self.canvas.winfo_width()
            max_height = self.canvas.winfo_height()

            width_ratio = max_width / img.width
            height_ratio = max_height / img.height
            scale_ratio = min(width_ratio, height_ratio)

            new_width = int(img.width * scale_ratio)
            new_height = int(img.height * scale_ratio)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)

            self.photo_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(max_width / 2, max_height / 2, anchor="center", image=self.photo_image)

    def open_camera(self):
        self.camera = cv2.VideoCapture(0)
        self.display_camera = True
        self.update_camera()

    def close_camera(self):
        if self.display_camera:
            self.display_camera = False
            self.camera.release()
            self.canvas.delete("all")

    def update_camera(self):
        if self.display_camera:
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = Image.fromarray(frame)
                frame.thumbnail((400, 400))
                frame = ImageTk.PhotoImage(frame)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=frame)
                self.canvas.image = frame
                self.canvas.after(15, self.update_camera)

    def take_photo(self):
        if self.display_camera:
            ret, frame = self.camera.read()
            if ret:
                self.image = frame.copy()
                self.close_camera()
                self.display_image()
                self.button_close_photo.config(state=tk.NORMAL)
                self.button_take_photo.config(state=tk.NORMAL)
                self.button_open_camera.config(state=tk.NORMAL)
                self.button_close_camera.config(state=tk.NORMAL)
                self.button_load.config(state=tk.NORMAL)
                self.button_done.config(state=tk.NORMAL)
                self.button_erase.config(state=tk.NORMAL)
                self.size_slider.config(state=tk.NORMAL)
                self.blur_type_dropdown.config(state=tk.NORMAL)
                
    def save_image(self, image):
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=(("PNG Image", "*.png"), ("JPEG Image", "*.jpg;*.jpeg"), ("All Files", "*.*")))
        if save_path:
            cv2.imwrite(save_path, image)
            print("Image saved successfully!")

    def close_photo(self):
        self.image = None
        self.canvas.delete("all")
        self.button_close_photo.config(state=tk.NORMAL)
        self.button_take_photo.config(state=tk.NORMAL)
        self.button_open_camera.config(state=tk.NORMAL)
        self.button_close_camera.config(state=tk.NORMAL)
        self.button_load.config(state=tk.NORMAL)
        self.button_done.config(state=tk.NORMAL)
        self.button_erase.config(state=tk.NORMAL)
        self.size_slider.config(state=tk.NORMAL)
        self.blur_type_dropdown.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Blur Image Project")
    image_blurrer = ImageBlurrer(root)
    root.mainloop()