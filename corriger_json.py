import os
import json

racine = "."  # Racine du dépôt Git

def corriger_texte(texte):
    if isinstance(texte, str):
        return (
            texte.replace("…", "...")
                 .replace("。", ".")
                 .replace("’", "'")
                 .replace(" !", "!")
                 .replace(" ?", "?")
                 .replace("~", "～")
                 .replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e")
                 .replace("î", "i").replace("ï", "i")
                 .replace("ô", "o").replace("ö", "o")
                 .replace("ù", "u").replace("û", "u")
                 .replace("à", "a").replace("â", "a").replace("ä", "a")
                 .replace("É", "E").replace("È", "E").replace("Ê", "E").replace("Ë", "E")
                 .replace("Î", "I").replace("Ï", "I")
                 .replace("Ô", "O").replace("Ö", "O")
                 .replace("Ù", "U").replace("Û", "U").replace("Ü", "U")
                 .replace("À", "A").replace("Â", "A").replace("Ä", "A")
                 .replace("ç", "c").replace("Ç", "C")
                 .replace("æ", "ae").replace("Æ", "AE")
                 .replace("œ", "oe").replace("Œ", "OE")
                 .replace('“', '"').replace('”', '"').replace("«", '"').replace("»", '"')
                 .replace("‐", "-").replace("‑", "-").replace("–", "-").replace("—", "-").replace("−", "-")
        )
    return texte

def corriger_contenu(obj, modifie_flag):
    if isinstance(obj, dict):
        return {k: corriger_contenu(v, modifie_flag) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [corriger_contenu(i, modifie_flag) for i in obj]
    elif isinstance(obj, str):
        texte_corrige = corriger_texte(obj)
        if texte_corrige != obj:
            modifie_flag[0] = True
        return texte_corrige
    else:
        return obj

# Balaye tous les fichiers .json récursivement
for racine_dossier, _, fichiers in os.walk(racine):
    for nom_fichier in fichiers:
        if nom_fichier == "name_overrides.json":
            continue  # Ignore ce fichier
        if nom_fichier.endswith(".json"):
            chemin_fichier = os.path.join(racine_dossier, nom_fichier)
            try:
                with open(chemin_fichier, "r", encoding="utf-8") as f:
                    contenu = json.load(f)

                modifie = [False]
                contenu_corrige = corriger_contenu(contenu, modifie)

                if modifie[0]:
                    with open(chemin_fichier, "w", encoding="utf-8") as f:
                        json.dump(contenu_corrige, f, ensure_ascii=False, indent=2)
                    print(f"Corrigé : {chemin_fichier}")
                else:
                    print(f"Aucune modification : {chemin_fichier}")

            except Exception as e:
                print(f"Erreur avec {chemin_fichier} : {e}")
