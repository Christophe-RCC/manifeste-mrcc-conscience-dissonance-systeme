# La Transition de Phase Critique dans les Systèmes Complexes Couplés.
# Le but du modèle n'est pas de prédire l'avenir, mais de donner une raison de changer.
# Si l'effondrement était juste "de la malchance" ou "une conspiration", on ne pourrait rien y faire.
# Mais si l'effondrement est une loi physique, alors on peut l'anticiper et adapter le système.

import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURATION --- 
TAILLE_GRILLE = 60
DUREE_SIM = 1000

# --- PARAMÈTRES DE BASE ---
DENSITE_INITIALE = 0.40
ENERGIE_INITIALE = 0.95

# --- PARAMÈTRES DU CHOC ---
AMPLITUDE_CHOC_MAX = 1.60
DUREE_CHOC = 600
VITESSE_CHOC = 20.5
step_choc = 300

# --- PARAMÈTRES DE RÉGLAGE ---
CONSOMMATION_STRESS = 0.05  

# 2. Coûts de base (Maintenance)
COUT_MAINTENANCE_BASE = 0.001 
GAIN_NUTRITION = 0.008  

# 3. Reproduction
SEUIL_NAISSANCE_MIN = 3
SEUIL_NAISSANCE_MAX = 6
PROBA_NAISSANCE = 0.15 
ENERGIE_NAISSANCE = 0.6

# 4. Seuil de Mortalité
SEUIL_MORTALITE_BASE = 0.15
FACTEUR_DEGRADATION = 0.5

# 5. Dette de Stress
TAUX_FATIGUE = 0.001
TAUX_REGENERATION = 0.002

def lancer_simulation_mrcc_corrige(seed_val):
    np.random.seed(seed_val)
    grille_vie = np.random.rand(TAILLE_GRILLE, TAILLE_GRILLE) > (1 - DENSITE_INITIALE)
    grille_energie = np.full((TAILLE_GRILLE, TAILLE_GRILLE), ENERGIE_INITIALE)
    
    hist_chaos_externe = []
    hist_chaos_local = []
    hist_vie = []
    hist_dette = []
    
    dette_stress = 0.0 
    
    for i in range(DUREE_SIM):
        alive_count = np.sum(grille_vie)
        total_energie = np.sum(grille_energie * grille_vie)
        avg_energie = total_energie / (alive_count + 1e-9)

        # 1. CHAOS EXTERNE
        if i < step_choc:
            chaos_externe = 0.0
        elif i < step_choc + DUREE_CHOC:
            prog = (i - step_choc) / DUREE_CHOC
            chaos_externe = AMPLITUDE_CHOC_MAX * (1 - np.exp(-prog * VITESSE_CHOC))
        elif i < step_choc + 2 * DUREE_CHOC:
            prog_desc = (i - (step_choc + DUREE_CHOC)) / DUREE_CHOC
            chaos_externe = AMPLITUDE_CHOC_MAX * np.exp(-prog_desc * VITESSE_CHOC)
        else:
            chaos_externe = 0.0
            
        # 2. DETTE DE STRESS & SEUIL DYNAMIQUE
        if chaos_externe > 0:
            dette_stress += TAUX_FATIGUE
        else:
            dette_stress = max(0, dette_stress - TAUX_REGENERATION)
            
        seuil_rupture_effectif = 1.0 - min(dette_stress, 0.9) 

        # 3. DÉFENSE ET CHAOS LOCAL
        # Capacité de défense : Densité * Énergie * Coefficient * Seuil
        capacite_dissipation = (alive_count * avg_energie * 0.0002) * seuil_rupture_effectif
        
        # Calcul du chaos local
        chaos_local = max(0.0, chaos_externe - capacite_dissipation)
        
        if chaos_local > 0.4:
            chaos_local += 0.05 * (chaos_local - 0.4)

        hist_chaos_externe.append(chaos_externe)
        hist_chaos_local.append(chaos_local)
        hist_dette.append(dette_stress)
        
        # 4. CALCUL DES VOISINS
        voisins_vivants = np.zeros_like(grille_vie, dtype=int)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                voisins_vivants += np.roll(np.roll(grille_vie, dx, axis=0), dy, axis=1)

        nouvelle_grille_vie = grille_vie.copy()
        nouvelle_grille_energie = grille_energie.copy()

        for x in range(TAILLE_GRILLE):
            for y in range(TAILLE_GRILLE):
                if not grille_vie[x, y]: 
                    continue
                
                nb_voisins = voisins_vivants[x, y]
                energie = grille_energie[x, y]
                
                risque = 0.0
                
                # A. Mortalité de base
                risque += 0.0005
                
                # B. Mortalité par Chaos (Seuil)
                if chaos_local > SEUIL_MORTALITE_BASE:
                    depassement = chaos_local - SEUIL_MORTALITE_BASE
                    risque += depassement * FACTEUR_DEGRADATION
                
                # C. Coût du Stress (Énergie)
                # COUT_TOTAL = BASE + (CHAOS * COEFF_STRESS)
                cout_stress = chaos_local * CONSOMMATION_STRESS
                cout_total = COUT_MAINTENANCE_BASE + cout_stress
                
                # Application de la mortalité
                if np.random.rand() < risque:
                    nouvelle_grille_vie[x, y] = False
                    nouvelle_grille_energie[x, y] = 0
                else:
                    # Économie d'énergie
                    nouvelle_grille_energie[x, y] = max(0, energie - cout_total + GAIN_NUTRITION)
                    
                    if nouvelle_grille_energie[x, y] <= 0:
                        nouvelle_grille_vie[x, y] = False
        
        # 5. REPRODUCTION (Conditionnelle)
        for x in range(TAILLE_GRILLE):
            for y in range(TAILLE_GRILLE):
                if not grille_vie[x, y]: 
                    if SEUIL_NAISSANCE_MIN <= voisins_vivants[x, y] <= SEUIL_NAISSANCE_MAX:
                        if np.random.rand() < PROBA_NAISSANCE:
                            if avg_energie > 0.2: # Seuil bas pour permettre la reproduction même en crise
                                nouvelle_grille_vie[x, y] = True
                                nouvelle_grille_energie[x, y] = ENERGIE_NAISSANCE

        grille_vie = nouvelle_grille_vie
        grille_energie = nouvelle_grille_energie
        
        densite = np.sum(grille_vie) / (TAILLE_GRILLE * TAILLE_GRILLE)
        hist_vie.append(densite)

    return hist_vie, hist_chaos_externe, hist_chaos_local, hist_dette

# --- LANCEMENT ---
plt.figure(figsize=(14, 10))

vie, chaos_externe, chaos_local, dette = lancer_simulation_mrcc_corrige(seed_val=42)

# Graphique 1 : Survie
plt.subplot(3, 1, 1)
plt.plot(vie, label="Densité de Vie", color='green', linewidth=2)
plt.axvline(300, color='black', linestyle='--', alpha=0.3, label="Début choc")
plt.axvline(300 + 10, color='orange', linestyle='--', alpha=0.3, label="Fin choc")
plt.title("Survie : Équilibre Rééquilibré", fontsize=14)
plt.xlabel("Temps")
plt.ylabel("Densité")
plt.legend()
plt.grid(True, alpha=0.3)

# Graphique 2 : Chaos
plt.subplot(3, 1, 2)
plt.plot(chaos_externe, label="Chaos Externe (A)", color='red', linestyle='--', linewidth=2)
plt.plot(chaos_local, label="Chaos Local", color='orange', linewidth=2, alpha=0.8)
plt.title("Chaos : A vs Local", fontsize=12)
plt.xlabel("Temps")
plt.ylabel("Niveau")
plt.legend()
plt.grid(True, alpha=0.3)

# Graphique 3 : Dette
plt.subplot(3, 1, 3)
plt.plot(dette, label="Dette de Stress", color='purple', linewidth=2)
plt.title("Dette de Stress (Fatigue)", fontsize=12)
plt.xlabel("Temps")
plt.ylabel("Dette")
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

print("\n--- RÉSULTATS : ÉCONOMIE RÉÉQUILIBRÉE ---")
print(f"Chaos Externe Max : {max(chaos_externe):.2f}")
print(f"Chaos Local Max : {max(chaos_local):.4f}")
print(f"Densité de Vie Finale : {vie[-1]:.4f}")
print(f"Dette de Stress Finale : {dette[-1]:.4f}")

if vie[-1] > 0.1:
    print("SUCCÈS : Le système a absorbé le choc et survécu.")
else:
    print("⚠️  Échec : Le système s'est effondré")
