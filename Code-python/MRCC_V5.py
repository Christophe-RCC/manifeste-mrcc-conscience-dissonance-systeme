#Python version 3.12.10
# MRCC v5.0 - VERSION STABLE (Sans force de rappel artificielle)
# Ce script utilise la puissance 1.5 et le lissage pour un rebond organique.
# Il repose sur l'équilibre naturel des paramètres pour maintenir les structures.

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import warnings

warnings.filterwarnings('ignore')

# --- PARAMÈTRES PHYSIQUES (Le "Moteur" de l'univers) ---

GRID_SIZE = 150  # La taille de la grille (150x150 pixels).
FRAMES = 800     # Durée de la simulation en secondes (frames).
DT = 0.05        # La vitesse du temps.

# --- 1. LA DISSONANCE (F) : La "Douleur" ou le "Bruit" qui déclenche tout ---

DIFF = 0.0005          # [CRITIQUE] Vitesse de propagation de la douleur.
# Bas pour isoler les structures (évite la soupe).

RELAX = 0.04          # Vitesse à laquelle la douleur "s'apaise" naturellement.

S_MAX = 0.00003        # [CRITIQUE] La "Source" de douleur externe.
# Très bas pour ne créer que quelques graines isolées.

F_CRIT = 0.35         # Le "Seuil de Trauma". La douleur doit dépasser ce niveau pour créer de la mémoire.

# --- 2. LA MÉMOIRE (M) : La "Matière" ou les "Traumas" accumulés ---

KAPPA = 0.12          # [CRITIQUE] La force du "Feedback" (Auto-renforcement).
# Assez fort pour créer des points nets, mais pas trop pour éviter l'explosion.

DECAY = 0.02         # L'"Oubli" naturel. La mémoire se dégrade avec le temps.
# Ajusté pour être assez faible pour laisser la trace, mais assez fort pour éviter la saturation totale.

MASS = 0.8            # L'"Inertie" de la mémoire.
# Permet le "battement de cœur" (le rebond).

FRICTION = 0.4        # Le "Frottement" (L'usure, la fatigue).
# Amortit les oscillations pour éviter l'effondrement à 0.

GAMMA_BOUNCE = 0.5    # La "Pression de Dégénérescence" (Le Rebond Quantique).
# Réduit pour un rebond plus doux (ressort).

M_PLANCK = 12.0       # La "Limite de Planck" (La densité maximale).
# Ne pas changer.

EPSILON = 1e-3        # Un petit correctif numérique.
# Ne pas toucher.

SEUIL_HAWKING = 4.0   # Le "Seuil d'Évaporation".
# L'évaporation ne s'active que pour les gros objets (évite de tuer les graines).

# --- PARAMÈTRES MANQUANTS (Retour v4.x) ---
GAMMA_EVAP = 0.008       # Force de l'évaporation pour les objets matures.
SIGMA_0 = 0.06           # Bruit de fond constant.
SIGMA_1 = 0.7            # Bruit dépendant de F.
SIGMA_2 = 0.25           # Bruit dépendant de M.
LAMBDA = 1.0             # Force d'accumulation de la mémoire.
N_EXPONENT = 2           # Exposant du feedback non-linéaire.

# --- INITIALISATION ---
F = np.random.uniform(0, 0.05, (GRID_SIZE, GRID_SIZE))
M = np.zeros((GRID_SIZE, GRID_SIZE))
V = np.zeros((GRID_SIZE, GRID_SIZE))

# --- CONFIGURATION GRAPHIQUE ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
ax1, ax2, ax3 = axes

cmap_F = LinearSegmentedColormap.from_list("F_brutal", ["navy", "cyan", "white", "red"], N=256)

im_F = ax1.imshow(F, cmap=cmap_F, vmin=0, vmax=1.5)
ax1.set_title("Dissonance (F)\nBruit / Douleur", color='white')
ax1.set_xticks([]); ax1.set_yticks([])

im_M = ax2.imshow(M, cmap='inferno', vmin=0, vmax=M_PLANCK)
ax2.set_title("Mémoire (M)\nMatière / Traumas", color='white')
ax2.set_xticks([]); ax2.set_yticks([])

line_max, = ax3.plot([], [], color='red', label='Max M (Singularité)')
line_mean, = ax3.plot([], [], color='blue', label='Moyenne M')
line_v, = ax3.plot([], [], color='green', linestyle='--', label='Vitesse (Inertie)')
ax3.set_xlim(0, FRAMES)
ax3.set_ylim(0, M_PLANCK + 2)
ax3.set_xlabel("Temps (Frames)")
ax3.set_ylabel("Densité / Vitesse")
ax3.legend(facecolor='#222', edgecolor='white', labelcolor='white')
ax3.grid(True, alpha=0.3)
ax3.set_facecolor('#111')
ax3.tick_params(colors='white')

history_max = []
history_mean = []
history_v = []

# --- ALGORITHME DE THOMAS (Résolution Tridiagonale) ---
def solve_tridiagonal(a, b, c, d):
    n = len(d)
    c_prime = np.zeros(n)
    d_prime = np.zeros(n)
    x = np.zeros(n)

    c_prime[0] = c[0] / b[0]
    d_prime[0] = d[0] / b[0]

    for i in range(1, n):
        denom = b[i] - a[i] * c_prime[i-1]
        if abs(denom) < 1e-12:
            denom = 1e-12 
        c_prime[i] = c[i] / denom if i < n-1 else 0
        d_prime[i] = (d[i] - a[i] * d_prime[i-1]) / denom

    x[n-1] = d_prime[n-1]
    for i in range(n-2, -1, -1):
        x[i] = d_prime[i] - c_prime[i] * x[i+1]

    return x

def crank_nicolson_step(F, dt, diff_coef):
    N = F.shape[0]
    alpha = 0.5 * dt * diff_coef
    
    a_diag = -alpha * np.ones(N)
    b_diag = (1 + 2*alpha) * np.ones(N)
    c_diag = -alpha * np.ones(N)
    
    a_diag[0] = 0.0
    c_diag[-1] = 0.0

    F_star = F.copy()
    for i in range(N):
        row = F[i, :]
        rhs = (1 - 2*alpha) * row
        F_star[i, :] = solve_tridiagonal(a_diag, b_diag, c_diag, rhs)

    F_new = F_star.copy()
    for j in range(N):
        col = F_star[:, j]
        rhs = (1 - 2*alpha) * col
        F_new[:, j] = solve_tridiagonal(a_diag, b_diag, c_diag, rhs)

    return F_new

def quantum_bounce_pressure(M, M_planck, gamma, eps):
    """
    Version STABLE : Puissance 1.5 + Lissage 0.1
    Crée un rebond progressif (ressort) sans force de rappel artificielle.
    """
    distance = M_planck - M
    pressure = np.zeros_like(M)
    mask = distance > eps
    
    # La formule corrigée : Puissance 1.5 + lissage 0.1
    # Cela évite la division par zéro et adoucit le rebond
    pressure[mask] = gamma / ( (distance[mask] ** 1.5) + 0.1 )
    
    # Pour les zones très proches (distance < eps), on met une pression massive mais finie
    pressure[~mask] = gamma * 1000.0 
    
    return pressure

# --- DANS LA FONCTION init() ---
def init():
    line_max.set_data([], [])
    line_mean.set_data([], [])
    line_v.set_data([], [])
    
    global stats_text_obj
    stats_text_obj = fig.text(0.02, 0.98, "", transform=fig.transFigure, 
             color='white', fontsize=10, verticalalignment='top', 
             fontfamily='monospace', 
             bbox=dict(facecolor='#000', alpha=0.8, edgecolor='none'))
    
    return [im_F, im_M, line_max, line_mean, line_v, stats_text_obj]

# --- DANS LA FONCTION update() ---
def update(frame):
    global F, M, V, stats_text_obj
    
    # 1. DYNAMIQUE DE F (Douleur)
    current_source = S_MAX * max(0.0, 1.0 - np.mean(M) / M_PLANCK)
    F_diffused = crank_nicolson_step(F, DT, DIFF)
    
    sigma_field = SIGMA_0 + SIGMA_1 * F_diffused + SIGMA_2 * M
    noise = sigma_field * np.random.normal(0, 1, F.shape)
    
    dF_relax = -RELAX * F_diffused + current_source + noise
    F_new = F_diffused + DT * dF_relax
    F = np.maximum(F_new, 0)

    # 2. DYNAMIQUE DE M (Mémoire)
    mask_Fcrit = F > F_CRIT
    force_accum = np.zeros_like(M)
    force_accum[mask_Fcrit] = LAMBDA * (F[mask_Fcrit] - F_CRIT)
    
    force_feedback = KAPPA * (M ** N_EXPONENT)
    force_decay = DECAY * M
    force_pressure = quantum_bounce_pressure(M, M_PLANCK, GAMMA_BOUNCE, EPSILON)
    mask_mature = M > SEUIL_HAWKING
    
    hawking_term = np.zeros_like(M)
    hawking_term[mask_mature] = GAMMA_EVAP / (M[mask_mature]**2 + EPSILON)
    
    # Calcul de l'Accélération (Newton : F = ma => a = F/m)
    # Forces nettes = Accumulation + Feedback - Déclin - Pression - Évaporation
    net_force = force_accum + force_feedback - force_decay - hawking_term - force_pressure
    
    acceleration = (net_force - FRICTION * V) / MASS
    
    V += DT * acceleration
    M += DT * V
    M = np.clip(M, 0, M_PLANCK + 0.5)
    M = np.maximum(M, 0)

    # --- MISE À JOUR VISUELLE ---
    im_F.set_data(F)
    im_M.set_data(M)
    
    # Statistiques
    max_M = np.max(M)
    mean_M = np.mean(M)
    mean_V = np.mean(np.abs(V))
    max_F = np.max(F)
    mean_F = np.mean(F)
    
    # Compteur de singularités
    SEUIL_SING = M_PLANCK * 0.8
    nombre_sing = np.sum(M > SEUIL_SING)
    
    history_max.append(max_M)
    history_mean.append(mean_M)
    history_v.append(mean_V)
    
    if len(history_max) > FRAMES:
        history_max.pop(0)
        history_mean.pop(0)
        history_v.pop(0)
    
    line_max.set_data(range(len(history_max)), history_max)
    line_mean.set_data(range(len(history_mean)), history_mean)
    line_v.set_data(range(len(history_v)), history_v)

    # --- AFFICHAGE DES STATS ---
    stats_text = (
        f"Frame: {frame}\n"
        f"Max M: {max_M:.2f} / {M_PLANCK}\n"
        f"Moyenne M: {mean_M:.2f}\n"
        f"Singularités (>80%): {nombre_sing}\n"
        f"Max F: {max_F:.2f}\n"
        f"Vitesse: {mean_V:.2f}\n"
        f"Source: {current_source:.4f}"
    )
    
    stats_text_obj.set_text(stats_text)
    
    return [im_F, im_M, line_max, line_mean, line_v, stats_text_obj]

print("Lancement MRCC v5.0 - VERSION STABLE (Rebond Organique 1.5)")
print("Attendez : la simulation va créer des îlots isolés avec un rebond doux.")

try:
    ani = animation.FuncAnimation(fig, update, init_func=init, frames=FRAMES, interval=30, blit=False)
    plt.tight_layout()
    plt.show()
except Exception as e:
    print(f"Erreur : {e}")
    plt.show()
