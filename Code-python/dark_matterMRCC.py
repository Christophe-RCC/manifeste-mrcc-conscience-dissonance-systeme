import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap

# --- CONFIGURATION ---
GRID_SIZE = 80
DT = 0.1
SIGMA_0 = 0.05
SIGMA_1 = 0.8
SIGMA_2 = 0.2
CRIT = 0.35
MEM_STRENGTH = 0.9
DECAY = 0.4
DIFF = 0.05
RELAX = 0.05

# --- INITIALISATION ---
F = np.random.uniform(0.0, 0.1, (GRID_SIZE, GRID_SIZE)) + SIGMA_0 * np.random.randn(GRID_SIZE, GRID_SIZE)
M = np.zeros((GRID_SIZE, GRID_SIZE))

# --- COULEURS ---
cmap_F = LinearSegmentedColormap.from_list("F", ["navy", "cyan", "red"])
cmap_M = LinearSegmentedColormap.from_list("M", ["black", "gray", "gold"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
fig.patch.set_facecolor('#111')
ax1.set_facecolor('#111')
ax2.set_facecolor('#111')

im_F = ax1.imshow(F, cmap=cmap_F, vmin=0, vmax=1.0)
im_M = ax2.imshow(M, cmap=cmap_M, vmin=0, vmax=1.0)

ax1.set_title("Dissonance (F)", color='white')
ax2.set_title("Mémoire (M)", color='white')

# --- LOGIQUE PHYSIQUE ---
def update(frame):
    global F, M
    
    # 1. Bruit multiplicatif
    sigma = SIGMA_0 + SIGMA_1 * F + SIGMA_2 * M
    noise = sigma * np.random.normal(0, 1, F.shape)
    
    # 2. Laplacien (Diffusion)
    lap = (np.roll(F, 1, 0) + np.roll(F, -1, 0) + 
           np.roll(F, 1, 1) + np.roll(F, -1, 1) - 4 * F)

    # --- NOUVELLE LOGIQUE : Source dépendante de la saturation mémoire
    # Plus la mémoire moyenne (M) est haute, moins le système reçoit d'énergie externe
    current_source = 0.02 * (1 - np.mean(M)) 
    
    # 3. Évolution de F
    dF = DIFF * lap - RELAX * F * (1 - M) + noise + current_source
    F = F + DT * dF
    F = np.maximum(F, 0)
    
    # 4. Mise à jour de M
    mask = F > CRIT
    delta = np.zeros_like(M)
    delta[mask] = MEM_STRENGTH * (F[mask] - CRIT)
    M = M * (1 - DECAY) + delta
    M = np.clip(M, 0, 1)
    
    # Mise à jour visuelle
    im_F.set_array(F)
    im_M.set_array(M)
    
    # Arrêt après 200 frames pour éviter de tourner indéfiniment
    if frame == 200:
        plt.close(fig) 
    return [im_F, im_M]

# --- LANCEMENT ---
# interval=50 = 20 images/seconde (fluide)
ani = animation.FuncAnimation(fig, update, frames=200, interval=50, blit=True)
plt.tight_layout()
plt.show()
