import logging
import os
import sys
import time
import yaml
import re
from .interfaces import IObserver, IObservable, IPlugin

logger = logging.getLogger()
if logger.hasHandlers():
    logger.handlers.clear()

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class Collect(IObserver):
    def __init__(self, observable: IObservable = None):
        self.__observable = observable

        # Déterminer le répertoire du plugin
        plugin_dir = os.path.dirname(os.path.abspath(__file__))

        # Chemin du répertoire 'data'
        self.data_dir = os.path.join(plugin_dir, 'data')

        # Créer le répertoire de données s'il n'existe pas
        os.makedirs(self.data_dir, exist_ok=True)

        logger.info(f"********************** Répertoire de données du plugin : {self.data_dir}")

    def _get_user_file(self, utilisateur: str) -> str:
        """Retourne le chemin du fichier utilisateur dans data/"""
        return os.path.join(self.data_dir, f"{utilisateur}.yaml")

    def _extract_metadata(self, message: str):
        """
        Extrait les expressions-clés (début de la première ligne) et l'URL à la fin du message.
        Retourne un dictionnaire contenant les éléments extraits et le message nettoyé.
        """
        metadata = {"expressions_clefs": [], "url": None}

        # Séparer la première ligne du reste du message
        first_line, _, remaining_text = message.partition("\n")

        # Extraction des expressions-clés **uniquement au début**
        first_line += " "
        match = re.match(r"^((#.*?#)\s)*", first_line)
        if match:
            expressions_brutes = match.group(0)  # Les expressions trouvées
            metadata["expressions_clefs"] = re.findall(r"#(.*?)#", expressions_brutes)
            first_line = first_line[len(expressions_brutes):]  # Supprimer les expressions de la première ligne

        # Reconstruction du message propre
        cleaned_message = (first_line.strip() + "\n" + remaining_text.strip()).strip()

        # Extraction d'une URL si elle est à la fin du message
        url_match = re.search(r"(https?://[^\s]+)$", cleaned_message, re.MULTILINE)
        if url_match:
            metadata["url"] = url_match.group(1)
            cleaned_message = cleaned_message.replace(metadata["url"], "").strip()  # Retirer l'URL du texte

        return metadata, cleaned_message

    def _append_to_file(self, filepath: str, message: str):
        """Ajoute un message structuré à un fichier YAML"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Extraction des métadonnées
        metadata, cleaned_message = self._extract_metadata(message)

        # Création de l'entrée
        entry = {
            "date": timestamp,
            "expressions_clefs": metadata["expressions_clefs"],
            "message": cleaned_message
        }

        if metadata["url"]:
            entry["url"] = metadata["url"]

        # Charger l'ancien contenu (si fichier existe)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f) or []
                except yaml.YAMLError:
                    data = []
        else:
            data = []

        # Ajouter la nouvelle entrée
        data.append(entry)

        # Sauvegarder dans le fichier YAML
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True)

    def _search_in_file(self, filepath: str, search_term: str):
        """Recherche les messages contenant le terme donné"""
        if not os.path.exists(filepath):
            return "Aucune note enregistrée."

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or []
            except yaml.YAMLError:
                return "Erreur de lecture du fichier."

        # Filtrer les messages contenant le terme recherché (insensible à la casse)
        results = [entry["message"] for entry in data if re.search(search_term, entry["message"], re.IGNORECASE)]

        if results:
            return f"Résultats de recherche ({len(results)} trouvés) :\n" + "\n".join(results[:5])  # Limite à 5 résultats
        else:
            return "Aucun résultat trouvé."

    def f(self, message: str, utilisateur: str, attachments):
        logger.info(f"Message de {utilisateur} : {message}")

        if not message.strip():
            return "Message vide"

        user_file = self._get_user_file(utilisateur)

        try:
            if message.startswith("s "):  # Recherche
                search_term = message[2:].strip()
                if not search_term:
                    return "Veuillez fournir un terme de recherche."
                return self._search_in_file(user_file, search_term)

            else:  # Ajout du message
                self._append_to_file(user_file, message)
                return f"'{message[:10]}...' ajouté avec succès."

        except Exception as e:
            logger.error(f"Erreur dans l'enregistrement ou la recherche : {e}")
            return "Une erreur s'est produite."

    async def notify(self, msg: str, to: str, attachments):
        logger.info(f"***************************** L'utilisateur {to} a écrit {msg}")
        reponse = self.f(msg, to, attachments)
        await self.__observable.notify(reponse, to, attachments)

    def prefix(self):
        return "!c"

class Plugin(IPlugin):
    def __init__(self, observable: IObservable):
        self.__observable = observable
        self.collect = Collect(self.__observable)
        logger.info(f"********************** Observateur créé {self.collect.prefix()}")

    def start(self):
        logger.info(f"********************** Inscription de {self.collect.prefix()}")
        self.__observable.subscribe(self.collect)

    async def stop(self):
        self.__observable.unsubscribe(self.collect)
