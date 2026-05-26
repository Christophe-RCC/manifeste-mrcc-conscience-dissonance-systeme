#Python version 3.12.10

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Paramètres
GRID_SIZE = 150
FRAMES = 300
DT = 0.05

# Physique et dynamique
KAPPA = 0.05
DIFF = 0.2
RELAX = 0.01
DECAY = 0.01
S_MAX = 0.5
F_CRIT = 0.35
M_PLANCK = 12.0
GAMMA_EVC = 1e-3
EPSILON = 1e-6

# Initialisation
F = np.random.uniform(0, 0.05, (GRID_SIZE, GRID_SIZE))
M = np.zeros((GRID_SIZE, GRID_SIZE))

# Figures et axes
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
ax1, ax2, ax3 = axes

# Images
im_F = ax1.imshow(F, cmap='coolwarm', vmin=0, vmax=1.5)
ax1.set_title("Dissonance (F)")
ax1.set_xticks([]); ax1.set_yticks([])
im_M = ax2.imshow(M, cmap='inferno', vmin=0, vmax=M_PLANCK)
ax2.set_title("Mémoire (M)")
ax2.set_xticks([]); ax2.set_yticks([])

# Graphique
line_max, = ax3.plot([], [], color='red', label='Max M')
line_mean, = ax3.plot([], [], color='blue', label='Mean M')
ax3.set_xlim(0, FRAMES)
ax3.set_ylim(0, M_PLANCK+1)
ax3.set_xlabel("Frame")
ax3.set_ylabel("Valeur")
ax3.legend()

# Historiques
history_max = []
history_mean = []

# Fonction de diffusion
def diffuse(field):
    return (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4*field)

# Fonction d'initialisation
def init():
    line_max.set_data([], [])
    line_mean.set_data([], [])
    return [im_F, im_M, line_max, line_mean]

# Fonction de mise à jour
def update(frame):
    global F, M
    # 1. Disjonction F
    lap_F = diffuse(F)
    current_source = S_MAX * max(0.0, 1.0 - np.mean(M))
    dF = DIFF * lap_F - RELAX * F + current_source
    F += DT * dF
    F = np.maximum(F, 0)

    # 2. Évolution de M
    mask_Fcrit = F > F_CRIT
    delta_linear = np.zeros_like(M)
    delta_linear[mask_Fcrit] = 0.8 * (F[mask_Fcrit] - F_CRIT)
    feedback = KAPPA * (M ** 2)
    decay = DECAY * M
    distance = M_PLANCK - M
    pressure = np.where(distance > 1.0, 0.0, GAMMA_EVC / (distance + EPSILON)**2)
    dM = delta_linear + feedback - decay - pressure
    M += DT * dM
    M = np.clip(M, 0, M_PLANCK)

    # Mise à jour images
    im_F.set_data(F)
    im_M.set_data(M)

    # Graphiques
    max_M = np.max(M)
    mean_M = np.mean(M)
    history_max.append(max_M)
    history_mean.append(mean_M)
    # Limiter la taille pour performance
    if len(history_max) > FRAMES:
        history_max.pop(0)
        history_mean.pop(0)
    # Mettre à jour courbes
    line_max.set_data(range(len(history_max)), history_max)
    line_mean.set_data(range(len(history_mean)), history_mean)

    return [im_F, im_M, line_max, line_mean]

# Création de l'animation
ani = animation.FuncAnimation(fig, update, init_func=init, frames=FRAMES, interval=30, blit=True)
plt.tight_layout()
plt.show()
