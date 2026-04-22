import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time
import pandas as pd
import random
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Fitness Trainer Pro++", page_icon="🏋️", layout="wide")

# ---------------- BROWSER VOICE ----------------
def speak(text):
    st.markdown(f"""
    <script>
    var msg = new SpeechSynthesisUtterance("{text}");
    window.speechSynthesis.speak(msg);
    </script>
    """, unsafe_allow_html=True)

# ---------------- UI ----------------
st.markdown("""<style>
.stApp {background: radial-gradient(circle at 10% 20%, #020617 0%, #0f172a 90%);color:white;}
.card {padding:20px;border-radius:20px;background:rgba(255,255,255,0.05);text-align:center;margin-bottom:20px;}
.reps {border-bottom:4px solid #22c55e;}
.cal {border-bottom:4px solid #f97316;}
.time {border-bottom:4px solid #38bdf8;}
.good {color:#4ade80;}
.warn {color:#facc15;}
.bad {color:#f87171;}
</style>""", unsafe_allow_html=True)

st.markdown("<h1>🏋️ AI Fitness Trainer Pro++</h1>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
exercise = st.sidebar.selectbox("Exercise", ["Squat", "Push-up", "Jumping Jack"])
run = st.sidebar.checkbox("🟢 Start Camera")

# ---------------- STATE ----------------
if "counter" not in st.session_state:
    st.session_state.counter = 0
if "stage" not in st.session_state:
    st.session_state.stage = "DOWN"
if "rep_history" not in st.session_state:
    st.session_state.rep_history = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "last_voice" not in st.session_state:
    st.session_state.last_voice = 0

# ---------------- MEDIAPIPE ----------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils

# ---------------- ANGLE ----------------
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360-angle if angle > 180 else angle

# ---------------- VIDEO PROCESSOR ----------------
class PoseTrainer(VideoTransformerBase):
    def __init__(self):
        self.counter = 0
        self.stage = "DOWN"

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        try:
            landmarks = results.pose_landmarks.landmark

            if exercise == "Squat":
                hip = [landmarks[23].x, landmarks[23].y]
                knee = [landmarks[25].x, landmarks[25].y]
                ankle = [landmarks[27].x, landmarks[27].y]
                angle = calculate_angle(hip, knee, ankle)

                if angle > 160:
                    self.stage = "UP"
                elif angle < 90 and self.stage == "UP":
                    self.counter += 1
                    self.stage = "DOWN"

            elif exercise == "Push-up":
                shoulder = [landmarks[11].x, landmarks[11].y]
                elbow = [landmarks[13].x, landmarks[13].y]
                wrist = [landmarks[15].x, landmarks[15].y]
                angle = calculate_angle(shoulder, elbow, wrist)

                if angle > 160:
                    self.stage = "UP"
                elif angle < 90 and self.stage == "UP":
                    self.counter += 1
                    self.stage = "DOWN"

            elif exercise == "Jumping Jack":
                left_wrist = landmarks[15].y
                right_wrist = landmarks[16].y
                left_shoulder = landmarks[11].y
                right_shoulder = landmarks[12].y
                left_ankle = landmarks[27].x
                right_ankle = landmarks[28].x

                if left_wrist < left_shoulder and abs(left_ankle-right_ankle)>0.25:
                    if self.stage == "DOWN":
                        self.counter += 1
                    self.stage = "UP"
                else:
                    self.stage = "DOWN"

        except:
            pass

        if results.pose_landmarks:
            mp_draw.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.putText(img, f"Reps: {self.counter}", (10,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        st.session_state.counter = self.counter
        return img

# ---------------- LAYOUT ----------------
col1, col2 = st.columns([2,1])

with col1:
    if run:
        webrtc_streamer(
            key="fitness",
            video_transformer_factory=PoseTrainer,
            media_stream_constraints={"video": True, "audio": False},
        )

with col2:
    reps = st.session_state.counter
    calories = reps * 0.3
    elapsed = int(time.time() - st.session_state.start_time)

    st.markdown(f"<div class='card reps'><h2>Reps</h2><h1>{reps}</h1></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card cal'><h2>Calories</h2><h1>{round(calories,1)}</h1></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card time'><h2>Time</h2><h1>{elapsed}s</h1></div>", unsafe_allow_html=True)

    # 🔊 Voice feedback (online)
    if reps > 0 and time.time() - st.session_state.last_voice > 3:
        speak(f"{reps} reps done")
        st.session_state.last_voice = time.time()

