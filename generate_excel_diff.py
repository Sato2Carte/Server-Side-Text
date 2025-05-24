import json
import pandas as pd
from pathlib import Path

def create_diff_excel(source_file: Path, fr_file: Path, out_file: Path):
    if not source_file.exists() or not fr_file.exists():
        print(f"Fichier manquant : {source_file} ou {fr_file}")
        return

    with source_file.open(encoding="utf-8") as f:
        jp_data = json.load(f)
    with fr_file.open(encoding="utf-8") as f:
        fr_data = json.load(f)

    jp_texts, fr_texts = [], []

    for key in jp_data:
        if key in fr_data and jp_data[key] != fr_data[key]:
            jp_texts.append(jp_data[key])
            fr_texts.append(fr_data[key])

    if jp_texts:
        df = pd.DataFrame({"Texte Japonais": jp_texts, "Texte FR": fr_texts})
        df.to_excel(out_file, index=False)
        print(f"✅ Exporté : {out_file}")
    else:
        print(f"⚠️ Aucune différence trouvée pour : {fr_file.name}")


def main():
    root = Path(__file__).parent
    fr_dir = root / "fr"
    out_dir = root / "excels"
    out_dir.mkdir(exist_ok=True)

    for fr_file in fr_dir.glob("*.json"):
        source_file = root / fr_file.name
        out_file = out_dir / fr_file.with_suffix(".xlsx").name
        create_diff_excel(source_file, fr_file, out_file)


if __name__ == "__main__":
    main()
