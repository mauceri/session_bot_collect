from towhee import ops, pipe, DataCollection

from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
import sys
import uuid
import numpy as np
from pymilvus import utility

class milvus_handler:
    def __init__(self,model_name='sentence-transformers/paraphrase-albert-small-v2'):
        print(f"Aqui")
        self.model_name = model_name

    def connect(self,host="localhost",port="19530"):
        print(f"connection to Milvus server")
        connections.connect(
            alias="default",
            host=host,  # ou l'adresse IP du serveur Milvus
            port=port       # le port exposé dans votre fichier docker-compose.yml
        )
    
    def create_collection(self,collection_name, dim=768):
        print(f"*************** dim = {dim}")
        if utility.has_collection(collection_name):
            Collection(collection_name).drop()
        
        fields = [
            FieldSchema (name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1000),   
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        schema = CollectionSchema(fields=fields, description='Text embeddings collection')
        collection = Collection(name=collection_name, schema=schema)

        index_params = {
            'metric_type': "COSINE",
            'index_type': "IVF_FLAT",
            'params': {"nlist": 128}
        }
        collection.create_index(field_name='embedding', index_params=index_params)
        return collection

    def insert(self, text,dim=768,collection_name = 'text_embeddings_collection'):
        # Pipeline Towhee pour créer des plongements
        embedding_pipeline = (
            pipe.input('text')
            .map('text', 'embedding', ops.sentence_embedding.transformers(model_name=self.model_name))
            .output('embedding')
        )

        # Calculer le plongement pour la chaîne de caractères
        result = embedding_pipeline(text).to_list()
        print(f"************************ {len(result)}")
        # Vérifier si un résultat a été produit
        if len(result) == 0:
            raise ValueError("Le pipeline n'a pas pu générer un plongement.")
        
        # Extraire le vecteur d'embedding
        embedding = result[0][0]

        # Obtenir la collection Milvus
        collection = Collection(collection_name)

        # Créer les entités à insérer dans Milvus
        entities = [
            [text],        # Texte original
            [embedding]    # Plongement
        ]

        # Insérer les entités dans Milvus
        insert_result = collection.insert(entities)
        print(f"Texte inséré avec succès avec l'ID : {insert_result.primary_keys}")

    def search(self,query,collection_name='text_embeddings_collection'):
        # Connexion au serveur Milvus
        connections.connect(alias="default", host="localhost", port="19530")

        # Charger la collection existante 
        if not utility.has_collection(collection_name):
            raise ValueError(f"La collection '{collection_name}' n'existe pas.")

        collection = Collection(name=collection_name)
        collection.load()
        # Créer un pipeline Towhee pour générer le plongement de la requête
        embedding_pipeline = (
            pipe.input('text')
                .map('text', 'embedding', ops.sentence_embedding.transformers(model_name='sentence-transformers/paraphrase-albert-small-v2'))
                .output('embedding')
        )

        #print(f"*************** { embedding_pipeline(query).to_list()}")   
        # Calculer le plongement de la requête
        query_embedding = embedding_pipeline(query).to_list()[0][0]

        # Effectuer une recherche avec la métrique Cosine
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            output_fields=["text"],
            limit=3  # Limiter à 10 résultats pour l'exemple
        )
        print(f"++++++++++++ {results}")
        # Filtrer les résultats basés sur le seuil
        matching_results = []
        for result in results:
            print(f"result = {result}")
            #if result.score >= threshold:
            matching_results.append(result)

        # Afficher les résultats
        if matching_results:
            print(f"Chaînes similaires trouvées pour la requête '{query}':")
            for res in matching_results:
                print(f"res: {res}")
        else:
            print(f"Aucune chaîne n'a dépassé le seuil.")
