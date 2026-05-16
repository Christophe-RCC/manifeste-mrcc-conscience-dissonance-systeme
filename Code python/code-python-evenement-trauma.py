import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
SIMULATION_LENGTH = 1000
ENVIRONMENT_NOISE = 0.05
INERTIA = 0.95           # Environnement très stable avant le choc
LEARNING_RATE_MRCC = 0.15 # Vitesse d'adaptation (plus rapide pour réagir au choc)
TRAUMA_STEP = 500        # Moment du choc (au milieu de la simulation)
TRAUMA_MAGNITUDE = 0.4   # La taille du saut (de 0.5 vers 0.9)

class Agent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.internal_model = 0.5 # Point de départ
        self.dissonance_history = []
        self.model_history = []
        
    def update(self, reality):
        # Calcul de la dissonance
        current_dissonance = abs(reality - self.internal_model)
        self.dissonance_history.append(current_dissonance)
        self.model_history.append(self.internal_model)
        
        if self.strategy == 'mrcc':
            # ADAPTATION : L'agent change son modèle pour coller à la réalité
            # C'est le mécanisme de "compréhension" et d'apprentissage
            self.internal_model = self.internal_model + LEARNING_RATE_MRCC * (reality - self.internal_model)
            
        elif self.strategy == 'free_will':
            # RIGIDITÉ : L'agent refuse de changer son modèle
            # Il reste bloqué sur sa croyance initiale (0.5)
            pass 
            
        return current_dissonance

# --- SIMULATION ---
env_history = []
agent_mrcc = Agent('mrcc')
agent_fw = Agent('free_will')

current_env = 0.5
for t in range(SIMULATION_LENGTH):
    # 1. Création de l'environnement (Causalité + Bruit)
    change = np.random.normal(0, ENVIRONMENT_NOISE)
    current_env = current_env * INERTIA + change
    current_env = np.clip(current_env, 0, 1)
    
    # 2. LE CHOC (TRAUMA)
    if t == TRAUMA_STEP:
        # Saut brutal de la réalité
        current_env = np.clip(current_env + TRAUMA_MAGNITUDE, 0, 1)
        print(f"TRAUMA survenu à l'itération {t} : Environnement passe à {current_env:.2f}")
    
    env_history.append(current_env)
    
    # Mise à jour des agents
    d_mrcc = agent_mrcc.update(current_env)
    d_fw = agent_fw.update(current_env)

# --- VISUALISATION AVANCÉE ---
plt.figure(figsize=(14, 12))

# Graphique 1 : Environnement vs Modèles
plt.subplot(3, 1, 1)
plt.plot(env_history, label='Réalité (Environnement)', color='black', linewidth=2, alpha=0.8)
plt.plot(agent_mrcc.model_history, label='Modèle MRCC (Adaptatif)', color='green', linestyle='--', linewidth=1.5)
plt.plot(agent_fw.model_history, label='Modèle Libre Arbitre (Rigide)', color='red', linestyle=':', linewidth=1.5)

# Ligne verticale pour le trauma
plt.axvline(x=TRAUMA_STEP, color='red', linestyle='-', linewidth=2, alpha=0.6, label='Choc Traumatique')

plt.title("Impact d'un Choc Brutal sur les Modèles Internes", fontsize=14, fontweight='bold')
plt.xlabel("Temps (Itérations)")
plt.ylabel("État du Système (0 à 1)")
plt.legend()
plt.grid(True, alpha=0.3)

# Graphique 2 : Dissonance (Énergie Gaspillée) - Vue d'ensemble
plt.subplot(3, 1, 2)
plt.plot(agent_mrcc.dissonance_history, label='Dissonance MRCC', color='green', alpha=0.7)
plt.plot(agent_fw.dissonance_history, label='Dissonance Libre Arbitre', color='red', alpha=0.7)

plt.axvline(x=TRAUMA_STEP, color='red', linestyle='--', linewidth=1, alpha=0.5)
plt.title("Réaction à la Dissonance : Résilience vs Effondrement", fontsize=14, fontweight='bold')
plt.xlabel("Temps")
plt.ylabel("Niveau de Dissonance (Énergie)")
plt.legend()
plt.grid(True, alpha=0.3)

# Graphique 3 : Zoom sur la phase post-trauma (Résilience)
# On ne regarde que les 300 dernières itérations pour voir la stabilisation
zoom_start = TRAUMA_STEP
plt.subplot(3, 1, 3)
plt.plot(agent_mrcc.dissonance_history[zoom_start:], label='Dissonance MRCC (Post-Trauma)', color='green', linewidth=2)
plt.plot(agent_fw.dissonance_history[zoom_start:], label='Dissonance Libre Arbitre (Post-Trauma)', color='red', linewidth=2)

# Lissage pour voir la tendance
smooth_mrcc = np.convolve(agent_mrcc.dissonance_history[zoom_start:], np.ones(30)/30, mode='valid')
smooth_fw = np.convolve(agent_fw.dissonance_history[zoom_start:], np.ones(30)/30, mode='valid')
x_smooth = range(len(smooth_mrcc))

plt.plot(x_smooth, smooth_mrcc, label='Tendance MRCC', color='darkgreen', linewidth=3)
plt.plot(x_smooth, smooth_fw, label='Tendance Libre Arbitre', color='darkred', linewidth=3)

plt.title("Zoom Post-Trauma : Capacité de Réduction de la Dissonance", fontsize=14, fontweight='bold')
plt.xlabel("Temps après le choc")
plt.ylabel("Niveau de Dissonance")
plt.legend()
plt.grid(True, alpha=0.3)
plt.axhline(y=0.2, color='gray', linestyle=':', alpha=0.5, label='Seuil de tolérance')

plt.tight_layout()
plt.show()

# --- ANALYSE DES DONNÉES ---
print("\n--- ANALYSE DES RÉSULTATS ---")
print(f"Dissonance moyenne AVANT le choc (0-{TRAUMA_STEP}):")
print(f"  MRCC : {np.mean(agent_mrcc.dissonance_history[:TRAUMA_STEP]):.4f}")
print(f"  Libre Arbitre : {np.mean(agent_fw.dissonance_history[:TRAUMA_STEP]):.4f}")

print(f"\nDissonance moyenne APRÈS le choc ({TRAUMA_STEP}-{SIMULATION_LENGTH}):")
print(f"  MRCC : {np.mean(agent_mrcc.dissonance_history[TRAUMA_STEP:]):.4f}")
print(f"  Libre Arbitre : {np.mean(agent_fw.dissonance_history[TRAUMA_STEP:]):.4f}")

print(f"\nÉcart de performance post-trauma : {np.mean(agent_fw.dissonance_history[TRAUMA_STEP:]) - np.mean(agent_mrcc.dissonance_history[TRAUMA_STEP:]):.4f}")
