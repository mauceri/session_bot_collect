import logging
import os
import sys
import time
from .interfaces import IObserver, IObservable, IPlugin
#from sqlite_handler import SQLiteHandler
#from interrogationLocale import InterrogationLocale
from signets import text_milvus_handler as tmh;
import signets.text_milvus_handler as mth

logger = logging.getLogger()
if logger.hasHandlers():
    logger.handlers.clear()

# Configurer le logging pour qu'il affiche sur stdout
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
    
class Signets(IObserver):
    def __init__(self,observable:IObservable=None):
        self.__observable = observable

        # Déterminer le répertoire du plugin
        plugin_dir = os.path.dirname(os.path.abspath(__file__))

        # Chemin du nouveau répertoire 'data'
        self.data_dir = os.path.join(plugin_dir, 'data')

        # Créer le répertoire de données s'il n'existe pas
        os.makedirs(self.data_dir, exist_ok=True)
        db_path = os.path.join(self.data_dir, 'test_context.sqlite')
        
        logger.info(f"********************** Répertoire de données du plugin : {self.data_dir}")
 

    def quoi_faire(self,message, utilisateur):
        if message.startswith("s "):
            return m.search_text(message.replace("s ",message),utilisateur)
        else:
            if message != "":
                try:
                    m.insert_text(message,utilisateur)
                    return f"{message[:10]}... sauvé"
                except:
                    return f"{message[:10]}... n'a pas été sauvé"
            else:
                return "message vide"
        
    def f(self,message:str,utilisateur:str,attachments):
        logger.info(f"Message de {utilisateur} : {message}")            
        reponse = ""
        try:
            stime = time.time()
            m = tmh.text_milvus_handler()
            m.disconnect()
            m.connect(host="sanroque")
            
            if m.session_id_ok(utilisateur) :
                if message.startswith("s "):
                    reponse = m.search_text(message.replace("s ",message),utilisateur)
                else:
                    if message != "":
                        try:
                            m.insert_text(message,utilisateur)
                            reponse = f"{message[:10]}... sauvé"
                        except:
                            reponse = f"{message[:10]}... n'a pas été sauvé"
                    else:
                        reponse = "message vide"
            else:
                reponse = f"{utilisateur} inconnu"
 
        except BaseException as e:
            logger.error(f"Quelque chose n'a pas fonctionné {e}")
            reponse = None
        reponset = f"{time.time()-stime} {reponse}"
        return reponset

    async def notify(self,msg:str,to:str,attachments):
        logger.info(f"***************************** L'utilisateur {to} a écrit {msg}")
        reponse = self.f(msg,to,attachments)
        if reponse == None:
            reponse = "Une erreur s'est produite lors de l'interrogation du LLM"
        await self.__observable.notify(reponse, to, attachments)

    def prefix(self):
        return "!f"
    
class Plugin(IPlugin):
    def __init__(self,observable:IObservable):
        self.__observable = observable
        self.signets = Signets(self.__observable)
        # Autres initialisations
        logger.info(f"********************** Observateur créé {self.signets.prefix()}")
        
    def start(self):
        logger.info(f"********************** Inscripton de {self.signets.prefix()}")
        self.__observable.subscribe(self.signets)

    async def stop(self):
        self.__observable.unsubscribe(self.signets)