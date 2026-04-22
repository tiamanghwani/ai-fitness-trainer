import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time
import pandas as pd
import pyttsx3
import threading
import random
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Fitness Trainer Pro++", page_icon="🏋️", layout="wide")

# ---------------- ULTRA UI & COLORS ----------------
st.markdown("""
<style>
/* Global Background */
.stApp {
    background: radial-gradient(circle at 10% 20%, #020617 0%, #0f172a 90%);
    color: white;
}

/* Neon Title */
h1 {
    text-align: center;
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(to right, #00f2fe 0%, #4facfe 50%, #00f2fe 100%);
    background-size: 200% auto;
    color: #fff;
    background-clip: text;
    text-fill-color: transparent;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 3s linear infinite;
}

@keyframes shine {
    to { background-position: 200% center; }
}

/* Upgraded Glass Cards with Animated Borders */
.card {
    padding: 20px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(15px);
    text-align: center;
    margin-bottom: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.5);
    background: rgba(255, 255, 255, 0.08);
}

/* Vivid Glowing Card Accents */
.reps { box-shadow: 0px 8px 32px 0px rgba(34, 197, 94, 0.37); border-bottom: 4px solid #22c55e; }
.cal { box-shadow: 0px 8px 32px 0px rgba(249, 115, 22, 0.37); border-bottom: 4px solid #f97316; }
.time { box-shadow: 0px 8px 32px 0px rgba(56, 189, 248, 0.37); border-bottom: 4px solid #38bdf8; }
.posture-card { border-bottom: 4px solid #a855f7; }

/* Metric Numbers */
.card h1 {
    font-size: 3.5rem;
    margin: 0;
    padding: 0;
    text-shadow: 0 0 10px rgba(255,255,255,0.3);
}

.card h2 {
    font-size: 1.2rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #94a3b8;
    margin-bottom: 10px;
}

/* Feedback colors */
.good { color: #4ade80 !important; text-shadow: 0 0 15px #4ade80; }
.warn { color: #facc15 !important; text-shadow: 0 0 15px #facc15; }
.bad { color: #f87171 !important; text-shadow: 0 0 15px #f87171; }

/* Instructions Box */
.instructions {
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(236, 72, 153, 0.15));
    padding: 25px;
    border-radius: 20px;
    margin-bottom: 25px;
    border: 1px solid rgba(236, 72, 153, 0.3);
    box-shadow: 0px 0px 20px rgba(236, 72, 153, 0.2);
}

/* Custom Streamlit Buttons */
div.stButton > button {
    background: linear-gradient(90deg, #ec4899, #8b5cf6);
    color: white;
    border: none;
    border-radius: 30px;
    padding: 10px 24px;
    font-weight: bold;
    font-size: 1.1rem;
    transition: all 0.3s;
    width: 100%;
}
div.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(236, 72, 153, 0.6);
    color: white;
}
div.stDownloadButton > button {
    background: linear-gradient(90deg, #22c55e, #10b981);
    color: white;
    border-radius: 30px;
    font-weight: bold;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🏋️ AI Fitness Trainer Pro++</h1>", unsafe_allow_html=True)

# ---------------- INSTRUCTIONS ----------------
st.markdown("""
<div class="instructions">
    <h3 style="color: #e879f9;">📘 How to Use</h3>
    <ul style="color: #e2e8f0; font-size: 1.1rem;">
        <li>Select your exercise from the sidebar and click <b>Start Workout</b>.</li>
        <li>Ensure your full body is visible in the camera frame.</li>
        <li>Listen to the AI coach for real-time posture corrections and motivation.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=100) 
st.sidebar.markdown("<h2 style='text-align: center; color: #38bdf8;'>Control Panel</h2>", unsafe_allow_html=True)
exercise = st.sidebar.selectbox("Choose Exercise", ["Squat", "Push-up", "Jumping Jack"])
st.sidebar.markdown("---")
run = st.sidebar.checkbox("🟢 Activate Camera", key="run_cam")
stop = st.sidebar.button("🛑 End Session")

# ---------------- MAC-OPTIMIZED VOICE ----------------
def speak(text):
    def run_speech():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 185) 
            engine.setProperty("volume", 1.0)
            
            voices = engine.getProperty('voices')
            for voice in voices:
                if any(mac_voice in voice.name for mac_voice in ["Samantha", "Alex", "Daniel", "Victoria"]):
                    engine.setProperty('voice', voice.id)
                    break
                    
            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            pass 
    threading.Thread(target=run_speech, daemon=True).start()

# Motivational phrases
motivations = ["Great job!", "Excellent form!", "Keep pushing!", "You're a machine!", "Nice rep!"]
milestones = {5: "Five down, keep going!", 10: "Ten reps! Halfway there!", 20: "Twenty reps! Absolute beast!"}

# ---------------- SESSION STATE ----------------
if "counter" not in st.session_state:
    st.session_state.counter = 0
if "stage" not in st.session_state:
    st.session_state.stage = "DOWN"
if "last_spoken_time" not in st.session_state:
    st.session_state.last_spoken_time = 0
if "last_warning_time" not in st.session_state:
    st.session_state.last_warning_time = 0
if "rep_history" not in st.session_state:
    st.session_state.rep_history = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "workout_summary" not in st.session_state:
    st.session_state.workout_summary = None

# ---------------- LAYOUT ----------------
col1, col2 = st.columns([2, 1.2])
FRAME_WINDOW = col1.empty()

with col2:
    feedback_display = st.empty()
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    rep_display = m1.empty()
    cal_display = m2.empty()
    time_display = st.empty()
    graph_display = st.empty()
    export_display = st.empty() # Placeholder for download button

# ---------------- MEDIAPIPE ----------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# ---------------- ANGLE MATH ----------------
def calculate_angle(a, b, c):
    a = np.array(a); b = np.array(b); c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
              np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180: angle = 360 - angle
    return angle

# ---------------- MAIN LOOP ----------------
while run:
    ret, frame = cap.read()
    if not ret:
        st.error("Camera not working ❌ Please check your permissions.")
        break

    frame = cv2.flip(frame, 1)
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    posture = "✔️ Perfect Form"
    posture_class = "good"
    current_time = time.time()

    try:
        landmarks = results.pose_landmarks.landmark

        # -------- SQUAT --------
        if exercise == "Squat":
            hip = [landmarks[23].x, landmarks[23].y]
            knee = [landmarks[25].x, landmarks[25].y]
            ankle = [landmarks[27].x, landmarks[27].y]
            angle = calculate_angle(hip, knee, ankle)

            if angle > 160:
                st.session_state.stage = "UP"
            elif angle < 90 and st.session_state.stage == "UP":
                st.session_state.counter += 1
                st.session_state.stage = "DOWN"
                st.session_state.rep_history.append(st.session_state.counter)

                if current_time - st.session_state.last_spoken_time > 2.5:
                    phrase = milestones.get(st.session_state.counter, random.choice(motivations))
                    speak(f"{st.session_state.counter}. {phrase}")
                    st.session_state.last_spoken_time = current_time

            if abs(hip[0] - ankle[0]) > 0.25:
                posture = "⚠️ Knees caving in!"
                posture_class = "bad"

        # -------- PUSHUP --------
        elif exercise == "Push-up":
            shoulder = [landmarks[11].x, landmarks[11].y]
            elbow = [landmarks[13].x, landmarks[13].y]
            wrist = [landmarks[15].x, landmarks[15].y]
            hip = [landmarks[23].x, landmarks[23].y]
            angle = calculate_angle(shoulder, elbow, wrist)

            if angle > 160:
                st.session_state.stage = "UP"
            elif angle < 90 and st.session_state.stage == "UP":
                st.session_state.counter += 1
                st.session_state.stage = "DOWN"
                st.session_state.rep_history.append(st.session_state.counter)

                if current_time - st.session_state.last_spoken_time > 2.5:
                    phrase = milestones.get(st.session_state.counter, random.choice(motivations))
                    speak(f"{st.session_state.counter}. {phrase}")
                    st.session_state.last_spoken_time = current_time

            if abs(shoulder[1] - hip[1]) > 0.2:
                posture = "⚠️ Lower your hips!"
                posture_class = "bad"

        # -------- JUMPING JACK --------
        elif exercise == "Jumping Jack":
            left_wrist = landmarks[15].y
            right_wrist = landmarks[16].y
            left_shoulder = landmarks[11].y
            right_shoulder = landmarks[12].y
            left_ankle = landmarks[27].x
            right_ankle = landmarks[28].x

            hands_up = left_wrist < left_shoulder and right_wrist < right_shoulder
            legs_apart = abs(left_ankle - right_ankle) > 0.25

            if hands_up and legs_apart:
                if st.session_state.stage == "DOWN":
                    st.session_state.counter += 1
                    st.session_state.rep_history.append(st.session_state.counter)

                    if current_time - st.session_state.last_spoken_time > 2.5:
                        phrase = milestones.get(st.session_state.counter, random.choice(motivations))
                        speak(f"{st.session_state.counter}. {phrase}")
                        st.session_state.last_spoken_time = current_time

                st.session_state.stage = "UP"
            else:
                st.session_state.stage = "DOWN"

    except Exception:
        posture = "🔍 Move into frame"
        posture_class = "warn"

    # --- VOICE POSTURE CORRECTION ---
    if posture_class == "bad" and (current_time - st.session_state.last_warning_time > 4):
        speak("Watch your form!")
        st.session_state.last_warning_time = current_time

    # Custom styling for pose drawing
    mp_draw.draw_landmarks(
        image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
        mp_draw.DrawingSpec(color=(244, 114, 182), thickness=2, circle_radius=2), 
        mp_draw.DrawingSpec(color=(56, 189, 248), thickness=2, circle_radius=2)   
    )
    
    FRAME_WINDOW.image(image, use_container_width=True)

    # -------- FEEDBACK METRICS --------
    feedback_display.markdown(
        f"<div class='card posture-card'><h2>Posture Status</h2><h1 class='{posture_class}' style='font-size: 2rem;'>{posture}</h1></div>",
        unsafe_allow_html=True
    )

    elapsed = int(time.time() - st.session_state.start_time)
    calories = st.session_state.counter * 0.3

    rep_display.markdown(f"<div class='card reps'><h2>Reps</h2><h1>{st.session_state.counter}</h1></div>", unsafe_allow_html=True)
    cal_display.markdown(f"<div class='card cal'><h2>KCal</h2><h1>{round(calories,1)}</h1></div>", unsafe_allow_html=True)
    time_display.markdown(f"<div class='card time'><h2>Time Active</h2><h1 style='font-size: 2.5rem;'>{elapsed}s</h1></div>", unsafe_allow_html=True)

    if len(st.session_state.rep_history) > 1:
        df = pd.DataFrame({"Reps Over Time": st.session_state.rep_history})
        graph_display.line_chart(df, height=150, color="#a855f7")

    if stop:
        speak(f"Workout Complete! You did {st.session_state.counter} reps. Great job!")
        
        # Save summary data to session state before breaking
        st.session_state.workout_summary = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Exercise": exercise,
            "Total Reps": st.session_state.counter,
            "Calories Burned": round(calories, 1),
            "Duration (sec)": elapsed
        }
        
        # Reset counters for the next run
        st.session_state.counter = 0
        st.session_state.rep_history = []
        st.session_state.start_time = time.time()
        
        break

cap.release()

# ---------------- EXPORT WORKOUT DATA ----------------
# This logic runs outside the camera loop so Streamlit can handle the file download properly
if not run and st.session_state.workout_summary:
    st.success("🎉 Workout Saved! Check out your stats below.")
    
    # Create DataFrame from summary
    summary_df = pd.DataFrame([st.session_state.workout_summary])
    
    # Show the data in the UI
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Convert to CSV
    csv = summary_df.to_csv(index=False).encode('utf-8')
    
    # Download Button
    st.download_button(
        label="💾 Download Workout History (CSV)",
        data=csv,
        file_name=f"Workout_{st.session_state.workout_summary['Exercise']}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

