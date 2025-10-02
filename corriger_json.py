#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import argparse
import shutil

# ------------- Helpers EOL (CRLF/LF) -------------
def _to_lf(s):
    """Normalise \\r\\n -> \\n (pour comparaisons fiables)."""
    return s.replace("\r\n", "\n") if isinstance(s, str) else s

def _restore_eol(s, template):
    """Si la clé originale était en CRLF, ré-applique CRLF à la nouvelle clé."""
    if isinstance(template, str) and "\r\n" in template:
        return s.replace("\n", "\r\n")
    return s

# ------------- Dé-hiérarchisation (aplatissement) des clés -------------
def deflatten(obj, sep="."):
    """
    Transforme {"P":{"":{"":{" Professeur!":"Bobibegk"}}}}
    en {"P... Professeur!":"Bobibegk"}.

    - Joint tous les segments de chemin (même vides) avec `sep`.
    - Détecte les collisions (deux chemins qui produisent la même clé).
    - Traite récursivement les dicts. Laisse les listes et autres types intacts
      (sauf si elles contiennent des dicts imbriqués, qui seront aplatis avec une clé jointe).
    """
    def _walk(node, parts, out):
        if isinstance(node, dict):
            for k, v in node.items():
                k_str = k if isinstance(k, str) else str(k)
                _walk(v, parts + [k_str], out)
        elif isinstance(node, list):
            # Si une liste contient des dicts, on les aplatit et les pose sous la clé actuelle
            # En revanche, si la liste est "pure" (pas de dict), on l'assigne telle quelle.
            if any(isinstance(i, dict) for i in node):
                # on place chaque dict enfant sous la même clé jointe (peut créer collision)
                for idx, item in enumerate(node):
                    if isinstance(item, dict):
                        _walk(item, parts + [str(idx)], out)
                    else:
                        # on capture les éléments non-dict dans une clé dédiée (indexée)
                        key = sep.join(parts + [str(idx)])
                        if key in out:
                            raise ValueError(f"Collision de clé après dé-hiérarchisation : {key}")
                        out[key] = item
            else:
                key = sep.join(parts)
                if key in out:
                    raise ValueError(f"Collision de clé après dé-hiérarchisation : {key}")
                out[key] = node
        else:
            key = sep.join(parts)
            if key in out:
                raise ValueError(f"Collision de clé après dé-hiérarchisation : {key}")
            out[key] = node

    if isinstance(obj, dict):
        result = {}
        _walk(obj, [], result)
        return result
    # Si le root est une liste, on la laisse telle quelle (cas rare pour i18n)
    return obj

# ------------- Chargement des règles -------------
def load_rules(path):
    """
    key_rules.json = [
      {"match":"exact|contains|startswith|endswith|regex", "old":"...", "new":"..."},
      ...
    ]
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rules = []
    for i, r in enumerate(data):
        m = r.get("match", "exact")
        old = r["old"]
        new = r["new"]
        if m not in {"exact", "contains", "startswith", "endswith", "regex"}:
            raise ValueError(f"Règle #{i+1}: type 'match' inconnu: {m}")
        rgx = re.compile(old) if m == "regex" else None
        rules.append({"match": m, "old": old, "new": new, "regex": rgx})
    return rules

# ------------- Corrections des valeurs -------------
def corriger_texte(texte, keep_accents=False):
    if not isinstance(texte, str):
        return texte
    t = (texte.replace("…", "...")
              .replace("。", ".")
              .replace("’", "'")
              .replace(" !", "!")
              .replace(" ?", "?")
              .replace("~", "～")
              .replace("‐", "-").replace("–", "-").replace("—", "-").replace("−", "-"))
    if not keep_accents:
        t = (t.replace("é","e").replace("è","e").replace("ê","e").replace("ë","e")
               .replace("î","i").replace("ï","i")
               .replace("ô","o").replace("ö","o")
               .replace("ù","u").replace("û","u")
               .replace("à","a").replace("â","a").replace("ä","a")
               .replace("É","E").replace("È","E").replace("Ê","E").replace("Ë","E")
               .replace("Î","I").replace("Ï","I")
               .replace("Ô","O").replace("Ö","O")
               .replace("Ù","U").replace("Û","U").replace("Ü","U")
               .replace("À","A").replace("Â","A").replace("Ä","A")
               .replace("ç","c").replace("Ç","C")
               .replace("æ","ae").replace("Æ","AE")
               .replace("œ","oe").replace("Œ","OE"))
    t = (t.replace('“','"').replace('”','"').replace("«",'"').replace("»",'"'))
    return t

def corriger_valeurs(obj, stats, keep_accents=False):
    if isinstance(obj, dict):
        return {k: corriger_valeurs(v, stats, keep_accents) for k, v in obj.items()}
    if isinstance(obj, list):
        return [corriger_valeurs(i, stats, keep_accents) for i in obj]
    if isinstance(obj, str):
        new = corriger_texte(obj, keep_accents)
        if new != obj:
            stats["values_changed"] += 1
        return new
    return obj

# ------------- Remplacements sur les CLÉS -------------
def apply_key_rules(obj, rules, stats):
    """
    Applique les règles sur les CLÉS uniquement (récursif).
    - exact : tolérant CRLF/LF (compare en LF, restaure EOL original).
    - contains/startswith/endswith/regex : comportement standard.
    Lève en cas de collision post-transformation.
    """
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_k = k

            if isinstance(k, str):
                for r in rules:
                    m = r["match"]
                    if m == "exact":
                        k_lf   = _to_lf(k)
                        old_lf = _to_lf(r["old"])
                        if k_lf == old_lf:
                            new_candidate = r["new"]  # construit en LF
                            new_k = _restore_eol(new_candidate, k)  # restaure CRLF si présent
                            stats["keys_changed"] += 1
                    elif m == "contains":
                        if r["old"] in new_k:
                            new_k = new_k.replace(r["old"], r["new"])
                            stats["keys_changed"] += 1
                    elif m == "startswith":
                        if new_k.startswith(r["old"]):
                            new_k = r["new"] + new_k[len(r["old"]):]
                            stats["keys_changed"] += 1
                    elif m == "endswith":
                        if new_k.endswith(r["old"]):
                            new_k = new_k[:len(new_k)-len(r["old"])] + r["new"]
                            stats["keys_changed"] += 1
                    elif m == "regex" and r["regex"]:
                        new2 = r["regex"].sub(r["new"], new_k)
                        if new2 != new_k:
                            new_k = new2
                            stats["keys_changed"] += 1

            new_v = apply_key_rules(v, rules, stats)

            if new_k in new_dict and new_k != k:
                raise ValueError(f"Collision de clé après transformation : {new_k}")
            new_dict[new_k] = new_v
        return new_dict

    if isinstance(obj, list):
        return [apply_key_rules(i, rules, stats) for i in obj]

    return obj

# ------------- Traitement d'un fichier -------------
def process_file(path, rules, args, global_stats):
    try:
        # utf-8-sig pour tolérer BOM
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Erreur lecture JSON: {path} : {e}")
        global_stats["errors"] += 1
        return

    # 1) Dé-hiérarchiser si demandé (avant toute autre opération)
    if args.deflatten:
        try:
            data = deflatten(data, sep=".")
        except Exception as e:
            print(f"  ! Dé-hiérarchisation échouée pour {path}: {e}")
            global_stats["errors"] += 1
            return

    stats = {"keys_changed": 0, "values_changed": 0}

    # 2) Corrections de valeurs (ponctuation, accents, etc.)
    data = corriger_valeurs(data, stats, keep_accents=args.keep_accents)

    # 3) Règles de renommage de clés
    data = apply_key_rules(data, rules, stats)

    # 4) Écriture si changements
    if stats["keys_changed"] or stats["values_changed"]:
        print(f"[CHANGES] {path}  (keys:{stats['keys_changed']} values:{stats['values_changed']})")
        global_stats["changed_files"] += 1
        if args.apply:
            if args.backup:
                try:
                    shutil.copy2(path, path + ".bak")
                except Exception as e:
                    print(f"  ! Backup échoué pour {path}: {e}")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"  ! Écriture échouée pour {path}: {e}")
                global_stats["errors"] += 1
    else:
        print(f"[OK] {path}")

    global_stats["files"] += 1
    global_stats["keys"] += stats["keys_changed"]
    global_stats["values"] += stats["values_changed"]

# ------------- Main -------------
def main():
    ap = argparse.ArgumentParser(description="Corriger valeurs et renommer des clés JSON (CRLF/LF safe).")
    ap.add_argument("--root", default=".", help="Racine à scanner (dossier).")
    ap.add_argument("--rules", default="key_rules.json", help="Fichier JSON des règles de clés.")
    ap.add_argument("--apply", action="store_true", help="Écrire les changements (sinon dry-run).")
    ap.add_argument("--backup", action="store_true", help="Créer un .bak avant d’écrire (avec --apply).")
    ap.add_argument("--keep-accents", action="store_true", help="Ne pas déaccentuer les valeurs.")
    ap.add_argument("--skip", nargs="*", default=["name_overrides.json"], help="Fichiers à ignorer.")
    ap.add_argument("--deflatten", action="store_true",
                    help="Aplatir les objets imbriqués pour reconstituer les clés jointes par '.' (ex: P... Professeur!).")
    args = ap.parse_args()

    try:
        rules = load_rules(args.rules)
    except Exception as e:
        print(f"Erreur chargement règles: {e}")
        return

    g = {"files": 0, "changed_files": 0, "keys": 0, "values": 0, "errors": 0}
    for root, _, files in os.walk(args.root):
        for name in files:
            if not name.endswith(".json"):
                continue
            if name in args.skip:
                continue
            process_file(os.path.join(root, name), rules, args, g)

    print("\n--- Bilan ---")
    print(f"Fichiers scannés : {g['files']}")
    print(f"Fichiers modifiés : {g['changed_files']}")
    print(f"Clés modifiées    : {g['keys']}")
    print(f"Valeurs modifiées : {g['values']}")
    print(f"Erreurs           : {g['errors']}")

if __name__ == "__main__":
    main()
