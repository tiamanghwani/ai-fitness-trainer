import streamlit as st
import mediapipe as mp
import numpy as np
import time
import pandas as pd
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Fitness Trainer Pro++", layout="wide")
st.markdown("<h1 style='text-align:center;'>🏋️ AI Fitness Trainer Pro++</h1>", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
exercise = st.sidebar.selectbox("Exercise", ["Squat", "Push-up", "Jumping Jack"])
run = st.sidebar.checkbox("Start Camera")

# ---------------- SESSION STATE ----------------
if "counter" not in st.session_state:
    st.session_state.counter = 0
if "stage" not in st.session_state:
    st.session_state.stage = "DOWN"
if "last_rep_time" not in st.session_state:
    st.session_state.last_rep_time = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# ---------------- MEDIAPIPE ----------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils

# ---------------- ANGLE FUNCTION ----------------
def calculate_angle(a, b, c):
    a = np.array(a); b = np.array(b); c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
              np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle

# ---------------- VIDEO PROCESSOR ----------------
class Trainer(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        image = img[:, :, ::-1]  # BGR → RGB

        results = pose.process(image)
        current_time = time.time()

        try:
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # -------- SQUAT --------
                if exercise == "Squat":
                    hip = [landmarks[23].x, landmarks[23].y]
                    knee = [landmarks[25].x, landmarks[25].y]
                    ankle = [landmarks[27].x, landmarks[27].y]

                    angle = calculate_angle(hip, knee, ankle)

                    if angle > 150:
                        st.session_state.stage = "UP"

                    if angle < 100 and st.session_state.stage == "UP":
                        if current_time - st.session_state.last_rep_time > 0.8:
                            st.session_state.counter += 1
                            st.session_state.last_rep_time = current_time
                        st.session_state.stage = "DOWN"

                # -------- PUSH-UP --------
                elif exercise == "Push-up":
                    shoulder = [landmarks[11].x, landmarks[11].y]
                    elbow = [landmarks[13].x, landmarks[13].y]
                    wrist = [landmarks[15].x, landmarks[15].y]

                    angle = calculate_angle(shoulder, elbow, wrist)

                    if angle > 150:
                        st.session_state.stage = "UP"

                    if angle < 100 and st.session_state.stage == "UP":
                        if current_time - st.session_state.last_rep_time > 0.8:
                            st.session_state.counter += 1
                            st.session_state.last_rep_time = current_time
                        st.session_state.stage = "DOWN"

                # -------- JUMPING JACK --------
                elif exercise == "Jumping Jack":
                    lw = landmarks[15].y
                    rw = landmarks[16].y
                    ls = landmarks[11].y
                    rs = landmarks[12].y

                    hands_up = lw < ls and rw < rs

                    if hands_up and st.session_state.stage == "DOWN":
                        if current_time - st.session_state.last_rep_time > 0.8:
                            st.session_state.counter += 1
                            st.session_state.last_rep_time = current_time
                        st.session_state.stage = "UP"
                    else:
                        st.session_state.stage = "DOWN"

                # Draw pose
                mp_draw.draw_landmarks(
                    img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                )

        except:
            pass

        return img

# ---------------- CAMERA ----------------
if run:
    webrtc_streamer(key="ai-trainer", video_transformer_factory=Trainer)

# ---------------- METRICS ----------------
col1, col2, col3 = st.columns(3)

elapsed = int(time.time() - st.session_state.start_time)
calories = round(st.session_state.counter * 0.4, 1)

with col1:
    st.metric("Reps", st.session_state.counter)

with col2:
    st.metric("Calories", calories)

with col3:
    st.metric("Time", f"{elapsed}s")

# ---------------- LEVEL SYSTEM ----------------
level = "Beginner"
if st.session_state.counter > 20:
    level = "Intermediate"
if st.session_state.counter > 50:
    level = "Beast 🔥"

st.success(f"Level: {level}")

# ---------------- EXPORT ----------------
if st.session_state.counter > 0:
    df = pd.DataFrame([{
        "Date": datetime.now(),
        "Exercise": exercise,
        "Reps": st.session_state.counter,
        "Calories": calories
    }])

    st.download_button("Download Report", df.to_csv(index=False), "report.csv")

