# 🦾 Myoelectric Robotic Arm for Surgical Instrument Sterilization

<!-- Intro video placeholder -->

https://github.com/user-attachments/assets/dcc49717-62b0-4c19-89aa-dea88fd53750

---

## 🎯 Project Overview

The aim of this project was to demonstrate how **surface electromyography (EMG)** can be harnessed to control a robotic arm for **sterile transfer of surgical instruments**.  

A **Quanser QArm** was connected to EMG sensors worn by an operator. By flexing or relaxing specific muscles, the operator could issue commands such as:

- Selecting a staging bin.  
- Opening or closing the gripper.  
- Operating the autoclave door.  
- Triggering the overall sterilization cycle.  

In simple terms: **muscle signals are translated into robot motions**. The end result is a semi‑autonomous workflow that transfers surgical tools from their bins into an autoclave for sterilization, with the human providing intuitive, muscle‑driven control.

---

## 🧬 How it Works

### 1. EMG Signal Processing

Two EMG channels \(e_1(t), e_2(t)\) are continuously sampled. Each channel is normalized and compared against thresholds:

$$
\tilde{e}_i(t) = \frac{e_i(t) - \mu_i}{\sigma_i}, \quad i \in \{1,2\}
$$

where \(\mu_i, \sigma_i\) are baseline mean and standard deviation.  
A contraction is detected when:

$$
\tilde{e}_i(t) > \theta_{\text{on}}, \qquad
\tilde{e}_i(t) < \theta_{\text{off}} \;\; \text{(release)}
$$

with hysteresis (\(\theta_{\text{on}} > \theta_{\text{off}}\)) to avoid flicker.  

- Channel 1 contraction → **selection / start**.  
- Channel 2 contraction → **grip / release**.  
- Both channels together → **toggle autoclave door**.  

### 2. State Machine Control

A **finite‑state machine (FSM)** ensures safety and predictability:

\`\`\`
IDLE → SELECT_BIN → APPROACH → GRIP → LIFT → TRANSIT
     → OPEN_AUTOCLAVE → PLACE → CLOSE_AUTOCLAVE → HOME
\`\`\`

Each transition requires both the correct EMG intent **and** successful completion of the previous motion.

### 3. Motion Primitives

- **Waypoints** define safe poses for bins (R, G, B), the autoclave, and home position.  
- **Primitives** such as `move_to()`, `grip()`, `open_door()` are composed into the sterilization sequence.  
- Timing and speeds are tuned to prevent collisions and ensure smooth transfers.

---

## 🧪 Results

- **Reliable pick/place** of mock instruments from bins to autoclave.  
- **Abort gesture** (sustained contraction) returns QArm to home safely.  
- System tested in both **simulation (QLabs)** and **hardware**.  
- Clear demonstration of EMG as an intuitive, hands‑free control interface for surgical workflows.

---

## ⚖️ Limitations

- EMG signals are inherently noisy — required filtering and debounce logic.  
- Autoclave actuation was simulated (time delay) rather than using a physical mechanism.  
- Gesture set is simple; adding more intents would need additional channels or better pattern recognition.

---

## 🧠 Glossary

- **EMG** — Surface electromyography signal from muscle activity.  
- **FSM** — Finite‑State Machine (explicit state transitions).  
- **QArm** — Quanser 4‑DOF robotic arm used in lab experiments.  
- **QLabs** — Quanser virtual environment mirroring hardware.  
- **Waypoint** — Predefined 3D target position for the end effector.  
- **Pose** — Position + orientation of the robotic gripper.  

---

## 📄 License

MIT — see `LICENSE`.

---

## 🔧 Code Notes

The repository contains the original Python controller script. A refactored version (`surgical.robotic_arm.refactored.py`) is included, featuring:

- Modular motion primitives.  
- Clear EMG → intent mapping.  
- Explicit FSM implementation.  
- Centralized constants for thresholds, waypoints, and speeds.

