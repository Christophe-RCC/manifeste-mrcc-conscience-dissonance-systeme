#MRCC big rip

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec

# --- CONFIGURATION (Emergence Pure - Sans Graine) ---
GRID_SIZE = 120  # Un peu plus grand pour mieux voir l'émergence
DT = 0.05
FRAMES = 2000    # Temps d'attente plus long pour l'émergence naturelle

# Paramètres physiques (Équilibre fin pour l'émergence spontanée)
SIGMA_0 = 0.08   # Bruit de fond un peu plus fort pour déclencher des fluctuations
SIGMA_1 = 0.6
SIGMA_2 = 0.3    # Amplification par la mémoire
F_CRIT = 0.40    # Seuil un peu plus haut pour éviter les faux positifs
LAMBDA = 1.2     
KAPPA = 0.08     # Gain de rétroaction (Critique : doit être > DECAY * M pour n=2)
N_EXPONENT = 2   
DECAY = 0.015    # Décroissance (oubli)
DIFF = 0.06      # Diffusion (étale la dissonance)
RELAX = 0.04     
S_MAX = 0.04     
M_SAT = 1.0

# --- INITIALISATION (Pur Chaos) ---
# Pas de graine ! Tout est bruit aléatoire faible
F = np.random.uniform(0.0, 0.05, (GRID_SIZE, GRID_SIZE))
M = np.zeros((GRID_SIZE, GRID_SIZE))

# --- CONFIGURATION GRAPHIQUE ---
fig = plt.figure(figsize=(14, 10))
fig.patch.set_facecolor('#111')

gs = GridSpec(3, 2, height_ratios=[2, 2, 1]) 

ax1 = fig.add_subplot(gs[0, :]) # Dissonance F
ax2 = fig.add_subplot(gs[1, :]) # Mémoire M
ax3 = fig.add_subplot(gs[2, :]) # Graphique Temporel

ax1.set_facecolor('#111')
ax2.set_facecolor('#111')
ax3.set_facecolor('#111')
ax3.grid(True, color='#333', linestyle='--', alpha=0.5)

cmap_F = LinearSegmentedColormap.from_list("F", ["navy", "cyan", "white", "red"])
cmap_M = LinearSegmentedColormap.from_list("M", ["black", "gray", "gold", "yellow", "white"])

im_F = ax1.imshow(F, cmap=cmap_F, vmin=0, vmax=1.5)
im_M = ax2.imshow(M, cmap=cmap_M, vmin=0, vmax=3.0) 

ax1.set_title("Dissonance (F) - Bruit Pur", color='white', fontsize=12)
ax2.set_title("Mémoire (M) - Émergence de Singularité", color='white', fontsize=12)

# Graphique
ax3.set_title("Diagnostic : Émergence Spontanée (Max M vs Mean M)", color='white', fontsize=12)
ax3.set_xlabel("Temps (Frames)", color='white')
ax3.set_ylabel("Valeur", color='white')
ax3.set_facecolor('#111')
ax3.tick_params(colors='white')
ax3.spines['bottom'].set_color('white')
ax3.spines['top'].set_color('white')
ax3.spines['left'].set_color('white')
ax3.spines['right'].set_color('white')

line_max, = ax3.plot([], [], color='red', label='Max M (Local)', linewidth=2)
line_mean, = ax3.plot([], [], color='cyan', label='Mean M (Global)', linewidth=2)
line_source, = ax3.plot([], [], color='yellow', label='Source S(t)', linewidth=1, linestyle='--')

ax3.legend(loc='upper left', facecolor='#222', edgecolor='white', labelcolor='white')

history_max = []
history_mean = []
history_source = []

def update(frame):
    global F, M
    
    # 1. Moyenne Globale
    mean_M = np.mean(M)
    
    # 2. Source Homeostatique
    current_source = S_MAX * max(0.0, 1.0 - mean_M / M_SAT)
    
    # 3. Bruit Multiplicatif
    sigma_field = SIGMA_0 + SIGMA_1 * F + SIGMA_2 * M
    noise = sigma_field * np.random.randn(GRID_SIZE, GRID_SIZE)
    
    # 4. Laplacien
    lap = (np.roll(F, 1, 0) + np.roll(F, -1, 0) + 
           np.roll(F, 1, 1) + np.roll(F, -1, 1) - 4 * F)
    
    # 5. Équation de F
    dF = DIFF * lap - RELAX * F + current_source + noise
    F = F + DT * dF
    F = np.maximum(F, 0)
    
    # 6. Équation de M (Émergence)
    delta_linear = np.zeros_like(M)
    mask = F > F_CRIT
    delta_linear[mask] = LAMBDA * (F[mask] - F_CRIT)
    
    feedback_nonlinear = KAPPA * (M ** N_EXPONENT)
    decay_term = DECAY * M
    
    dM = delta_linear + feedback_nonlinear - decay_term
    M = M + DT * dM
    
    # Pas de clip strict pour voir l'explosion réelle
    M_clipped = np.clip(M, 0, 5.0) 
    
    # Mise à jour visuelle
    im_F.set_array(F)
    im_M.set_array(M_clipped)
    
    # Mise à jour graphique
    current_max = np.max(M)
    current_mean = np.mean(M)
    
    history_max.append(current_max)
    history_mean.append(current_mean)
    history_source.append(current_source)
    
    window = 200
    if len(history_max) > window:
        line_max.set_data(range(len(history_max)-window, len(history_max)), history_max[-window:])
        line_mean.set_data(range(len(history_mean)-window, len(history_mean)), history_mean[-window:])
        line_source.set_data(range(len(history_source)-window, len(history_source)), history_source[-window:])
    else:
        line_max.set_data(range(len(history_max)), history_max)
        line_mean.set_data(range(len(history_mean)), history_mean)
        line_source.set_data(range(len(history_source)), history_source)
        
    ax3.relim()
    ax3.autoscale_view()
    
    stats = f"Frame: {frame}\nMax M: {current_max:.4f}\nMean M: {current_mean:.4f}\nSource: {current_source:.4f}"
    ax1.text(0.02, 0.95, stats, transform=ax1.transAxes, color='white', fontsize=10, verticalalignment='top', bbox=dict(facecolor='#000', alpha=0.7))
    
    return [im_F, im_M, line_max, line_mean, line_source]

# --- LANCEMENT ---
print("Lancement MRCC v4.3 - Émergence Pure (Sans Graine)")
print("Attente d'une fluctuation critique... (Cela peut prendre 200-500 frames)")
print("Objectif : Voir la ligne ROUGE exploser tandis que la BLEUE reste plate.")

try:
    ani = animation.FuncAnimation(fig, update, frames=FRAMES, interval=30, blit=True)
    plt.tight_layout()
    plt.show()
except Exception as e:
    print(f"Erreur : {e}")
    plt.show()
