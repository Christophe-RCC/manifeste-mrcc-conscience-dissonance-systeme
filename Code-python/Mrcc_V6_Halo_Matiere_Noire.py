import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# 1. CONFIGURATION (Basée sur l'Annexe 2.1 du MRCC v6.0)
# =============================================================================

N = 256
L = 10.0
dx = L / N
dt = 0.01  # Pas de temps ajusté pour la stabilité de l'intégration du 2nd ordre

# Paramètres physiques (Strictement issus de ton Annexe 2.1)
mu = 0.1           # Inertie Causale
gamma_fric = 1.4   # Friction dynamique (Dissipation d'énergie en entropie)
lambda_accum = 0.8 # Taux d'accumulation de mémoire
gamma_bounce = 0.2 # Force de la pression de rebond
beta = 1.8         # Exposant de "dureté" de la limite (Annexe 2.1)
epsilon = 1e-10    # Régularisation numérique
M_planck = 1.0     # Densité critique maximale (Seuil de saturation)

# Paramètres pour l'Énergie Libre F (Annexe 2.3)
D_base = 0.0005
alpha_conn = 0.05   # L'apprentissage augmente la diffusion
lambda_relax = -0.1
sigma_noise = 0.01
source_F = 0.01    # Flux d'énergie externe constant

# Initialisation des champs
M = np.zeros((N, N))       # Densité de Mémoire (Buffer)
F = np.zeros((N, N))       # Énergie Libre (Dissonance)
v_M = np.zeros((N, N))     # Vitesse de variation de M (Inertie)

# Source initiale : Une "dissonance" centrale (comme dans ton script V6)
cy, cx = N // 2, N // 2
y, x = np.ogrid[:N, :N]
dist = np.sqrt((x - cx)**2 + (y - cy)**2)

# On injecte une forte dissonance F au centre
F += 3.0 * np.exp(-(dist**2) / 50.0)

print("Démarrage Simulation MRCC v6.2 (Équations Exactes de l'Annexe 2.1)")
print(f"Paramètres: mu={mu}, gamma_fric={gamma_fric}, beta={beta}, M_planck={M_planck}")
print("Le système va tenter de minimiser F tout en respectant la pression de saturation.")

# =============================================================================
# 2. FONCTIONS DYNAMIQUES (Équations de l'Annexe)
# =============================================================================

def compute_laplacian(field):
    """Calcule le Laplacien (diffusion) avec conditions aux limites périodiques."""
    return (
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field
    ) / (dx * dx)

def update_step(M, F, v_M, dt):
    # --- 1. ÉVOLUTION DE F (Annexe 2.3) ---
    # D(M) = D_base + alpha_conn * M
    D = D_base + alpha_conn * M
    
    # Gradient de F et D (pour la diffusion non-linéaire: div(D * grad(F)))
    # Utilisation de différences finies simples pour la vitesse
    grad_F_x = np.gradient(F, dx, axis=1)
    grad_F_y = np.gradient(F, dx, axis=0)
    grad_D_x = np.gradient(D, dx, axis=1)
    grad_D_y = np.gradient(D, dx, axis=0)
    
    # Terme de divergence : d/dx(D * dF/dx) + d/dy(D * dF/dy)
    flux_X = D * grad_F_x
    flux_Y = D * grad_F_y
    
    div_flux_x = np.gradient(flux_X, dx, axis=1)
    div_flux_y = np.gradient(flux_Y, dx, axis=0)
    
    diffusion_F = div_flux_x + div_flux_y
    
    # Équation de F : dF/dt = div(D grad F) - lambda_relax * F + source + noise
    noise_F = np.random.normal(0, sigma_noise, F.shape)
    dF_dt = diffusion_F - lambda_relax * F + source_F + noise_F
    
    F_new = F + dt * dF_dt
    F_new = np.clip(F_new, -2.0, 3.0) # Bornes pour stabilité

    # --- 2. ÉVOLUTION DE M (Annexe 2.1) ---
    # Force d'accumulation : lambda * (F - F_crit)^+
    F_crit = 0.5 # Seuil pour commencer à accumuler la mémoire
    force_accum = lambda_accum * np.maximum(0, F_new - F_crit)
    
    # Pression de Saturation : P_sat = gamma_bounce / ( (M_planck - M)^beta + epsilon )
    # Attention: ne s'applique que si M < M_planck
    delta_M = M_planck - M
    # On évite la division par zéro ou les nombres négatifs
    pressure = np.zeros_like(M)
    mask = delta_M > epsilon
    pressure[mask] = gamma_bounce / (np.power(delta_M[mask], beta) + epsilon)
    
    # Accélération : (Force - Pression) / Inertie
    accel_M = (force_accum - pressure) / mu
    
    # Intégration de l'équation du 2nd ordre (Verlet simplifié ou Euler avec friction)
    # dv/dt = accel - gamma_fric * v
    # dM/dt = v
    v_M_new = v_M + dt * (accel_M - gamma_fric * v_M)
    M_new = M + dt * v_M_new
    
    # Sécurité : M ne doit pas dépasser M_planck de manière incontrôlée
    # Si M > M_planck, on force une rétroaction forte (rebond)
    if np.any(M_new > M_planck * 1.05):
        v_M_new[M_new > M_planck * 1.05] *= -0.5 # Rebond
        M_new = np.clip(M_new, 0, M_planck * 1.1)

    M_new = np.maximum(0, M_new)
    
    return M_new, F_new, v_M_new

# =============================================================================
# 3. SIMULATION
# =============================================================================

steps = 2000
history_M = []
history_F = []

for t in range(steps):
    M, F, v_M = update_step(M, F, v_M, dt)
    
    if t % 100 == 0:
        max_M = np.max(M)
        max_F = np.max(F)
        mean_M = np.mean(M)
        print(f"Step {t}: Max(M) = {max_M:.4f}, Max(F) = {max_F:.4f}, Mean(M) = {mean_M:.4f}")
        
        if np.isnan(max_M):
            print("ERREUR: Instabilité numérique détectée.")
            break
    
    if t % 50 == 0:
        history_M.append(M.copy())
        history_F.append(F.copy())

# =============================================================================
# 4. VISUALISATION (Robuste)
# =============================================================================

if len(history_M) > 0:
    final_M = history_M[-1]
    final_F = history_F[-1]
    
    fig = plt.figure(figsize=(15, 5))
    
    # Axe 1 : Mémoire (M) - La "Matière Noire"
    ax1 = fig.add_subplot(1, 3, 1)
    im1 = ax1.imshow(final_M, cmap='viridis', origin='lower', extent=[-L/2, L/2, -L/2, L/2], 
                     vmin=0, vmax=M_planck * 1.0)
    ax1.set_title("Mémoire (M) - Structure Émergente")
    ax1.set_xlabel("X"); ax1.set_ylabel("Y")
    plt.colorbar(im1, ax=ax1, label="Densité M")
    
    # Axe 2 : Énergie Libre (F) - La Dissonance
    ax2 = fig.add_subplot(1, 3, 2)
    im2 = ax2.imshow(final_F, cmap='RdBu_r', origin='lower', extent=[-L/2, L/2, -L/2, L/2], 
                     vmin=-2, vmax=3)
    ax2.set_title("Énergie Libre (F) - Dissonance Résiduelle")
    ax2.set_xlabel("X"); ax2.set_ylabel("Y")
    plt.colorbar(im2, ax=ax2, label="F")
    
    # Axe 3 : Profil Radial de M
    X, Y = np.meshgrid(np.linspace(-L/2, L/2, N), np.linspace(-L/2, L/2, N))
    r = np.sqrt(X**2 + Y**2)
    r_bins = np.linspace(0, L/2, 100)
    radial_profile = []
    bin_centers = []
    
    for i in range(len(r_bins)-1):
        mask = (r >= r_bins[i]) & (r < r_bins[i+1])
        if np.sum(mask) > 0:
            radial_profile.append(np.mean(final_M[mask]))
            bin_centers.append(np.mean(r[mask]))
    
    ax3 = fig.add_subplot(1, 3, 3)
    ax3.plot(bin_centers, radial_profile, 'o-', color='purple')
    ax3.set_title("Profil Radial de la Mémoire")
    ax3.set_xlabel("Rayon r")
    ax3.set_ylabel("Densité M")
    ax3.grid(True)
    ax3.set_yscale('log')
    
    plt.tight_layout()
    plt.show()
    
    # Analyse
    max_M = np.max(final_M)
    mean_M = np.mean(final_M)
    
    print(f"\n--- RÉSULTAT FINAL ---")
    print(f"Max(M) = {max_M:.4f} (Limit: {M_planck})")
    print(f"Mean(M) = {mean_M:.4f}")
    
    if max_M > 0.9 * M_planck and mean_M < 0.5 * M_planck:
        print("RÉSULTAT : Halo dense au centre, fond moins saturé.")
        print("La pression de saturation a empêché l'effondrement global.")
    elif max_M > 0.9 * M_planck and mean_M > 0.8 * M_planck:
        print("RÉSULTAT : Saturation globale. Le système est tout 'rempli'.")
    else:
        print("RÉSULTAT : Pas de structure forte. La dissonance F n'a pas été convertie en M.")

else:
    print("Échec de la simulation.")
