from abc import ABC, abstractmethod
from azure.search.documents.models import VectorizableImageBinaryQuery

class AbsAISearchService(ABC):
    @abstractmethod
    def get_image_embedding(self, img_path: str) -> VectorizableImageBinaryQuery:
        """
        Generate an image embedding from the given image path.
        Args:
            img_path (str): The file path to the image.
        Returns:
            VectorizableImageBinaryQuery: The vectorized image query.
        """
        pass


    @abstractmethod
    def search(self, vector_queries: list, top_k: int = 10) -> list:
        """
        Perform a search using AI capabilities.
        Args:
            vector_queries (list[Any]): A list of vectorized queries to search for.
            top_k (int, optional): The number of top results to return. Defaults to 10.
        """
        pass