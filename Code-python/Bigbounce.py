#Python version 3.12.10

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- PARAMÈTRES PHYSIQUES ---
GRID_SIZE = 150
FRAMES = 500       # Augmenté pour voir les cycles
DT = 0.02          # Pas de temps plus petit pour la stabilité de l'intégration du 2nd ordre

# Coefficients de l'équation de la mémoire (v5.0 - Inertie)
KAPPA = 0.002       # Feedback non-linéaire (formation de singularités)
DIFF = 0.02         # Diffusion de la dissonance
RELAX = 0.01       # Relaxation naturelle de F
DECAY = 0.01       # Déclin naturel de M (mémoire à long terme)
S_MAX = 0.5        # Source externe de dissonance
F_CRIT = 0.25      # Seuil d'activation de la mémoire
M_PLANCK = 12.0    # Limite de densité (Horizon)

# --- NOUVEAUX PARAMÈTRES POUR L'INERTIE (v5.0) ---
MASS = 0.5         # "Masse" du système (Inertie : résistance au changement de vitesse)
FRICTION = 0.8     # Amortissement (Friction : dissipe l'énergie pour éviter l'explosion)
GAMMA_BOUNCE = 1.0 # Force de répulsion quantique (Pression de dégénérescence)
EPSILON = 1e-3     # Lissage pour éviter la division par zéro

# --- INITIALISATION ---
# F : Dissonance (Énergie libre)
F = np.random.uniform(0, 0.05, (GRID_SIZE, GRID_SIZE))
# M : Densité de Mémoire (Position)
M = np.zeros((GRID_SIZE, GRID_SIZE))
# V : Vitesse de la Mémoire (Nouveau : Inertie)
V = np.zeros((GRID_SIZE, GRID_SIZE))

# --- CONFIGURATION GRAPHIQUE ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
ax1, ax2, ax3 = axes

# Images
im_F = ax1.imshow(F, cmap='coolwarm', vmin=0, vmax=1.5)
ax1.set_title("Dissonance (F)\nSignal de la douleur")
ax1.set_xticks([]); ax1.set_yticks([])

im_M = ax2.imshow(M, cmap='inferno', vmin=0, vmax=M_PLANCK)
ax2.set_title("Mémoire (M)\nDensité Causale")
ax2.set_xticks([]); ax2.set_yticks([])

# Graphique d'évolution
line_max, = ax3.plot([], [], color='red', label='Max M (Singularité)')
line_mean, = ax3.plot([], [], color='blue', label='Moyenne M')
line_v, = ax3.plot([], [], color='green', linestyle='--', label='Vitesse Moyenne (Inertie)')
ax3.set_xlim(0, FRAMES)
ax3.set_ylim(0, M_PLANCK + 2)
ax3.set_xlabel("Temps (Frames)")
ax3.set_ylabel("Densité / Vitesse")
ax3.legend()
ax3.grid(True, alpha=0.3)

# Historiques
history_max = []
history_mean = []
history_v = []

# --- FONCTIONS UTILITAIRES ---
def diffuse(field):
    """Calcul du Laplacien pour la diffusion (voisins 4 directions)"""
    return (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4*field)

def quantum_bounce_pressure(M, M_planck, gamma, eps):
    """
    Calcule la pression de dégénérescence quantique.
    Devient infinie quand M approche M_planck.
    """
    distance = M_planck - M
    # On utilise un masque pour éviter les divisions par zéro ou négatives
    # Si distance < eps, on force une pression énorme
    pressure = np.zeros_like(M)
    mask = distance > eps
    pressure[mask] = gamma / (distance[mask] ** 2)
    # Pour les zones très proches, on ajoute une force de répulsion massive
    pressure[~mask] = gamma * 1e6 
    return pressure

# --- BOUCLE DE SIMULATION ---
def init():
    line_max.set_data([], [])
    line_mean.set_data([], [])
    line_v.set_data([], [])
    return [im_F, im_M, line_max, line_mean, line_v]

def update(frame):
    global F, M, V
    
    # 1. DYNAMIQUE DE LA DISSONANCE (F) - Reste du 1er ordre (rapide)
    lap_F = diffuse(F)
    # La source diminue si la mémoire globale est saturée (homéostasie globale)
    current_source = S_MAX * max(0.0, 1.0 - np.mean(M) / M_PLANCK)
    
    # Équation de F : Diffusion - Relaxation + Source
    dF = DIFF * lap_F - RELAX * F + current_source
    F += DT * dF
    F = np.maximum(F, 0) # F ne peut pas être négative

    # 2. DYNAMIQUE DE LA MÉMOIRE (M) - Passage au 2nd ordre (Inertie)
    # Forces agissant sur la mémoire :
    
    # A. Accumulation linéaire (si F > F_crit)
    mask_Fcrit = F > F_CRIT
    force_accum = np.zeros_like(M)
    force_accum[mask_Fcrit] = 0.8 * (F[mask_Fcrit] - F_CRIT)
    
    # B. Feedback non-linéaire (Auto-renforcement)
    force_feedback = KAPPA * (M ** 2)
    
    # C. Déclin naturel (Oubli)
    force_decay = DECAY * M
    
    # D. Pression Quantique (Répulsion à l'horizon)
    force_pressure = quantum_bounce_pressure(M, M_PLANCK, GAMMA_BOUNCE, EPSILON)
    
    # Calcul de l'Accélération (Newton : F = ma => a = F/m)
    # Forces nettes = Accumulation + Feedback - Déclin - Pression
    net_force = force_accum + force_feedback - force_decay - force_pressure
    
    # Équation du mouvement (Inertie + Friction) :
    # a = (Force_Nette - Friction * Vitesse) / Masse
    acceleration = (net_force - FRICTION * V) / MASS
    
    # Mise à jour de la Vitesse (Intégration de l'accélération)
    V += DT * acceleration
    
    # Mise à jour de la Position (Mémoire) via la Vitesse
    M += DT * V
    
    # Contraintes physiques (M ne peut pas être négative, et on la limite légèrement avant Planck pour la stabilité numérique)
    # Note : La pression devrait théoriquement empêcher M > M_PLANCK, mais on clip pour éviter les bugs numériques
    M = np.clip(M, 0, M_PLANCK + 0.5) 
    # Si M dépasse légèrement, on le ramène doucement (effet de rebond numérique)
    M = np.maximum(M, 0)

    # --- MISE À JOUR VISUELLE ---
    im_F.set_data(F)
    im_M.set_data(M)
    
    # Statistiques pour le graphique
    max_M = np.max(M)
    mean_M = np.mean(M)
    mean_V = np.mean(np.abs(V)) # On regarde la vitesse absolue pour voir l'agitation
    
    history_max.append(max_M)
    history_mean.append(mean_M)
    history_v.append(mean_V)
    
    # Gestion de la taille de l'historique
    if len(history_max) > FRAMES:
        history_max.pop(0)
        history_mean.pop(0)
        history_v.pop(0)
    
    line_max.set_data(range(len(history_max)), history_max)
    line_mean.set_data(range(len(history_mean)), history_mean)
    line_v.set_data(range(len(history_v)), history_v)

    return [im_F, im_M, line_max, line_mean, line_v]

# --- LANCEMENT ---
ani = animation.FuncAnimation(fig, update, init_func=init, frames=FRAMES, interval=30, blit=True)
plt.tight_layout()
plt.show()
