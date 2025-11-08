import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "pet_control"
COLLECTION_NAME = "profiles"
PETS_COLLECTION_NAME = "pets"
VACCINES_COLLECTION_NAME = "vacinas"
ECTOPARASITES_COLLECTION_NAME = "ectoparasitas"
VERMIFUGOS_COLLECTION_NAME = "vermifugos"


class Database:
    """Classe para gerenciar conexões com MongoDB"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self._connect()
        
    def _connect(self):
        """Estabelece conexão com MongoDB"""
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.db = self.client[DB_NAME]
            
            # Testa conexão - skip em ambiente de teste (mongomock)
            if not str(self.client).startswith('mongomock'):
                self.client.admin.command("ismaster")
                
        except Exception as e:
            print(f"Could not connect to MongoDB: {e}")
            raise ConnectionError("Failed to connect to MongoDB.")
    
    def connect(self):
        """Método público para conectar (se já não estiver conectado)"""
        if not self.client:
            self._connect()
        return self
    
    def close(self):
        """Fecha a conexão com MongoDB"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
    
    @property
    def profiles_collection(self):
        return self.db[COLLECTION_NAME]
    
    @property
    def pets_collection(self):
        return self.db[PETS_COLLECTION_NAME]
        
    @property
    def vaccines_collection(self):
        return self.db[VACCINES_COLLECTION_NAME]
        
    @property
    def ectoparasites_collection(self):
        return self.db[ECTOPARASITES_COLLECTION_NAME]
        
    @property 
    def vermifugos_collection(self):
        return self.db[VERMIFUGOS_COLLECTION_NAME]


# Instância global do banco
database = Database()
