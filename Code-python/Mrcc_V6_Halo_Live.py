import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# 1. CONFIGURATION (Basée sur l'Annexe 2.1 du MRCC v6.0)
# =============================================================================

N = 256
L = 10.0
dx = L / N
dt = 0.01  # Pas de temps ajusté pour la stabilité de l'intégration du 2nd ordre

# Paramètres physiques
mu = 0.1           # Inertie Causale
gamma_fric = 1.4    # Friction dynamique
lambda_accum = 0.8  # Taux d'accumulation de mémoire
gamma_bounce = 0.2  # Force de la pression de rebond
beta = 1.8          # Exposant de "dureté" de la limite
epsilon = 1e-10     # Régularisation numérique
M_planck = 1.0      # Densité critique maximale

# Paramètres pour l'Énergie Libre F
D_base = 0.0005
alpha_conn = -0.55  # L'apprentissage augmente la diffusion
lambda_relax = -0.1
sigma_noise = 0.9
source_F = 0.02     # Flux d'énergie externe constant

# Initialisation des champs
M = np.zeros((N, N))
F = np.zeros((N, N))
v_M = np.zeros((N, N))

# Source initiale : Une "dissonance" centrale
cy, cx = N // 2, N // 2
y, x = np.ogrid[:N, :N]
dist = np.sqrt((x - cx)**2 + (y - cy)**2)

# On injecte une forte dissonance F au centre
F += 3.0 * np.exp(-(dist**2) / 50.0)

print("Démarrage Simulation MRCC v6.2 (Visualisation Temps Réel)")
print(f"Paramètres: mu={mu}, gamma_fric={gamma_fric}, beta={beta}, M_planck={M_planck}")

# =============================================================================
# 2. FONCTIONS DYNAMIQUES
# =============================================================================

def compute_laplacian(field):
    """Calcule le Laplacien avec conditions aux limites périodiques."""
    return (
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field
    ) / (dx * dx)

def update_step(M, F, v_M, dt):
    # --- 1. ÉVOLUTION DE F ---
    D = D_base + alpha_conn * M
    
    grad_F_x = np.gradient(F, dx, axis=1)
    grad_F_y = np.gradient(F, dx, axis=0)
    grad_D_x = np.gradient(D, dx, axis=1)
    grad_D_y = np.gradient(D, dx, axis=0)
    
    flux_X = D * grad_F_x
    flux_Y = D * grad_F_y
    
    div_flux_x = np.gradient(flux_X, dx, axis=1)
    div_flux_y = np.gradient(flux_Y, dx, axis=0)
    
    diffusion_F = div_flux_x + div_flux_y
    
    noise_F = np.random.normal(0, sigma_noise, F.shape)
    dF_dt = diffusion_F - lambda_relax * F + source_F + noise_F
    
    F_new = F + dt * dF_dt
    F_new = np.clip(F_new, -2.0, 3.0)

    # --- 2. ÉVOLUTION DE M ---
    F_crit = 0.5
    force_accum = lambda_accum * np.maximum(0, F_new - F_crit)
    
    delta_M = M_planck - M
    pressure = np.zeros_like(M)
    mask = delta_M > epsilon
    pressure[mask] = gamma_bounce / (np.power(delta_M[mask], beta) + epsilon)
    
    accel_M = (force_accum - pressure) / mu
    
    v_M_new = v_M + dt * (accel_M - gamma_fric * v_M)
    M_new = M + dt * v_M_new
    
    # Sécurité : Rebond si dépassement critique
    if np.any(M_new > M_planck * 1.05):
        v_M_new[M_new > M_planck * 1.05] *= -0.5
        M_new = np.clip(M_new, 0, M_planck * 1.1)

    M_new = np.maximum(0, M_new)
    
    return M_new, F_new, v_M_new

# =============================================================================
# 3. INITIALISATION DE LA VISUALISATION (Temps Réel)
# =============================================================================

# Création de la figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
plt.subplots_adjust(left=0.02, right=0.98, wspace=0.0) # Marges serrées pour performance

# Configuration de l'axe 1 (M)
im1 = ax1.imshow(M, cmap='viridis', origin='lower', extent=[-L/2, L/2, -L/2, L/2], 
                 vmin=0, vmax=M_planck * 1.1, interpolation='bilinear')
ax1.set_title("Mémoire (M) - Densité Causale", fontsize=12)
ax1.set_xlabel("X | Y")
ax1.set_ylabel("Y")
ax1.set_aspect('equal', 'box')

# Configuration de l'axe 2 (F)
im2 = ax2.imshow(F, cmap='RdBu_r', origin='lower', extent=[-L/2, L/2, -L/2, L/2], 
                 vmin=-2.0, vmax=3.0, interpolation='bilinear')
ax2.set_title("Énergie Libre (F) - Dissonance", fontsize=12)
ax2.set_xlabel("X | Y")
ax2.set_ylabel("Y")
ax2.set_aspect('equal', 'box')

# Ajout d'un texte pour les stats
text_stats = fig.text(0.01, 0.01, "", fontsize=10, verticalalignment='bottom', color='green')

# Barre de progression simulée (simple compteur)
step_count = 0
total_steps = 2000

def on_close(event):
    raise SystemExit

fig.canvas.mpl_connect('close_event', on_close)

# =============================================================================
# 4. BOUCLE DE SIMULATION EN TEMPS RÉEL
# =============================================================================

try:
    for t in range(total_steps):
        # Mise à jour du calcul physique
        M, F, v_M = update_step(M, F, v_M, dt)
        
        # Mise à jour des graphiques (très rapide)
        im1.set_data(M)
        im2.set_data(F)
        
        # Mise à jour des textes de statistiques (toutes les 50 étapes pour ne pas ralentir)
        if t % 50 == 0:
            max_M = np.max(M)
            max_F = np.max(F)
            mean_M = np.mean(M)
            
            # Mise à jour du texte dans la figure
            info_text = f"Step: {t}/{total_steps}\nMax M: {max_M:.3f}\nMax F: {max_F:.3f}\nMean M: {mean_M:.3f}"
            text_stats.set_text(info_text)
            
            # Affichage dans la console (optionnel, pour les logs)
            # print(f"Step {t}: Max(M) = {max_M:.4f}, Max(F) = {max_F:.4f}")
        
        # Rafraîchissement de l'affichage
        # pause(0.001) permet de laisser l'interface se mettre à jour
        plt.pause(0.001)
        
        if np.isnan(max_M) or np.isnan(max_F):
            print("ERREUR: Instabilité numérique détectée.")
            break

except KeyboardInterrupt:
    print("\nSimulation interrompue par l'utilisateur.")
except Exception as e:
    print(f"\nErreur inattendue : {e}")

# Si on sort de la boucle proprement
if not np.isnan(max_M):
    print("\n--- FIN DE SIMULATION ---")
    print(f"Max(M) = {max_M:.4f} | Max(F) = {max_F:.4f}")

else:
    plt.close()
    print("Simulation échouée.")
