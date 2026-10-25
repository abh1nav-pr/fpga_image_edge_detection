# ⚡ FPGA Image Edge detection

An end-to-end hardware-accelerated image processing project built for the **Vicharak Shrike Lite** FPGA development board. This project offloads real-time 2D spatial convolution (Sobel Edge Detection) to the onboard FPGA logic while providing a responsive desktop GUI to capture, flash, process, and stream edge-detected visual frames in real time over serial communication.

---

## 📌 Project Concept & Architecture

Modern image processing tasks such as edge detection demand significant computational power when executed sequentially on a CPU. This project implements a hybrid hardware/software architecture:

1. **Host PC GUI (Python/Tkinter):** Takes standard input images (`.jpg`, `.png`, `.bmp`), pre-processes them down to an $80 \times 48$ grayscale grid, and automatically packages and flashes the bitstream, MicroPython runtime code, and binary image data directly onto the MCU/FPGA board using `mpremote`.
2. **Microcontroller (RP2040 / MicroPython):** Manages file storage, streams pixel arrays line-by-line into the FPGA over high-speed hardware buses, and captures returning edge values.
3. **FPGA Accelerator (Verilog HDL):** Implements a dedicated hardware pipeline featuring line buffers, $3 \times 3$ sliding window generators, horizontal/vertical Sobel matrix operators ($G_x$ and $G_y$), gradient magnitude calculation ($|G_x| + |G_y|$), and thresholding.
4. **Real-Time Visualizer:** Live-streams calculated frame buffers back to the host GUI via UART for real-time visualization and automatic snapshot saving.

```
+-------------------+      mpremote / Serial      +---------------------------------+
|   Host PC GUI     |  ------------------------>  |   Vicharak Shrike Lite Board    |
| (Python/Tkinter)  |                             |                                 |
|                   |  <------------------------  |  +---------------+   +-------+  |
| - Image Scaling   |       UART Data Stream      |  | Microcontroller|<->| FPGA  |  |
| - Live Viewer     |                             |  |  (MicroPython) |   | Engine|  |
+-------------------+                             |  +---------------+   +-------+  |
                                                  +---------------------------------+
```

---

## 📁 Project Structure

```text
fpga_edge_detection/
├── Output/
│   ├── sobel_gui.py             
│   └── output_results/          
├── FPGA_Logic/
│   ├── sobel.v      
│   └── FPGA_bitstream_MCU.bin   
├── Script/
│   └── main.py                   
├── bimage.bin                   
└── README.md                    
```

---

## ⚙️ Prerequisites & Dependencies

### Hardware Requirements
* **Vicharak Shrike Lite** (or compatible RP2040 + FPGA development module)
* USB-C Data Cable

### Software Requirements
* **Python 3.8+** installed on host machine
* MicroPython flashed on the RP2040 microcontroller

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com//.git
cd 
```

### 2. Install Python Dependencies
Install the required packages for image processing, serial link, and GUI rendering:

```bash
pip install pyserial numpy opencv-python pillow mpremote
```

---

## 🕹️ How to Run the Application

1. **Connect the Board:** Connect your Vicharak Shrike Lite board to your computer via USB. Identify the active COM port (e.g., `COM3` on Windows or `/dev/ttyUSB0` on Linux/macOS).
2. **Launch the Dashboard:** Navigate to the project folder and run the GUI script:
   ```bash
   python Output/sobel_gui.py
   ```
3. **Flash the Files:**
   * The application auto-detects `FPGA_bitstream_MCU.bin` and `main.py` if present in the working directory.
   * Click **Select Input Image** to load any photo (`.jpg`, `.png`).
   * Click **🚀 Flash All to Board**. This automatically resizes the image to $80 \times 48$, generates `bimage.bin`, and uploads all required files to the board using `mpremote`.
4. **Reset Board & Stream:**
   * Press the physical **RESET** button on your Shrike Lite board.
   * Enter your **COM Port** into the GUI input field.
   * Click **▶ Start Real-Time Stream**.

The live edge-detected output will display inside the real-time window, and frame snapshots will automatically be saved into the `output_results/` folder.

---

## 🛠️ Technical Implementation Details

### Sobel Kernel Matrices
The FPGA hardware accelerator applies the standard $3 \times 3$ horizontal and vertical Sobel kernel masks across the pixel grid:

$$
G_x = \begin{bmatrix} -1 & 0 & +1 \\ -2 & 0 & +2 \\ -1 & 0 & +1 \end{bmatrix}, \quad
G_y = \begin{bmatrix} +1 & +2 & +1 \\ 0 & 0 & 0 \\ -1 & -2 & -1 \end{bmatrix}
$$

### Gradient Magnitude Approximation
To reduce resource utilization and achieve high clock frequencies on the FPGA, the gradient magnitude is computed using Manhattan distance:

$$|G| \approx |G_x| + |G_y|$$

Pixels exceeding the configured threshold value are output as white edge pixels ($255$), while background regions are driven to black ($0$).

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request.

---

## 📜 License

This project is licensed under the **MIT License**.