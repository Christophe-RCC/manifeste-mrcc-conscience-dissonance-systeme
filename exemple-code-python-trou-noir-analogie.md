## 7. Analogie du Trou Noir : La Densité de Causalité et l'Effondrement de la Liberté

### 7.1. Postulat Théorique
Le MRCC postule que la **liberté** (la capacité d'un système à choisir parmi plusieurs trajectoires futures) n'est pas une propriété absolue, mais une fonction décroissante de la **densité de causalité** (la densité d'interactions ou de contraintes gravitationnelles).

*   **État Fluide (Liberté)** : À faible densité, les systèmes maintiennent une haute entropie de trajectoire. Ils peuvent explorer, s'adapter et minimiser la dissonance de manière dynamique.
*   **L'Horizon des Événements** : Il existe un seuil critique de densité ($\rho_{crit}$) au-delà duquel la force de causalité devient si intense que toutes les trajectoires possibles convergent vers un état unique.
*   **La Singularité (Rigidité)** : Au-delà de l'horizon, la variance des états possibles s'annule. Le système perd sa capacité d'adaptation et se fige dans un état unique (mort thermodynamique ou trauma psychologique figé).

> **Hypothèse Unificatrice** : Un trou noir astrophysique et un système psychologique en état de trauma sévère (TSPTC, dépression majeure) obéissent à la même loi : **la densité excessive de causalité annule la liberté de trajectoire, forçant le système vers une singularité unique.**

---

### 7.2. Simulation : Effondrement Causal et Transition de Phase

La simulation ci-dessous modélise 30 particules (systèmes) soumises à une augmentation progressive de la densité de causalité.
*   **Phase Bleue** : Densité faible. Les particules ont des trajectoires variées (liberté, entropie élevée).
*   **Seuil Critique (Ligne Rouge)** : La densité atteint le point de non-retour.
*   **Phase Rouge** : Densité critique. Toutes les particules s'effondrent instantanément vers la singularité (position 0), perdant toute individualité.

#### Code de Simulation (Python)

```python
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
NUM_PARTICLES = 30
MAX_TIME = 300       # Durée de la simulation
SINGULARITY_POS = 0.0
CRITICAL_DENSITY = 0.6 # Seuil de densité critique (l'horizon)
DENSITY_STEP = 0.002 

class Particle:
    def __init__(self, start_pos, start_vel):
        self.pos = start_pos
        self.vel = start_vel
        self.history = [start_pos]
        self.trapped = False
        
    def update(self, density, time):
        if self.trapped:
            # Chute lente vers 0 pour bien voir la convergence
            self.vel -= 0.02 * (1 - self.pos) 
            self.pos += self.vel
            self.pos = max(self.pos, SINGULARITY_POS)
            self.history.append(self.pos)
            return
        
        # Force de gravité plus douce avant le seuil
        gravity_force = density * 0.5 * (1 / (self.pos + 0.2)) 
        
        # Bruit stochastique (liberté) qui diminue lentement
        noise = np.random.normal(0, 0.08 * (1 - density))
        
        self.vel = self.vel - gravity_force + noise
        
        # Piégeage au seuil
        if density >= CRITICAL_DENSITY:
            self.trapped = True
            self.vel = -0.05 - (0.02 * (1 - self.pos))
        
        self.pos += self.vel
        
        if self.pos > 1.0:
            self.pos = 1.0
            self.vel *= -0.3
            
        self.history.append(self.pos)

# --- SIMULATION ---
densities = np.linspace(0.0, 1.0, MAX_TIME)
particles = [Particle(np.random.uniform(0.3, 1.0), np.random.uniform(-0.1, 0.1)) for _ in range(NUM_PARTICLES)]

entropy_history = []

for t, density in enumerate(densities):
    for p in particles:
        p.update(density, t)
    
    positions = [p.pos for p in particles]
    current_entropy = np.var(positions)
    entropy_history.append(current_entropy)

# --- VISUALISATION ---
plt.figure(figsize=(14, 10))

# Graphique 1 : Trajectoires
plt.subplot(2, 1, 1)
for p in particles:
    time_axis = range(len(p.history))
    color = 'red' if p.trapped else 'blue'
    if p.trapped:
        # Trouver l'index où la densité dépasse le seuil
        trap_idx = next(i for i, d in enumerate(densities) if d >= CRITICAL_DENSITY)
        # Partie libre (Bleu)
        plt.plot(range(trap_idx), p.history[:trap_idx], color='blue', alpha=0.4, linewidth=1)
        # Partie piégée (Rouge)
        plt.plot(range(trap_idx, len(p.history)), p.history[trap_idx:], color='red', alpha=0.6, linewidth=1.5)
    else:
        plt.plot(time_axis, p.history, color='blue', alpha=0.4, linewidth=1)

plt.axhline(y=SINGULARITY_POS, color='black', linestyle='-', linewidth=2, label='Singularité (État Unique)')
critical_time = int(np.argmax(densities >= CRITICAL_DENSITY))
plt.axvline(x=critical_time, color='red', linestyle='--', linewidth=2, label='Seuil Critique (Horizon)')

plt.title("Phase Libre (Bleu) vs Effondrement (Rouge) : La Transition Brutale", fontsize=14, fontweight='bold')
plt.xlabel("Temps (Densité croissante)")
plt.ylabel("Position (État du système)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(-0.1, 1.1)

# Graphique 2 : Entropie
plt.subplot(2, 1, 2)
plt.plot(densities, entropy_history, color='purple', linewidth=2, label='Entropie (Liberté)')
plt.axvline(x=CRITICAL_DENSITY, color='red', linestyle='--', linewidth=2, label='Seuil Critique')
plt.fill_between(densities, 0, entropy_history, where=(densities < CRITICAL_DENSITY), color='blue', alpha=0.1, label='Zone de Liberté')
plt.fill_between(densities, 0, entropy_history, where=(densities >= CRITICAL_DENSITY), color='red', alpha=0.1, label='Zone de Singularité')

plt.title("L'Entropie (Liberté) s'effondre au Seuil Critique", fontsize=14, fontweight='bold')
plt.xlabel("Densité de Causalité")
plt.ylabel("Entropie (Variance des états)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(-0.05, max(entropy_history)*1.1)

plt.tight_layout()
plt.show()

# --- ANALYSE ---
print("\n--- ANALYSE THÉORIQUE ---")
print(f"Seuil critique atteint à la densité : {CRITICAL_DENSITY}")
print(f"Entropie max avant effondrement : {max(entropy_history):.4f}")
print(f"Entropie finale : {entropy_history[-1]:.4f}")
print("\nConclusion :")
print("La simulation démontre que la liberté (entropie) est stable tant que la densité de causalité reste faible.")
print("Dès que le seuil critique est franchi, la variance s'effondre instantanément : le système perd toute capacité de choix.")
print("Ceci modélise mathématiquement la transition d'un état fluide (résilience) à un état de singularité (trauma figé / trou noir).")
