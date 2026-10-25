import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2
import serial
import subprocess
import os
import threading
import time

class SobelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Vicharak Shrike Lite - FPGA Studio")
        self.root.geometry("720x860")
        self.root.config(bg="#0f172a")
        self.root.resizable(True, True)

        # File paths 
        self.bitstream_path = "FPGA_bitstream_MCU.bin" if os.path.exists("FPGA_bitstream_MCU.bin") else None
        self.script_path = "main.py" if os.path.exists("main.py") else ("sorbel.py" if os.path.exists("sorbel.py") else None)
        self.image_path = None
        
        self.serial_port = "COM3"
        self.baud_rate = 115200
        self.is_streaming = False
        self.serial_thread = None
        self.tk_stream_img = None
        self.tk_preview = None
        
        os.makedirs("output_results", exist_ok=True)
        self.setup_ui()

    def setup_ui(self):
        # --- Header ---
        header_frame = tk.Frame(self.root, bg="#0f172a")
        header_frame.pack(fill="x", padx=20, pady=12)
        
        tk.Label(header_frame, text="⚡ FPGA Edge Detection", font=("Segoe UI", 16, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w")
        tk.Label(header_frame, text="Vicharak Shrike Lite Hardware Dashboard", font=("Segoe UI", 9), fg="#94a3b8", bg="#0f172a").pack(anchor="w")

        # --- Card 1: Project & File Configuration ---
        card_files = tk.LabelFrame(self.root, text=" 1. Project & File Management ", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#1e293b", bd=1, relief="solid", padx=15, pady=12)
        card_files.pack(fill="x", padx=20, pady=6)

        # Bitstream Row
        tk.Button(card_files, text="Select Bitstream", command=self.browse_bitstream, width=18, bg="#334155", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").grid(row=0, column=0, padx=5, pady=4)
        self.lbl_bitstream = tk.Label(card_files, text=os.path.basename(self.bitstream_path) if self.bitstream_path else "Not detected", fg="#4ade80" if self.bitstream_path else "#94a3b8", bg="#1e293b", anchor="w", width=42, font=("Segoe UI", 9))
        self.lbl_bitstream.grid(row=0, column=1, padx=5, pady=4)

        # Script Row
        tk.Button(card_files, text="Select Script", command=self.browse_script, width=18, bg="#334155", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").grid(row=1, column=0, padx=5, pady=4)
        self.lbl_script = tk.Label(card_files, text=os.path.basename(self.script_path) if self.script_path else "Not detected", fg="#4ade80" if self.script_path else "#94a3b8", bg="#1e293b", anchor="w", width=42, font=("Segoe UI", 9))
        self.lbl_script.grid(row=1, column=1, padx=5, pady=4)

        # Image Row
        tk.Button(card_files, text="Select Input Image", command=self.browse_image, width=18, bg="#059669", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").grid(row=2, column=0, padx=5, pady=4)
        self.lbl_image = tk.Label(card_files, text="No image selected", fg="#94a3b8", bg="#1e293b", anchor="w", width=42, font=("Segoe UI", 9))
        self.lbl_image.grid(row=2, column=1, padx=5, pady=4)

        # Preview & Upload Sub-grid
        preview_frame = tk.Frame(card_files, bg="#1e293b")
        preview_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.preview_canvas = tk.Canvas(preview_frame, width=160, height=96, bg="#0f172a", highlightthickness=1, highlightbackground="#334155")
        self.preview_canvas.pack(side="left", padx=10)

        action_sub_frame = tk.Frame(preview_frame, bg="#1e293b")
        action_sub_frame.pack(side="left", padx=10)

        tk.Label(action_sub_frame, text="Target Matrix:\n80 x 48 Pixels", fg="#94a3b8", bg="#1e293b", font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=5)
        
        self.btn_upload = tk.Button(action_sub_frame, text="🚀 Flash All to Board", command=self.upload_all_files, width=22, bg="#2563eb", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", state="disabled", cursor="hand2")
        self.btn_upload.pack(anchor="w", pady=5)

        # --- Card 2: Serial Link & Communication ---
        card_serial = tk.LabelFrame(self.root, text=" 2. Hardware Communication Link ", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#1e293b", bd=1, relief="solid", padx=15, pady=10)
        card_serial.pack(fill="x", padx=20, pady=6)

        serial_inner = tk.Frame(card_serial, bg="#1e293b")
        serial_inner.pack(fill="x")

        tk.Label(serial_inner, text="COM Port:", fg="#f8fafc", bg="#1e293b", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        self.port_entry = tk.Entry(serial_inner, width=12, font=("Segoe UI", 10), bg="#0f172a", fg="white", insertbackground="white", relief="solid", bd=1)
        self.port_entry.insert(0, "COM3")
        self.port_entry.pack(side="left", padx=5)

        self.btn_stream = tk.Button(serial_inner, text="▶ Start Real-Time Stream", command=self.toggle_stream, width=25, bg="#d97706", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2")
        self.btn_stream.pack(side="right", padx=5)

        # --- Card 3: Live Output View ---
        card_output = tk.LabelFrame(self.root, text=" 3. Real-Time FPGA Sobel Output ", font=("Segoe UI", 10, "bold"), fg="#38bdf8", bg="#1e293b", bd=1, relief="solid", padx=15, pady=10)
        card_output.pack(fill="both", expand=True, padx=20, pady=6)

        canvas_container = tk.Frame(card_output, bg="#1e293b")
        canvas_container.pack(pady=4)

        self.stream_canvas = tk.Canvas(canvas_container, width=400, height=210, bg="#0b0f19", highlightthickness=2, highlightbackground="#334155")
        self.stream_canvas.pack()

        # --- Status Bar ---
        self.lbl_status = tk.Label(self.root, text="● System Ready. Please verify files and connect.", fg="#38bdf8", bg="#0f172a", font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_status.pack(fill="x", padx=20, pady=6)

        # Run initial check to enable upload if auto-detected
        self.check_enable_upload()

    def browse_bitstream(self):
        path = filedialog.askopenfilename(filetypes=[("Binary Files", "*.bin")])
        if path:
            self.bitstream_path = path
            self.lbl_bitstream.config(text=os.path.basename(path), fg="#4ade80")
            self.check_enable_upload()

    def browse_script(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            self.script_path = path
            self.lbl_script.config(text=os.path.basename(path), fg="#4ade80")
            self.check_enable_upload()

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            self.image_path = path
            self.lbl_image.config(text=os.path.basename(path), fg="#4ade80")
            
            # Preview 80x48 image scaled up
            img = Image.open(path).convert("L").resize((80, 48))
            img_disp = img.resize((160, 96), Image.Resampling.NEAREST)
            self.tk_preview = ImageTk.PhotoImage(img_disp)
            self.preview_canvas.create_image(0, 0, anchor="nw", image=self.tk_preview)
            
            self.check_enable_upload()

    def check_enable_upload(self):
        if self.image_path and self.bitstream_path and self.script_path:
            self.btn_upload.config(state="normal", bg="#2563eb")
        else:
            self.btn_upload.config(state="disabled", bg="#475569")

    def upload_all_files(self):
        try:
            img = Image.open(self.image_path).convert("L").resize((80, 48))
            with open("bimage.bin", "wb") as f:
                f.write(img.tobytes())

            self.lbl_status.config(text="⏳ Status: Converting image & flashing files to Shrike Lite...", fg="#fbbf24")
            self.root.update()

            # Push Bitstream
            res1 = subprocess.run(["mpremote", "cp", self.bitstream_path, ":FPGA_bitstream_MCU.bin"], capture_output=True, text=True)
            if res1.returncode != 0:
                raise Exception(f"Failed to upload bitstream:\n{res1.stderr}")

            # Push Script as main.py
            res2 = subprocess.run(["mpremote", "cp", self.script_path, ":main.py"], capture_output=True, text=True)
            if res2.returncode != 0:
                raise Exception(f"Failed to upload script:\n{res2.stderr}")

            # Push Image Binary
            res3 = subprocess.run(["mpremote", "cp", "bimage.bin", ":bimage.bin"], capture_output=True, text=True)
            if res3.returncode != 0:
                raise Exception(f"Failed to upload image binary:\n{res3.stderr}")

            self.lbl_status.config(text="✔ Status: All files flashed successfully! Press board RESET button.", fg="#4ade80")
            messagebox.showinfo("Success", "Bitstream, main.py, and bimage.bin uploaded successfully!\n\nPress the hardware RESET button on your Shrike Lite board now.")

        except Exception as e:
            messagebox.showerror("Upload Error", str(e))
            self.lbl_status.config(text="✖ Status: Flash upload failed.", fg="#f87171")

    def toggle_stream(self):
        if not self.is_streaming:
            self.serial_port = self.port_entry.get()
            self.is_streaming = True
            self.btn_stream.config(text="⏹ Stop Real-Time Stream", bg="#dc2626")
            self.serial_thread = threading.Thread(target=self.stream_worker, daemon=True)
            self.serial_thread.start()
        else:
            self.is_streaming = False
            self.btn_stream.config(text="▶ Start Real-Time Stream", bg="#d97706")
            self.lbl_status.config(text="● Status: Stream stopped.", fg="#38bdf8")

    def stream_worker(self):
        IMAGE_WIDTH = 80
        IMAGE_HEIGHT = 46
        EXPECTED_BYTES = 3680

        try:
            ser = serial.Serial(self.serial_port, self.baud_rate, timeout=0.5)
            self.lbl_status.config(text=f"● Status: Connected to {self.serial_port}. Receiving live stream...", fg="#4ade80")
        except Exception as e:
            self.lbl_status.config(text=f"✖ Status: Serial Error: {e}", fg="#f87171")
            self.is_streaming = False
            self.btn_stream.config(text="▶ Start Real-Time Stream", bg="#d97706")
            return

        raw_stream_buffer = bytearray()
        frame_count = 0

        while self.is_streaming:
            data = ser.read(2048)
            if data:
                raw_stream_buffer.extend(data)
                
                if b"START_FRAME" in raw_stream_buffer and b"END_FRAME" in raw_stream_buffer:
                    start_idx = raw_stream_buffer.find(b"START_FRAME") + len(b"START_FRAME")
                    end_idx = raw_stream_buffer.find(b"END_FRAME")
                    
                    pixel_payload = raw_stream_buffer[start_idx:end_idx]
                    
                    if len(pixel_payload) == EXPECTED_BYTES:
                        img_np = np.frombuffer(pixel_payload, dtype=np.uint8)
                        aligned_pixels = np.roll(img_np, -2)
                        img_gray = aligned_pixels.reshape((IMAGE_HEIGHT, IMAGE_WIDTH))
                        
                        scaled_img = cv2.resize(img_gray, (400, 210), interpolation=cv2.INTER_NEAREST)
                        self.root.after(0, lambda img=scaled_img: self.update_canvas(img))
                        
                        frame_count += 1
                        if frame_count % 30 == 0:
                            filename = f"output_results/edge_frame_{int(time.time())}.png"
                            cv2.imwrite(filename, scaled_img)
                            
                    raw_stream_buffer = raw_stream_buffer[end_idx + len(b"END_FRAME"):]

        ser.close()

    def update_canvas(self, scaled_img):
        img_pil = Image.fromarray(scaled_img)
        self.tk_stream_img = ImageTk.PhotoImage(img_pil)
        self.stream_canvas.delete("all")
        self.stream_canvas.create_image(0, 0, anchor="nw", image=self.tk_stream_img)

if __name__ == "__main__":
    root = tk.Tk()
    app = SobelGUI(root)
    root.mainloop()