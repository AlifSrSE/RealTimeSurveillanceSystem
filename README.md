Here's an improved version of the `README.md` file for your project that includes all the functionalities, features, and an overview of the project. This version is structured to be user-friendly, informative, and clear for developers, collaborators, or stakeholders.

---

# Real-Time Surveillance and Analytics System 🚨

## Overview

This project implements a real-time video processing system for surveillance and security purposes. It utilizes computer vision, deep learning, and data visualization techniques to detect and track people, classify their posture, identify abandoned objects, detect loitering behavior, and analyze crowd dynamics. Alerts are generated for unusual activities such as falls, crowd formation, inactivity, and abandoned objects. The system also provides detailed logs and visualizations through Flask and Streamlit dashboards for monitoring.

## Key Features

### **1. Person Detection & Tracking**
   - Multi-camera support (e.g., store front, back exit).
   - Real-time people detection and tracking using `PersonDetector` and `CentroidTracker`.
   - People counting across a virtual line using `LineCounter` (entry/exit tracking).

### **2. Pose Estimation & Posture Classification**
   - Classifies human posture into Standing, Sitting, and Lying using `mediapipe` for pose estimation.
   - Fall detection alerts based on posture (i.e., person in lying position).

### **3. Face Processing & Privacy Protection**
   - Blurs faces in the video stream for privacy protection.
   - Demographic data (age and gender) estimation using OpenCV DNN-based model on face regions.

### **4. Object Monitoring**
   - Detection of abandoned objects using object detection models.
   - Monitors stationary objects for a prolonged period and triggers alerts if an object is abandoned.

### **5. Analytics & Alerts**
   - **Inactivity Detection**: Identifies objects (people) that have not moved for a set period.
   - **Zone-based Heatmaps**: Tracks people density across different zones (virtual grid) within the camera view.
   - **Crowd Detection**: Detects crowd formation based on the number of people in the frame.
   - Real-time alerts via email and WhatsApp for incidents like falls, crowding, inactivity, and abandoned objects.

### **6. Data Logging & Visualization**
   - Logs all important events and traffic data to CSV files and an SQLite database.
   - **Flask Dashboard**: Basic web interface to view logs and filters (camera, start/end time).
   - **Streamlit Dashboard**: Advanced visualization with heatmaps, zone occupancy matrix, In/Out trend charts, and alert frequency.

### **7. Notifications**
   - **Email Alerts**: Sends real-time alerts via email for fall detection, crowd formation, inactivity, and abandoned objects.
   - **WhatsApp Alerts**: Sends real-time alerts via WhatsApp (placeholder for API integration).

---

## System Components & Structure

### **1. Main Modules**

- `main.py`: Main script for processing the video streams from multiple cameras and generating real-time alerts.
- `pose_utils.py`: Includes functions for pose estimation using `mediapipe` and drawing landmarks.
- `tracker.py`: Implements centroid tracking for real-time object (person) tracking.
- `line_counter.py`: Tracks people crossing a virtual line for entry/exit counting.
- `object_detector.py`: Object detection module to detect potential abandoned objects.
- `alerts.py`: Sends real-time alerts via email and WhatsApp.
- `db.py`: Database utility for logging events to SQLite.

### **2. Dashboards**

- **Flask Dashboard**: Web-based interface for real-time logs and camera feed analysis. Allows filtering by camera ID, start time, and end time.
- **Streamlit Dashboard**: Advanced visualization including zone heatmaps, trend charts (In/Out), alert frequency, and occupancy matrix.

### **3. Data Storage**

- Logs and traffic data are saved in an SQLite database and CSV files.
- Zone counts and activity logs are saved for each camera feed and event.
- Images (heatmaps, zone overlays) are saved in the `/logs` directory for further analysis.

---

## Installation

### **1. Clone the repository**
```bash
git clone https://github.com/yourusername/real-time-surveillance-system.git
cd real-time-surveillance-system
```

### **2. Install Dependencies**
Ensure that you have `Python 3.x` installed, then create a virtual environment and install the required dependencies:

```bash
python3 -m venv env
source env/bin/activate  # For Linux/Mac
env\Scripts\activate     # For Windows

pip install -r requirements.txt
```

### **3. Install OpenCV and Dependencies**
Ensure you have OpenCV installed, or use the following command to install it:

```bash
pip install opencv-python-headless
```

### **4. Set up SQLite Database**
Run the following command to set up the SQLite database:

```bash
python db.py
```

### **5. Running the Application**
To start processing the video feed and triggering real-time alerts:

```bash
python main.py
```

This will process the video from the specified camera feeds and start tracking people, detecting posture, and monitoring for inactivity, abandoned objects, and crowding.

### **6. Access the Dashboards**
- **Flask Dashboard**: Open a web browser and go to [http://localhost:5000](http://localhost:5000).
- **Streamlit Dashboard**: Run the following command to start the Streamlit dashboard:

```bash
streamlit run streamlit_dashboard.py
```

---

## Features & Alerts

### **Real-Time Alerts**
- **Fall Detection**: Alerts triggered when a person is detected in a lying position for an extended period.
- **Crowd Detection**: Alerts when more than a predefined number of people are detected within the camera frame.
- **Inactivity Detection**: Alerts when an object or person is detected stationary for an extended period (e.g., abandoned objects).
- **Abandoned Object Detection**: Trigger alerts when an object stays in the same position for a prolonged period.

### **Alert Notifications**
- **Email**: Uses Python's `smtplib` to send real-time alerts to a predefined email address.
- **WhatsApp**: Placeholder function to send real-time alerts via WhatsApp (can be integrated with Twilio API for production use).

### **Logging & Analytics**
- **CSV Logs**: Event data is saved in CSV files (e.g., camera logs, zone counts).
- **SQLite**: Event logs are stored in a local SQLite database for historical analysis.

---

## Example Use Case

### **Smart Retail Store Surveillance**

Imagine a retail store using multiple cameras to monitor customers' behavior:

- **Person Detection & Tracking**: Track customer movement throughout the store, monitor people entering or leaving the store.
- **Fall Detection**: Alert staff if a customer falls down in any area.
- **Abandoned Object Detection**: Detect items left unattended in aisles, and alert staff for quick action.
- **Zone Heatmaps**: Analyze which areas of the store are most trafficked, and optimize store layout.
- **Crowd Detection**: Alert management if the store gets too crowded, allowing them to take action (e.g., limiting entry).

---

## Future Improvements & Extensions

### **1. Advanced Analytics**
   - Implement more advanced machine learning models to detect unusual behaviors or anomalies in customer actions.
   - Integrate facial recognition (with privacy considerations) for customer demographic analysis.

### **2. Cloud Deployment**
   - Deploy the system in the cloud for better scalability and remote monitoring.
   - Implement cloud-based logging and visualization with AWS, Google Cloud, or Azure.

### **3. Edge Computing**
   - Consider offloading some computational tasks (like object detection) to edge devices to reduce the load on central servers.
   - Implement real-time analysis with edge computing solutions (e.g., NVIDIA Jetson).

### **4. API Integration**
   - Expose a REST API to allow integration with other systems like building access control, or integrating with cloud storage for video feeds.

---

## Contributing

If you wish to contribute to the project, feel free to fork the repository, create a branch, and submit a pull request with your changes. Make sure to adhere to the following guidelines:

- **Code Style**: Follow PEP8 Python style guidelines.
- **Testing**: Write unit tests for new features or bug fixes.
- **Documentation**: Update the `README.md` if necessary and document any new features or modules.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

For any questions or inquiries, feel free to contact me via email at [alif.rahman.c@gmail.com].

---

This README provides a comprehensive overview of the project, setup instructions, features, and potential future improvements. It ensures that other developers or users can easily understand the project and get started with it.