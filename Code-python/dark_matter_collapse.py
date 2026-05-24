#python version 3.12.10

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap

# --- CONFIGURATION PHYSIQUE MRCC ---
GRID_SIZE = 100
DT = 0.05

# Paramètres de la "Matière Noire" (Mémoire M)
GRAVITY_STRENGTH = 0.15  
DECAY_RATE = 0.005       

# Paramètres de l'événement (Dissonance F)
NOISE_BASE = 0.02
NOISE_INTENSITY = 50.0  

FEEDBACK = 0.005

# --- INITIALISATION ---
F = np.zeros((GRID_SIZE, GRID_SIZE))

# Positions initiales (Tuples) valable pour vitesse 1
#source_1_pos = (GRID_SIZE // 4, GRID_SIZE // 2)
#source_2_pos = (3 * GRID_SIZE // 4, GRID_SIZE // 2)

# Changez les positions de départ pour qu'elles soient compatibles avec la vitesse 2
source_1_pos = (24, GRID_SIZE // 2)
source_2_pos = (76, GRID_SIZE // 2)

# Initialiser F avec deux pics
F[source_1_pos] = 1.0
F[source_2_pos] = 1.0

M = np.zeros((GRID_SIZE, GRID_SIZE))

# --- VISUALISATION ---
cmap_F = LinearSegmentedColormap.from_list("F", ["blue", "white", "red"])
cmap_M = LinearSegmentedColormap.from_list("M", ["black", "gray", "gold"])

fig, ax = plt.subplots(figsize=(10, 10))
fig.patch.set_facecolor('#111')
ax.set_facecolor('#111')

im_F = ax.imshow(F, cmap=cmap_F, vmin=0, vmax=2.0, origin='lower')
im_M = ax.imshow(M, cmap=cmap_M, vmin=0, vmax=1.0, origin='lower', alpha=0.6)

ax.set_title("Simulation Bullet Cluster MRCC : Collision d'Événements\n(Le visible F passe, la Mémoire M reste)", color='white', fontsize=14)
ax.set_xlabel("Espace-Temps")
ax.set_ylabel("Espace-Temps")
ax.set_xticks([])
ax.set_yticks([])

stats_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, color='white', fontsize=10, verticalalignment='top')

# --- LOGIQUE PHYSIQUE MRCC ---
def update(frame):
    global F, M, source_1_pos, source_2_pos
    
    # 1. Mouvement des sources (Collision à vitesse 2)
    if frame < 100:
        r1, c1 = source_1_pos
        r2, c2 = source_2_pos
        
        # Vitesse
        source_1_pos = (r1 + 2, c1)
        source_2_pos = (r2 - 2, c2)
        
        # Reset de la grille F
        F[:] = 0
        
        # Fonction pour projeter l'énergie sur les voisins (corrige l'effet de saut)
        def add_energy(pos, strength):
            r, c = pos
            radius = 2  # Rayon d'impact adapté à la vitesse
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                        dist = np.sqrt(dr*dr + dc*dc)
                        if dist <= radius:
                            # Énergie décroissante avec la distance
                            energy = strength * (1 - dist / radius)
                            F[nr, nc] += energy

        add_energy(source_1_pos, 1.0)
        add_energy(source_2_pos, 1.0)
    
    # 2. Diffusion de F (L'événement se propage)
    lap_F = (np.roll(F, 1, 0) + np.roll(F, -1, 0) + 
             np.roll(F, 1, 1) + np.roll(F, -1, 1) - 4 * F)
    
    # 3. Interaction Gravitationnelle (M attire F)
    grad_M_x = np.roll(M, 1, 0) - np.roll(M, -1, 0)
    grad_M_y = np.roll(M, 1, 1) - np.roll(M, -1, 1)
    gravity_force = GRAVITY_STRENGTH * (grad_M_x + grad_M_y)
    
    # 4. Bruit Multiplicatif (Distorsion)
    noise = (NOISE_BASE + NOISE_INTENSITY * M) * np.random.randn(GRID_SIZE, GRID_SIZE)
    
    # 5. Mise à jour de F (Équation complète)
    dF = 0.05 * lap_F + gravity_force + noise
    F = F + DT * dF
    F = np.maximum(F, 0)
    
    # 6. Mise à jour de M (avec rétroaction non linéaire)
    # Paramètres pour la rétroaction
    feedback_gain = FEEDBACK  # ajuste si nécessaire
    non_linear_power = 2  # puissance de rétroaction
    
    # Calcul de la rétroaction
    feedback = feedback_gain * (M ** non_linear_power)
    
    # Mise à jour de M
    delta_M = 0.1 * (F - 0.5) * (F > 0.5).astype(float)
    M = M * (1 - DECAY_RATE) + delta_M + feedback
    M = np.clip(M, 0, 1)
    
    # Mise à jour visuelle
    im_F.set_array(F)
    im_M.set_array(M)
    
    # Stats
    total_M = np.sum(M)
    stats_text.set_text(f"Frame: {frame}\nMatière Noire (M): {total_M:.2f}")
    
    return [im_F, im_M, stats_text]

# --- LANCEMENT ---
print("Simulation : Collision d'événements et formation de Matière Noire (Mémoire)...")
try:
    ani = animation.FuncAnimation(fig, update, frames=15000, interval=50, blit=True)
    plt.tight_layout()
    plt.show()
except Exception as e:
    print(f"Erreur lors du lancement de l'animation : {e}")
    plt.show()
