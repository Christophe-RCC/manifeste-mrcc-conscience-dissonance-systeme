import numpy as np
import sys
import matplotlib.pyplot as plt

print("--- Simulation MRCC (Correction Effondrement) ---")

# --- 1. CONFIGURATION ---
LAMBDA_LYAP = 2.5
K_RESISTANCE = 0.8
K_ACCEPTE = 1.2

T_MAX = 50.0
DT = 0.01
N_STEPS = int(T_MAX / DT)

INIT_H = 1.5
INIT_V = 5.0

# --- 2. LOGIQUE ---

def get_acceptance(t):
    if t < 0.1:
        return 0.0
    return 1.0 - np.exp(-(t - 0.1) * 2.0)

def run_mrcc_simulation(label, force_acceptance_zero=False):
    temps = np.arange(0, T_MAX, DT)
    entropie = np.zeros(len(temps))
    potentiel = np.zeros(len(temps))
    
    entropie[0] = INIT_H
    potentiel[0] = INIT_V
    
    print(f"Lancement: {label} (Force Acceptation: {force_acceptance_zero})")
    
    divergence_step = -1
    divergence_time = 0.0
    is_dead = False # État du cerveau
    
    for i in range(1, len(temps)):
        t = temps[i-1]
        H = entropie[i-1]
        V = potentiel[i-1]
        
        if force_acceptance_zero:
            accept = 0.0
        else:
            accept = get_acceptance(t)
        
        # --- CALCUL DES TERMES ---
        term_dissonance = (1.0 - accept) * H * LAMBDA_LYAP
        term_plasticite = -K_ACCEPTE * accept * V
        term_relathe = -K_RESISTANCE * (V - 0.1)
        bruit = 5.0 * np.random.randn()
        
        dH_dt = term_dissonance + bruit
        dV_dt = term_plasticite + term_relathe
        
        # Mise à jour
        H_next = H + dH_dt * DT
        V_next = V + dV_dt * DT
        
        # --- GESTION DE LA DIVERGENCE / MORT ---
        if not is_dead:
            if H_next > 100.0:
                # Divergence détectée
                divergence_step = i
                divergence_time = t
                print(f"   >> DIVERGENCE DÉTECTÉE à t={t:.2f} (H={H_next:.2f})")
                is_dead = True # Le cerveau est mort
                
                # On le fait "s'effondrer" à 0 instantanément pour la simulation
                H_next = 0.0
                V_next = 0.0 # On arrête aussi le potentiel
            else:
                # Clip normal pour éviter les NaNs
                H_next = np.clip(H_next, 0, 1e6)
                V_next = np.clip(V_next, -1e6, 1e6)
        else:
            # Si le cerveau est mort, il reste à 0
            H_next = 0.0
            V_next = 0.0
        
        entropie[i] = H_next
        potentiel[i] = V_next
        
    return temps, entropie, potentiel, divergence_time, divergence_step

# --- 3. EXÉCUTION ---

temps_a, h_a, v_a, div_time_a, step_a = run_mrcc_simulation("Cerveau A (Illusion)", force_acceptance_zero=True)
temps_b, h_b, v_b, div_time_b, step_b = run_mrcc_simulation("Cerveau B (MRCC - Effet Papillon)", force_acceptance_zero=False)

# --- 4. RÉSULTATS ---

plt.figure(figsize=(12, 6))

# On trace les deux courbes
plt.plot(temps_a, h_a, label='Cerveau A (Illusion)', color='red', linewidth=2, linestyle='-')
plt.plot(temps_b, h_b, label='Cerveau B (MRCC)', color='blue', linewidth=2, linestyle='--')

# Ajout des lignes de divergence si elles existent
if div_time_a > 0:
    plt.axvline(x=div_time_a, color='red', linestyle=':', alpha=0.8, label=f'Divergence A (t={div_time_a:.2f}s)')
    # Annotation
    plt.text(div_time_a, 50, f'Effondrement à t={div_time_a:.2f}', color='red', fontweight='bold')

if div_time_b > 0:
    plt.axvline(x=div_time_b, color='blue', linestyle=':', alpha=0.8, label=f'Divergence B (t={div_time_b:.2f}s)')
    plt.text(div_time_b, 50, f'Stabilité A (pas d\'effondrement)', color='blue', fontweight='bold') # Exemple

plt.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Seuil de Divergence (H=100)')

plt.xlabel('Temps (s)')
plt.ylabel('Entropie (H)')
plt.title('Simulation MRCC : Comparaison Illusion vs Effet Papillon')
plt.legend(loc='upper right')
plt.grid(True, alpha=0.3)

# Ajustement de l'axe Y pour bien voir la chute à 0
plt.ylim(-5, 120) 

print(f"\n--- Résumé ---")
print(f"Cerveau A : Divergence à t={div_time_a:.2f}s" if div_time_a > 0 else "Cerveau A : Pas de divergence")
print(f"Cerveau B : Divergence à t={div_time_b:.2f}s" if div_time_b > 0 else "Cerveau B : Pas de divergence")

plt.show()
