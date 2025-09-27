import os
import json

racine = "."  # Racine du dépôt Git

# --- Clés à modifier spécifiquement (「。」 -> ".") ---
KEY1_OLD = "』の\n　お手本が　どうしても見たいんです！\n<br>\n「しぐさをするのは　先生自身でもいいし\n　先生のお仲間の方が　私の目の前で　するのでも\n　かまいません。ご指導　よろしくお願いします！"
KEY1_NEW = "』の\n　お手本が　どうしても見たいんです！\n<br>\n「しぐさをするのは　先生自身でもいいし\n　先生のお仲間の方が　私の目の前で　するのでも\n　かまいません.ご指導　よろしくお願いします！"

KEY2_OLD = "』の\nお手本を見せてほしい！　と頼まれた。\nしぐさを行うのは　仲間でもいいようだ。"
KEY2_NEW = "』の\nお手本を見せてほしい！　と頼まれた.\nしぐさを行うのは　仲間でもいいようだ."

# --- Corrections générales (comme ton script initial) ---
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
                 .replace("‐", "-").replace("-", "-").replace("–", "-").replace("—", "-").replace("−", "-")
        )
    return texte

def corriger_valeurs(obj, modifie_flag):
    """Applique corriger_texte sur les VALEURS uniquement (pas les clés)."""
    if isinstance(obj, dict):
        return {k: corriger_valeurs(v, modifie_flag) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [corriger_valeurs(i, modifie_flag) for i in obj]
    elif isinstance(obj, str):
        txt = corriger_texte(obj)
        if txt != obj:
            modifie_flag[0] = True
        return txt
    else:
        return obj

def transformer_cles(obj, modifie_flag):
    """Ne modifie PAS les clés en général, sauf les deux clés ciblées ci-dessus."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_k = k
            if isinstance(k, str):
                if k == KEY1_OLD:
                    new_k = KEY1_NEW
                elif k == KEY2_OLD:
                    new_k = KEY2_NEW
                if new_k != k:
                    modifie_flag[0] = True
            # d'abord transformer récursivement les sous-objets (pour traiter les valeurs)
            new_v = transformer_cles(v, modifie_flag)
            # gestion collision éventuelle
            if new_k in new_dict and new_k != k:
                raise ValueError(f"Collision de clé après transformation : {new_k}")
            new_dict[new_k] = new_v
        return new_dict
    elif isinstance(obj, list):
        return [transformer_cles(i, modifie_flag) for i in obj]
    else:
        return obj

# --- Parcours des fichiers JSON ---
for racine_dossier, _, fichiers in os.walk(racine):
    for nom_fichier in fichiers:
        if nom_fichier == "name_overrides.json":
            continue  # ignore ce fichier
        if not nom_fichier.endswith(".json"):
            continue
        chemin_fichier = os.path.join(racine_dossier, nom_fichier)
        try:
            with open(chemin_fichier, "r", encoding="utf-8") as f:
                contenu = json.load(f)

            modifie = [False]

            # 1) Corriger les VALEURS (comme le script initial, mais sans toucher aux clés)
            contenu_corrige_val = corriger_valeurs(contenu, modifie)

            # 2) Appliquer la transformation ciblée sur les DEUX CLÉS seulement
            contenu_final = transformer_cles(contenu_corrige_val, modifie)

            if modifie[0]:
                with open(chemin_fichier, "w", encoding="utf-8") as f:
                    json.dump(contenu_final, f, ensure_ascii=False, indent=2)
                print(f"Corrigé : {chemin_fichier}")
            else:
                print(f"Aucune modification : {chemin_fichier}")

        except Exception as e:
            print(f"Erreur avec {chemin_fichier} : {e}")
