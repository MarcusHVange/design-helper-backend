from azure.search.documents.models import VectorizableImageBinaryQuery
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import base64
import os
from src.infrastructure.config.app_config import AppConfig

class AISearchService():
    def __init__(self, app_config: AppConfig):
        self.credential = AzureKeyCredential(app_config.AI_SEARCH_KEY)
        self.search_client = SearchClient(
            endpoint=app_config.AI_SEARCH_ENDPOINT,
            index_name="design-helper-index",
            credential=self.credential,
        )

    def get_image_embedding(self, img_path: str):
        # Turn image into base64
        with open(img_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        vector_query = VectorizableImageBinaryQuery(
            fields="image_vector",
            base64_image=base64_image,
            k_nearest_neighbors=2,
        )

        return vector_query
    
    def search(self):
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        img_path = os.path.join(workspace_root, "testimg.png")

        vector_query = self.get_image_embedding(img_path)

        results = self.search_client.search(
            vector_queries=[vector_query]
        )

        res = [r for r in results]

        return res
