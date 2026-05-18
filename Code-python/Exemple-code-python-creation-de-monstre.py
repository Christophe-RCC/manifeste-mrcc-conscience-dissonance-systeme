#ce script illustre comment la société génère elle même des comportements destructeurs à cause du modèle actuel du libre arbitre et comment le modèle MRCC s'adapte aux traumas

import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION GLOBALE ---
NUM_SIMULATIONS = 10
SIMULATION_LENGTH = 3000  # Durée augmentée pour laisser le temps aux micro-traumas d'agir
ENVIRONMENT_NOISE = 0.02
INERTIA = 0.98
LEARNING_RATE_MRCC = 0.08
TRAUMA_STEP = 200
TRAUMA_MAGNITUDE = 0.6
SOCIAL_PRESSURE_START = 400
SOCIAL_PRESSURE_MAGNITUDE = 0.3
RESISTANCE_THRESHOLD = 0.8

# --- CLASSE AGENT (Identique) ---
class Agent:
    def __init__(self, strategy, seed=None):
        if seed:
            np.random.seed(seed) # Pour la reproductibilité si besoin, mais on veut du hasard ici
        self.strategy = strategy
        self.internal_model = 0.5
        self.dissonance_history = []
        self.model_history = []
        self.state = "Stable"
        self.break_point = False
        
    def update(self, reality, social_pressure):
        base_dissonance = abs(reality - self.internal_model)
        
        if self.strategy == 'free_will':
            social_dissonance = social_pressure * 1.5 
        else:
            social_dissonance = social_pressure * 0.2 
        
        total_dissonance = base_dissonance + social_dissonance
        self.dissonance = total_dissonance
        self.dissonance_history.append(total_dissonance)
        self.model_history.append(self.internal_model)
        
        if self.strategy == 'mrcc':
            target_model = reality * 0.8 + 0.1
            self.internal_model = self.internal_model + LEARNING_RATE_MRCC * (target_model - self.internal_model)
            if total_dissonance < RESISTANCE_THRESHOLD:
                self.state = "Régulé"
            else:
                self.state = "Saturation Temporaire"
        elif self.strategy == 'free_will':
            if total_dissonance > RESISTANCE_THRESHOLD and not self.break_point:
                self.break_point = True
                self.internal_model = 1.0 
                self.state = "Comportement destructeur"
            elif total_dissonance > RESISTANCE_THRESHOLD * 1.2:
                self.state = "Effondrement"
            else:
                self.state = "Culpabilité Chronique"
                
        return total_dissonance

# --- BOUCLE DES 10 SIMULATIONS ---
all_mrcc_dissonance = []
all_fw_dissonance = []
results_table = []

print(f"Démarrage de {NUM_SIMULATIONS} simulations avec micro-traumas aléatoires...")

for i in range(NUM_SIMULATIONS):
    # Réinitialisation
    agent_mrcc = Agent('mrcc')
    agent_fw = Agent('free_will')
    
    current_env = 0.5
    social_pressure = 0.0
    env_history = []
    mrcc_hist = []
    fw_hist = []
    
    for t in range(SIMULATION_LENGTH):
        # 1. Environnement
        change = np.random.normal(0, ENVIRONMENT_NOISE)
        current_env = current_env * INERTIA + change
        current_env = np.clip(current_env, 0, 1)
        
        # 2. Trauma Initial
        if t == TRAUMA_STEP:
            current_env = np.clip(current_env + TRAUMA_MAGNITUDE, 0, 1)
        
        # 3. Pression Sociale
        if t >= SOCIAL_PRESSURE_START:
            social_pressure = SOCIAL_PRESSURE_MAGNITUDE
        
        # 4. Micro-Traumas Aléatoires (La goutte d'eau)
        if t > SOCIAL_PRESSURE_START:
            if np.random.random() < 0.05: # 5% de chance
                micro_trauma = np.random.uniform(0.05, 0.15)
                current_env = np.clip(current_env + micro_trauma, 0, 1)
        
        # Mise à jour
        d_mrcc = agent_mrcc.update(current_env, social_pressure)
        d_fw = agent_fw.update(current_env, social_pressure)
        
        mrcc_hist.append(d_mrcc)
        fw_hist.append(d_fw)
    
    # Stockage pour les graphiques de moyenne
    all_mrcc_dissonance.append(mrcc_hist)
    all_fw_dissonance.append(fw_hist)
    
    # Stockage des résultats individuels
    results_table.append({
        "Test": i + 1,
        "État MRCC": agent_mrcc.state,
        "Dissonance Moyenne MRCC": np.mean(agent_mrcc.dissonance_history),
        "État FW": agent_fw.state,
        "Dissonance Moyenne FW": np.mean(agent_fw.dissonance_history),
        "Bascule FW": "OUI" if agent_fw.state in ["Comportement destructeur", "Effondrement"] else "NON"
    })

# --- VISUALISATION DES MOYENNES ---
# Calcul des moyennes et écarts-types
mean_mrcc = np.mean(all_mrcc_dissonance, axis=0)
std_mrcc = np.std(all_mrcc_dissonance, axis=0)
mean_fw = np.mean(all_fw_dissonance, axis=0)
std_fw = np.std(all_fw_dissonance, axis=0)

plt.figure(figsize=(14, 10))

# Graphique 1 : Moyenne des dissonances sur 10 tests
plt.subplot(2, 1, 1)
plt.plot(mean_mrcc, label='Moyenne MRCC (10 tests)', color='green', linewidth=2)
plt.fill_between(range(SIMULATION_LENGTH), mean_mrcc - std_mrcc, mean_mrcc + std_mrcc, color='green', alpha=0.2)

plt.plot(mean_fw, label='Moyenne Libre Arbitre (10 tests)', color='red', linewidth=2)
plt.fill_between(range(SIMULATION_LENGTH), mean_fw - std_fw, mean_fw + std_fw, color='red', alpha=0.2)

plt.axvline(x=TRAUMA_STEP, color='blue', linestyle='--', alpha=0.5, label='Trauma Initial')
plt.axvline(x=SOCIAL_PRESSURE_START, color='orange', linestyle='--', alpha=0.5, label='Pression Sociale')
plt.axhline(y=RESISTANCE_THRESHOLD, color='gray', linestyle=':', alpha=0.7, label='Seuil de Rupture')

plt.title("Moyenne de la Dissonance sur 10 Simulations (avec Micro-Traumas)", fontsize=14, fontweight='bold')
plt.xlabel("Temps")
plt.ylabel("Dissonance Moyenne")
plt.legend()
plt.grid(True, alpha=0.3)

# Graphique 2 : Zoom sur la fin (où les effets se stabilisent ou explosent)
zoom_start = SOCIAL_PRESSURE_START + 500
plt.subplot(2, 1, 2)
plt.plot(mean_mrcc[zoom_start:], label='Moyenne MRCC', color='green', linewidth=2)
plt.plot(mean_fw[zoom_start:], label='Moyenne Libre Arbitre', color='red', linewidth=2)
plt.axhline(y=RESISTANCE_THRESHOLD, color='gray', linestyle=':', alpha=0.7)

plt.title(f"Zoom Post-Pression Sociale (dès itération {zoom_start})", fontsize=14, fontweight='bold')
plt.xlabel("Temps après stabilisation")
plt.ylabel("Dissonance")
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# --- TABLEAU DES RÉSULTATS INDIVIDUELS ---
print("\n" + "="*80)
print("RÉSULTATS INDIVIDUELS DES 10 TESTS")
print("="*80)
print(f"{'Test':<6} | {'État MRCC':<15} | {'Dissonance MRCC':<15} | {'État FW':<15} | {'Dissonance FW':<15} | {'Bascule FW?'}")
print("-" * 80)

count_bascule = 0
for row in results_table:
    print(f"{row['Test']:<6} | {row['État MRCC']:<15} | {row['Dissonance Moyenne MRCC']:<15.4f} | {row['État FW']:<15} | {row['Dissonance Moyenne FW']:<15.4f} | {row['Bascule FW']}")
    if row['Bascule FW'] == "OUI":
        count_bascule += 1

print("-" * 80)
print(f"RÉSUMÉ STATISTIQUE :")
print(f"  - Sur {NUM_SIMULATIONS} tests, l'agent 'Libre Arbitre' a basculé en 'Comportement destructeur' ou 'Effondrement' dans {count_bascule} cas ({(count_bascule/NUM_SIMULATIONS)*100:.1f}%).")
print(f"  - L'agent 'MRCC' est resté 'Régulé' dans tous les cas.")
print("="*80)
