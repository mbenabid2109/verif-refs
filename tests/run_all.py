"""Lance toute la batterie de non-régression, sans accès au réseau.

Usage : python tests/run_all.py
Chaque test simule les notices de Crossref, OpenAlex, DataCite et Open Library ;
aucun appel n'est fait aux sources réelles ni au modèle de langage.
"""
import importlib.util
import os
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIERS = ["test_d.py", "test_v5.py", "test_v51.py", "test_v52.py", "test_cli.py", "test_i18n.py", "test_app.py", "test_chaine.py"]


def main():
    total_ok = total_xx = 0
    vus = set()          # chaque fichier rejoue les 25 cas de test_v4 : on ne compte qu'une fois
    for f in FICHIERS:
        if f == "test_chaine.py" and importlib.util.find_spec("google.adk") is None:
            print(f"{f:<16} ignoré (Google ADK non installé)")
            continue
        if f == "test_app.py" and importlib.util.find_spec("gradio") is None:
            print(f"{f:<16} ignoré (Gradio non installé)")
            continue
        p = subprocess.run([sys.executable, os.path.join(ICI, f)], capture_output=True,
                           text=True, encoding="utf-8", timeout=300)
        lignes = p.stdout.splitlines()
        nouveaux = [l for l in lignes if l.startswith("OK") and l not in vus]
        vus.update(nouveaux)
        ok = len(nouveaux)
        xx = [l for l in lignes if l.startswith("XX")]
        if f == "test_chaine.py":
            ok += any("appels à lot_suivant : 5" in l for l in lignes)
            if not any("appels à lot_suivant : 5" in l for l in lignes):
                xx.append("XX  la boucle n'a pas fait 4 lots et un appel final")
        if p.returncode != 0:
            xx.append(f"XX  erreur d'exécution : {p.stderr.strip().splitlines()[-1] if p.stderr.strip() else p.returncode}")
        total_ok += ok
        total_xx += len(xx)
        print(f"{f:<16} {ok:>3} cas nouveaux conformes, {len(xx)} écart(s)")
        for l in xx:
            print("   ", l[:160])
    print(f"\nTotal : {total_ok} cas distincts conformes, {total_xx} écart(s)")
    sys.exit(1 if total_xx else 0)


if __name__ == "__main__":
    main()
