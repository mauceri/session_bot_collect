import logging
import os
import sys
import time
import re

logger = logging.getLogger()
if logger.hasHandlers():
    logger.handlers.clear()

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def _extract_metadata(message: str):
    """
        Extrait les expressions-clés (#...#), les catégories ($...$) et l'URL à la fin du message.
        Retourne un dictionnaire contenant les éléments extraits et le message nettoyé.
    """
    metadata = {"expressions_clefs": [], "categorie": None, "url": None}

    # Séparer la première ligne du reste du message
    first_line, _, remaining_text = message.partition("\n")

    # Extraction des expressions-clés **uniquement au début**
    match_expr = re.match(r"^((#.*?#)\s)*", first_line)
    if match_expr:
        expressions_brutes = match_expr.group(0)  # Les expressions trouvées
        metadata["expressions_clefs"] = re.findall(r"#(.*?)#", expressions_brutes)
        first_line = first_line[len(expressions_brutes):]  # Supprimer les expressions-clés de la première ligne

    # Extraction des catégories (étiquettes $...$)
    match_expr = re.match(r"^((\$.*?\$)\s)*", first_line)
    if match_expr:
        expressions_brutes = match_expr.group(0)  # Les expressions trouvées
        metadata["categorie"] = re.findall(r"\$(.*?)\$", expressions_brutes)
        first_line = first_line[len(expressions_brutes):]  # Supprimer les expressions-clés de la première ligne

    # Reconstruction du message propre
    cleaned_message = (first_line.strip() + "\n" + remaining_text.strip()).strip()

    # Extraction d'une URL si elle est à la fin du message
    url_match = re.search(r"(https?://[^\s]+)$", cleaned_message, re.MULTILINE)
    if url_match:
        metadata["url"] = url_match.group(1)
        cleaned_message = cleaned_message.replace(metadata["url"], "").strip()  # Retirer l'URL du texte

    return metadata, cleaned_message


if __name__ == '__main__':
    print(_extract_metadata(sys.argv[1]))