# 🦾 Myoelectric Robotic Arm for Surgical Instrument Sterilization

## 🎬 Demo
https://github.com/user-attachments/assets/dcc49717-62b0-4c19-89aa-dea88fd53750

---

## 🎯 Project Overview

This project demonstrates how **surface electromyography (EMG)** can control a robotic arm for **sterile transfer of surgical instruments**.

A **Quanser QArm** was linked to EMG sensors worn by an operator. By contracting and relaxing specific muscles, the operator issues:
- Staging‑bin selection
- Gripper open/close
- Autoclave door toggle
- Start/abort of the transfer sequence

In short, **muscle signals are mapped to robot actions** to complete a pick–place sterilization workflow.

---

## 🧬 How it Works

### 1) EMG signal processing

Two channels \(e_1(t), e_2(t)\) are sampled, normalized, and thresholded.

$$
\tilde e_i(t) = \frac{e_i(t) - \mu_i}{\sigma_i},\quad i \in \{1,2\}.
$$

A contraction is detected when

$$
\tilde e_i(t) > \theta_{\text{on}},\qquad \tilde e_i(t) < \theta_{\text{off}}\;\text{ (release)}.
$$

Hysteresis (placed on its own line to render cleanly):

$$
\theta_{\text{on}} > \theta_{\text{off}}.
$$

Mapping used here:
- Channel 1 → **select / start**
- Channel 2 → **grip / release**
- Both channels together → **toggle autoclave door**
- Sustained Channel 2 → **abort**

### 2) Sterilization sequence control (gesture‑driven)

```
IDLE → SELECT_BIN → APPROACH → GRIP → LIFT → TRANSIT
     → OPEN_AUTOCLAVE → PLACE → CLOSE_AUTOCLAVE → HOME
```

Each step advances only when the required gesture is observed **and** the previous motion completes.

### 3) Motion primitives

`move_to(·)`, `grip(open/close)`, and `toggle_door()` operate on predefined **waypoints** for bins (R/G/B), autoclave, and home. Speeds and dwell times are tuned to avoid collisions and ensure smoothness.

---

## 🧪 Results

- Reliable pick/place of mock instruments into the autoclave (simulation and hardware).  
- **Abort** gesture returns the arm safely to **home**.  
- Demonstrates EMG as a hands‑free control channel for sterile operations.

---

## ⚖️ Limitations

- EMG noise requires filtering, debounce, and hysteresis.  
- Autoclave actuation is simulated (timed delay) in this prototype.  
- Gesture vocabulary is minimal; extension would need more channels or classifier‑based recognition.

---

## 🧠 Glossary

**EMG** — surface electromyography • **Sequence control** — gesture‑triggered stepwise motions • **QArm** — Quanser 4‑DOF arm • **QLabs** — Quanser simulation • **Waypoint** — predefined pose • **Pose** — position + orientation.

---

## 📄 License

MIT — see `LICENSE`.

---

## 🔧 Code

See `surgical.robotic_arm.refactored.py` for the cleaned controller with gesture decoding, sequence control, motion primitives, and centralized constants.
