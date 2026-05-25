#python version 3.12.10

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

# --- CONFIGURATION (v4.6 - Chronomètre de Vie) ---
GRID_SIZE = 150
DT = 0.05
# On lance très longtemps pour voir si la saturation est lente ou rapide
FRAMES = 10000 

# Paramètres (par default)
#KAPPA = 0.035      
#DIFF = 0.08        
#DECAY = 0.025      
#SIGMA_0 = 0.05
#SIGMA_1 = 0.6
#SIGMA_2 = 0.2
#F_CRIT = 0.35
#LAMBDA = 0.8
#N_EXPONENT = 2
#RELAX = 0.04
#S_MAX = 0.025
#M_SAT = 1.0
#M_PLANCK = 12.0

# Paramètres (On garde ceux qui ont fait saturer, pour observer le processus)
KAPPA = 0.035      
DIFF = 0.020        
DECAY = 0.005      
SIGMA_0 = 0.05
SIGMA_1 = 0.6
SIGMA_2 = 0.2
F_CRIT = 0.35
LAMBDA = 0.8
N_EXPONENT = 2
RELAX = 0.04
S_MAX = 0.025
M_SAT = 1.0
M_PLANCK = 12.0

# --- SEUILS DE VIE ---
# Phase 1 : Jeunesse (0% de saturation)
# Phase 2 : Maturité (Singularités locales, < 5% saturation)
# Phase 3 : Vieillesse (5% - 20% saturation)
# Phase 4 : Mort (> 20% saturation)
SATURATION_MATURE = 0.05
SATURATION_OLD = 0.20

# --- INITIALISATION ---
F = np.random.uniform(0.0, 0.05, (GRID_SIZE, GRID_SIZE))
M = np.zeros((GRID_SIZE, GRID_SIZE))

# --- GRAPHIQUE ---
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('#111')
gs = GridSpec(3, 3, height_ratios=[2, 2, 1], width_ratios=[2, 2, 1])

ax1 = fig.add_subplot(gs[0, :2])
ax2 = fig.add_subplot(gs[1, :2])
ax3 = fig.add_subplot(gs[2, :2])
ax_stats = fig.add_subplot(gs[:, 2])

ax1.set_facecolor('#111'); ax2.set_facecolor('#111'); ax3.set_facecolor('#111'); ax_stats.set_facecolor('#111')
ax3.grid(True, color='#333', linestyle='--', alpha=0.5)

cmap_F = LinearSegmentedColormap.from_list("F", ["navy", "cyan", "white", "red"])
cmap_M = LinearSegmentedColormap.from_list("M", ["black", "gray", "gold", "yellow", "white"])

im_F = ax1.imshow(F, cmap=cmap_F, vmin=0, vmax=1.5)
im_M = ax2.imshow(M, cmap=cmap_M, vmin=0, vmax=M_PLANCK)

ax1.set_title("Dissonance (F)", color='white')
ax2.set_title("Mémoire (M) - Cycle de Vie", color='white')

line_max, = ax3.plot([], [], color='red', label='Max M', linewidth=2)
line_mean, = ax3.plot([], [], color='cyan', label='Mean M', linewidth=2)
line_planck, = ax3.plot([], [], color='white', label='% Planck', linewidth=2, linestyle=':')

ax3.legend(loc='upper left', facecolor='#222', edgecolor='white', labelcolor='white')
ax3.set_title("Évolution du Système", color='white')
ax3.set_xlabel("Temps (Frames)", color='white')
ax3.set_ylabel("Valeur / %", color='white')
ax3.tick_params(colors='white')
for spine in ax3.spines.values(): spine.set_color('white')

stats_text = ax_stats.text(0.1, 0.95, '', transform=ax_stats.transAxes, color='white', fontsize=11, verticalalignment='top', fontfamily='monospace')
ax_stats.axis('off')

history_max = []
history_mean = []
history_planck = []
life_phase = "Jeunesse"
death_frame = None

def update(frame):
    global F, M, life_phase, death_frame
    
    mean_M = np.mean(M)
    current_source = S_MAX * max(0.0, 1.0 - mean_M / M_SAT)
    
    sigma_field = SIGMA_0 + SIGMA_1 * F + SIGMA_2 * M
    noise = sigma_field * np.random.randn(GRID_SIZE, GRID_SIZE)
    
    lap = (np.roll(F, 1, 0) + np.roll(F, -1, 0) + 
           np.roll(F, 1, 1) + np.roll(F, -1, 1) - 4 * F)
    
    dF = DIFF * lap - RELAX * F + current_source + noise
    F = F + DT * dF
    F = np.maximum(F, 0)
    
    is_planck = M >= M_PLANCK
    delta_linear = np.zeros_like(M)
    mask = F > F_CRIT
    delta_linear[mask] = LAMBDA * (F[mask] - F_CRIT)
    
    feedback_nonlinear = KAPPA * (M ** N_EXPONENT)
    decay_term = DECAY * M
    
    dM = delta_linear + feedback_nonlinear - decay_term
    dM = np.where(is_planck, 0.0, dM)
    
    M = M + DT * dM
    M = np.clip(M, 0, M_PLANCK)
    M = np.nan_to_num(M, nan=0.0, posinf=M_PLANCK, neginf=0.0)
    F = np.nan_to_num(F, nan=0.0, posinf=1.5, neginf=0.0)
    
    # --- CALCUL DE LA PHASE DE VIE ---
    planck_count = np.sum(is_planck)
    total_cells = GRID_SIZE * GRID_SIZE
    planck_ratio = planck_count / total_cells
    
    if planck_ratio == 0:
        life_phase = "Jeunesse (0% saturation)"
    elif planck_ratio < SATURATION_MATURE:
        life_phase = "Maturité (Singularités locales)"
    elif planck_ratio < SATURATION_OLD:
        life_phase = "Vieillesse (Propagation)"
    else:
        life_phase = "MORT DU SYSTÈME (Saturation Totale)"
        if death_frame is None:
            death_frame = frame
            print(f"!!! MORT DU SYSTÈME à la frame {frame} !!!")
            # On ne coupe pas, on laisse voir la "mort thermique"
    
    # Mise à jour visuelle
    im_F.set_array(F)
    im_M.set_array(M)
    
    # Mise à jour graphique
    current_max = np.max(M)
    current_mean = np.mean(M)
    
    history_max.append(current_max)
    history_mean.append(current_mean)
    history_planck.append(planck_ratio)
    
    window = 500
    if len(history_max) > window:
        line_max.set_data(range(len(history_max)-window, len(history_max)), history_max[-window:])
        line_mean.set_data(range(len(history_mean)-window, len(history_mean)), history_mean[-window:])
        line_planck.set_data(range(len(history_planck)-window, len(history_planck)), history_planck[-window:])
    else:
        line_max.set_data(range(len(history_max)), history_max)
        line_mean.set_data(range(len(history_mean)), history_mean)
        line_planck.set_data(range(len(history_planck)), history_planck)
        
    ax3.relim()
    ax3.autoscale_view()
    
    # Stats détaillées
    stats = (
        f"Frame: {frame:05d}\n"
        f"Phase: {life_phase}\n"
        f"Max M: {current_max:.5f}\n"
        f"Mean M: {current_mean:.5f}\n"
        f"Source: {current_source:.5f}\n"
        f"Planck %: {planck_ratio:.5f}\n"
        f"Planck Nb: {planck_count:05d}\n"
        f"Kappa: {KAPPA:.5f}\n"
        f"Decay: {DECAY:.5f}"
    )
    if death_frame:
        stats += f"\n\nDURÉE DE VIE: {death_frame} frames"
    
    stats_text.set_text(stats)
    
    return [im_F, im_M, line_max, line_mean, line_planck, stats_text]

print("Lancement MRCC v4.6 - Chronomètre de Vie")
print("Observez la transition : Jeunesse -> Maturité -> Vieillesse -> Mort.")
print("Notez la frame où la saturation dépasse 20% (Mort).")

try:
    ani = animation.FuncAnimation(fig, update, frames=FRAMES, interval=30, blit=True)
    plt.tight_layout()
    plt.show()
except Exception as e:
    print(f"Erreur : {e}")
    plt.show()
