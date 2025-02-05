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
    metadata = {"expressions_clefs": [], "url": None}

    # Séparer la première ligne du reste du message
    first_line = message

    print(f"+++++++++++++++++++++ {first_line}")
    # Extraction des expressions-clés **uniquement au début**
    match = re.match(r"^((#.*?#)\s)*", first_line)
    if match:
        expressions_brutes = match.group(0)  # Les expressions trouvées
        metadata["expressions_clefs"] = re.findall(r"#(.*?)#", expressions_brutes)
        print(f'{metadata["expressions_clefs"]}')
        first_line = first_line[len(expressions_brutes):]  # Supprimer les expressions de la première ligne
        return metadata["expressions_clefs"]

if __name__ == '__main__':
    print(_extract_metadata(sys.argv[1]))