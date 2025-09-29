# 🦾 Myoelectric Robotic Arm for Surgical Instrument Sterilization

## 🎬 Demo
https://github.com/user-attachments/assets/dcc49717-62b0-4c19-89aa-dea88fd53750

---

## ⚡ Quick overview (start to finish)

1) You flex a muscle → tiny electrical activity (EMG) is measured on two channels.  
2) The signal is cleaned and turned into a smooth **strength** number (an **envelope**).  
3) We compare that strength to two thresholds to decide **on/off** with **hysteresis** (so it doesn’t flicker).  
4) If the contraction lasts long enough (debounce) and we haven’t sent a recent command (cooldown), we turn it into an **intent** (select, grip, toggle door, abort).  
5) The robot runs a **step‑by‑step transfer**: approach bin → grip → lift → move to autoclave → open door → place → close door → home.

That’s it: **muscle → intent → motion**, repeated until the instrument is safely in the autoclave.

---

## 🧬 Signal processing and decisions — with gentle math

Let $x_i[n]$ be raw EMG on channel $i\in\{1,2\}$ sampled at $f_s$ Hz.

### 1) Make a smooth strength signal (the envelope)

We first take the absolute value (**rectify**) and then low‑pass filter to get a smooth envelope $u_i[n]$:

$$
u_i[n] = (1-\alpha)\,u_i[n-1] + \alpha\,\lvert x_i[n]\rvert \,, \qquad
\alpha = 1 - e^{-2\pi f_c/f_s}.
$$

- $f_c$ is a small cutoff (about $3$–$6$ Hz).  
- Intuition: this is a moving average of the absolute EMG, so momentary spikes don’t cause false triggers.

### 2) Put everyone on the same scale (z‑score)

From a few seconds of **rest**, compute a baseline mean $\mu_i$ and standard deviation $\sigma_i$, then normalize:

$$
z_i[n] = \frac{u_i[n]-\mu_i}{\sigma_i}.
$$

- Intuition: different electrodes and people give different raw levels; $z_i[n]$ says “how many standard deviations above rest” we are.

### 3) Decide on/off with hysteresis (no flicker)

Use two thresholds: an **on** level $\theta_{\text{on}}$ and a lower **off** level $\theta_{\text{off}}$ (so $\theta_{\text{on}}>\theta_{\text{off}}$). Define the contraction state $c_i[n]\in\{0,1\}$ as

$$
c_i[n] =
\begin{cases}
1, & \text{if } z_i[n]\ge \theta_{\text{on}} \text{ or } \big(c_i[n-1]=1 \text{ and } z_i[n]>\theta_{\text{off}}\big),\\
0, & \text{otherwise.}
\end{cases}
$$

- Intuition: once “on”, we require the signal to drop **below** the lower threshold to switch “off”. That kills boundary chatter.

### 4) Only accept solid presses (debounce) and space them out (cooldown)

- **Debounce:** accept a gesture only if $c_i[n]=1$ for at least $T_d$ seconds in a row. With sample period $\Delta t=1/f_s$, that’s $N_d=\lceil T_d/\Delta t\rceil$ consecutive samples.  
- **Cooldown:** after we accept a gesture, ignore new ones for $T_c$ seconds so we don’t double‑fire.

### 5) Long‑press for abort (safety)

If channel 2 stays accepted for $T_\ell$ seconds (e.g., $\sim 1.2$ s), we issue **ABORT** and send the arm home.

---

## 🧭 Gesture → intent → motion (the step‑by‑step transfer)

**Gestures (from the two channels):**  
- CH1 → **START / cycle bin**  
- CH2 → **GRIP** (first press closes, press again at the autoclave to release)  
- CH1+CH2 together → **TOGGLE DOOR**  
- CH2 long‑press → **ABORT** (go home safely)

**Transfer sequence:**

```
IDLE → SELECT_BIN → APPROACH → GRIP → LIFT → TRANSIT
     → OPEN_AUTOCLAVE → PLACE → CLOSE_AUTOCLAVE → HOME
```

Each step runs a safe **motion primitive** to a predefined waypoint (bins R/G/B, autoclave, home). We only advance when both the **intent** is present and the previous move has finished.

---

## 🎚️ Typical parameters (good starting points)

| Symbol | Meaning | Typical |
|---|---|---|
| $f_s$ | EMG sampling rate | 200–1000 Hz |
| $f_c$ | Envelope cutoff | 3–6 Hz |
| $\theta_{\text{on}}$ | On threshold (z‑score) | 0.65–0.9 |
| $\theta_{\text{off}}$ | Off threshold (z‑score) | 0.30–0.5 |
| $T_d$ | Debounce time | 0.10–0.20 s |
| $T_c$ | Cooldown | 0.30–0.40 s |
| $T_\ell$ | Long‑press (abort) | ≈ 1.2 s |

**Calibration tip.** From the rest segment, set $\theta_{\text{on}}$ near the $95$‑th percentile of $z_i[n]$ plus a small margin; set $\theta_{\text{off}}$ to roughly half that. Adjust until contractions feel easy but accidental triggers are rare.

---

## 🧪 What you should see

- Reliable pick/place of mock instruments into the autoclave (sim + hardware).  
- Long‑press abort always returns to **home**.  
- Stable control thanks to envelope + hysteresis + debounce.

**Limitations.** EMG varies day‑to‑day; minor re‑tuning may be needed. The autoclave door is simulated by a timed dwell in this prototype. A richer gesture set would require more channels or a classifier.

---

## 🧠 Glossary

**EMG** — electrical activity from muscles.  
**Envelope** — a smoothed “strength” of EMG (after rectifying + low‑pass).  
**Hysteresis** — two thresholds (on/off) to prevent flicker.  
**Debounce** — minimum time pressed before acting.  
**Cooldown** — minimum time between accepted commands.  
**Waypoint** — a predefined robot pose used to compose the motion sequence.

---

## 📄 Code

See `surgical.robotic_arm.py` for the cleaned controller (gesture decoding, sequence control, motion primitives, centralized constants).

---

## 📜 License

MIT — see `LICENSE`.
