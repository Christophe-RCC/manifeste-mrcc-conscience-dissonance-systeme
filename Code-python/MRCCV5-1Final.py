#Python version 3.12.10

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap

# ==============================================================================
# SIMULATION MRCC v5.1 - "UNIVERS VIVANT"
# Ajout d'une Source Externe Constante pour maintenir la dynamique.
# ==============================================================================

# --- PARAMÈTRES GLOBAUX ---
GRID_SIZE = 150
DT = 0.015
FRAMES = 1000  # Plus de temps pour voir la stabilité

# --- PARAMÈTRES PHYSIQUES ---
MASS_M = 1.0
FRICTION_M = 0.06

M_PLANCK = 10.0
GAMMA_BOUNCE = 1.5
EPSILON = 1e-3
KAPPA = 0.15
DECAY = 0.01

DIFF = 0.002
RELAX = 0.08
F_CRIT = 0.35

SIGMA_0 = 0.01
SIGMA_1 = 0.6
SIGMA_2 = 0.4

# --- NOUVEAU : SOURCE EXTERNE CONSTANTE (Le "Soleil" de l'univers) ---
# Cette source injecte de l'énergie en permanence pour compenser le frottement.
S_EXT_CONSTANT = 0.0  # Le bruit est déjà une source, avec ou sans cela ne change rien à la mort thermique car rien ne peut se reproduire deux fois exactement de la même manière, la cause de la première fois a déjà eu lieu

# --- INITIALISATION ---
F = np.zeros((GRID_SIZE, GRID_SIZE))
M = np.zeros((GRID_SIZE, GRID_SIZE))
V_M = np.zeros((GRID_SIZE, GRID_SIZE))

# Initialisation :
density_initial = 0.1 * M_PLANCK #si la densité est trop faible, le système ne "nait" pas si aucune source externe n'est présente.
noise_init = np.random.normal(0, 0.1, (GRID_SIZE, GRID_SIZE))
M = np.full((GRID_SIZE, GRID_SIZE), density_initial) + noise_init
M = np.clip(M, 0, M_PLANCK + 0.5)
F = np.random.uniform(0, 0.1, (GRID_SIZE, GRID_SIZE))

# --- VISUALISATION ---
cmap_F = LinearSegmentedColormap.from_list("F", ["blue", "white", "red"])
cmap_M = LinearSegmentedColormap.from_list("M", ["black", "gray", "gold"])

fig, ax = plt.subplots(figsize=(10, 10))
fig.patch.set_facecolor('#000')
ax.set_facecolor('#000')

im_F = ax.imshow(F, cmap=cmap_F, vmin=0, vmax=1.5, origin='lower', extent=[0, GRID_SIZE, 0, GRID_SIZE])
im_M = ax.imshow(M, cmap=cmap_M, vmin=0, vmax=M_PLANCK, origin='lower', extent=[0, GRID_SIZE, 0, GRID_SIZE], alpha=0.8)

ax.set_title("Simulation MRCC v5.1 : Univers Vivant \n"
             "", 
             color='white', fontsize=14, fontweight='bold')
ax.set_xlabel("Espace (X)")
ax.set_ylabel("Espace (Y)")
ax.set_xticks([])
ax.set_yticks([])

stats_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, color='white', fontsize=10, verticalalignment='top')

# --- FONCTIONS ---

def diffuse(field):
    return (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4*field)

def quantum_bounce_pressure(M_field, M_planck, gamma, eps):
    distance = M_planck - M_field
    pressure = np.zeros_like(M_field)
    mask = distance > eps
    pressure[mask] = gamma / (distance[mask] ** 1.5 + 0.1) 
    pressure[~mask] = gamma * 1e4 
    return pressure

def init():
    stats_text.set_text('')
    return [im_F, im_M, stats_text]

def update(frame):
    global F, M, V_M
    
    # --- 1. DYNAMIQUE DE F (Avec Source Externe) ---
    lap_F = diffuse(F)
    
    # Source dépendante de la saturation (homéostasie)
    local_saturation = M / M_PLANCK
    current_source = S_EXT_CONSTANT * np.clip(1.0 - local_saturation, 0.0, 1.0)
    
    # Bruit stochastique
    sigma_field = SIGMA_0 + SIGMA_1 * F + SIGMA_2 * M
    noise = sigma_field * np.random.normal(0, 1, F.shape)
    
    dF = DIFF * lap_F - RELAX * F + current_source + noise
    F += DT * dF
    F = np.maximum(F, 0)

    # --- 2. DYNAMIQUE DE M ---
    mask_Fcrit = F > F_CRIT
    
    force_accum = np.zeros_like(M)
    force_accum[mask_Fcrit] = 2.0 * (F[mask_Fcrit] - F_CRIT)
    
    force_feedback = KAPPA * (M ** 2)
    force_decay = DECAY * M
    force_pressure = quantum_bounce_pressure(M, M_PLANCK, GAMMA_BOUNCE, EPSILON)
    
    net_force = force_accum + force_feedback - force_decay - force_pressure
    acceleration = (net_force - FRICTION_M * V_M) / MASS_M
    
    V_M += DT * acceleration
    M += DT * V_M
    
    M = np.clip(M, 0, M_PLANCK + 1.0)

    # --- 3. VISUALISATION ---
    im_F.set_array(F)
    im_M.set_array(M)
    
    total_M = np.sum(M)
    max_M = np.max(M)
    mean_M = np.mean(M)
    std_M = np.std(M)
    
    # Détection de l'état
    state = "Mort (Effondrement)" if std_M < 0.1 else "Vivant (Mousse Oscillante)"
    
    stats_text.set_text(
        f"Frame: {frame}\n"
        f"Densité Moyenne: {mean_M:.2f}\n"
        f"Max Densité: {max_M:.2f}\n"
        f"Écart-type (Structure): {std_M:.2f}\n"
        f"État: {state}\n"
        f"Source Externe: {S_EXT_CONSTANT} (Active)"
    )
    
    return [im_F, im_M, stats_text]

# --- LANCEMENT ---
print("Lancement Simulation 'Univers Vivant'...")

ani = animation.FuncAnimation(fig, update, init_func=init, frames=FRAMES, interval=30, blit=True)

plt.tight_layout()
plt.show()
