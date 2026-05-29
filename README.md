<div align="center">
  <img src="https://img.shields.io/badge/VTU-Project-blue?style=for-the-badge&logo=appveyor" alt="VTU Project" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />

  <h1>🌿 Smart Indoor Plant Care System</h1>
  <p><b>An AI-Powered Plant Health Monitoring Web Application</b></p>
  <p><i>Mini Project (2024-2025) • B.E. in Artificial Intelligence & Machine Learning</i></p>
  <p><b>P.A. College of Engineering, Mangalore</b></p>
</div>

---

## 📖 Overview
The **Smart Indoor Plant Care System** is an advanced web application designed to help users monitor, analyze, and maintain the health of their indoor plants. By combining real-time environmental monitoring with deterministic Computer Vision-based health analysis, the system detects physical damage, pest infestations, nutrient deficiencies, and fungal diseases with high precision.

## ✨ Key Features
- **🔬 Advanced AI Plant Diagnosis:** Upload a plant leaf image, and the Pillow-powered Computer Vision engine analyzes the HSV color space, edge density, and texture variance to detect conditions like Leaf Blight, Powdery Mildew, Pest Infestations, and Nutrient Deficiency.
- **🛡️ Strict Image Validation:** Intelligent fallback logic immediately rejects non-plant images (e.g., humans, animals, random objects) by analyzing skin-tone ratios and vegetation density.
- **🐛 Physical Damage & Bug Bite Detection:** Utilizes high-frequency structural edge detection (`ImageFilter.FIND_EDGES`) to identify tears, holes, and pest bites even when the leaf color remains green.
- **📡 Live Sensor Monitoring:** Real-time simulated gauges for Temperature, Humidity, Soil Moisture, and Light Levels updating every 3 seconds.
- **📲 Automated SMS Alerts:** Automatically sends SMS alerts (with customizable dynamic phone numbers) when pests or critical damage are detected.
- **🎨 Premium UI/UX:** A stunning, fully responsive dashboard built with vanilla CSS glassmorphism, dynamic animations, and Dark/Light mode support.
- **📄 Downloadable Reports:** Generates detailed text-based plant health analysis reports that can be downloaded locally.

---

## 🛠️ Technology Stack
*   **Backend:** Python 3, Flask, Pillow (Computer Vision processing), Hashlib (Deterministic caching).
*   **Frontend:** HTML5, CSS3 (Glassmorphism & Variables), Vanilla JavaScript.
*   **APIs:** RESTful endpoints for real-time telemetry, image analysis, and alert dispatching.

---

## 👥 The Team
This project was developed by the 5th Semester students of **Artificial Intelligence and Machine Learning** at **P.A. College of Engineering** under the guidance of **Dr. Mohammed Zakir**.

*   **Aboobakkar Aqeef Ilal** (4PA22AI004)
*   **Joyline Dsilva** (4PA22AI013)
*   **Savin S S** (4PA22AI024)
*   **Ummar Farook Shahil** (4PA22AI031)

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/smart-indoor-plant-care.git
   cd smart-indoor-plant-care
   ```

2. **Install the dependencies:**
   Ensure you have Python 3 installed, then run:
   ```bash
   pip install flask flask-cors pillow
   ```

3. **Run the Flask application:**
   ```bash
   python app.py
   ```

4. **Access the Web App:**
   Open your browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## 📸 Screenshots & Usage
1. **Dashboard:** View high-level statistics and recent monitoring data.
   
   <p align="center">
  <img src="https://raw.githubusercontent.com/savin-ss/Smart-Indoort-Plant-Care-System/refs/heads/main/assests/home%20page.png?token=GHSAT0AAAAAAD6JDZMRPVGYHROLJ7XECYNG2QZ54CA" alt="Results Dashboard" width="1919px">
</p>

2. **Analysis:** Drag and drop an image of a leaf. The system will process it, and if it detects pests, it will automatically send an SMS to the phone number configured in the UI.

   <p align="center">
  <img src="https://raw.githubusercontent.com/savin-ss/Smart-Indoort-Plant-Care-System/refs/heads/main/assests/report%20history.png?token=GHSAT0AAAAAAD6JDZMQFVK3Y67DVXDBGN3W2QZ55IQ" alt="Results Dashboard" width="1919px">
</p>


4. **Live Monitor:** Watch as the circular CSS gauges update in real-time with environmental variables.

   <p align="center">
  <img src="https://raw.githubusercontent.com/savin-ss/Smart-Indoort-Plant-Care-System/refs/heads/main/assests/live%20monitoring.png?token=GHSAT0AAAAAAD6JDZMRF5JJDCJTFNPL7NHI2QZ55UQ" alt="Results Dashboard" width="1919px">
</p>

5. **Result:**
   <p align="center">
  <img src="https://raw.githubusercontent.com/savin-ss/Smart-Indoort-Plant-Care-System/refs/heads/main/assests/result.png?token=GHSAT0AAAAAAD6JDZMQZO44QOYTJM6MSRGA2QZ562Q" alt="Results Dashboard" width="1919px">
</p>

---
<div align="center">
  <p>Built with ❤️ for Visvesvaraya Technological University (VTU), Belagavi.</p>
</div>
