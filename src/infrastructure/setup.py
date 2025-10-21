import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.models import (
    SearchIndexerDataSourceConnection,
    SearchIndexerDataContainer,
    SearchIndexerDataSourceType,
    VisionVectorizeSkill,
    InputFieldMappingEntry, 
    OutputFieldMappingEntry,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
    SearchIndex,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjection,
    SearchIndexerIndexProjectionsParameters,
    IndexProjectionMode,
    CognitiveServicesAccountKey,
    SearchIndexerSkillset,
    SearchIndexer,
    IndexingParameters,
    IndexingParametersConfiguration,
    BlobIndexerParsingMode,
    AIServicesVisionVectorizer,
    AIServicesVisionParameters
)
from dotenv import load_dotenv
load_dotenv()


class AISearchSetup():
    def __init__(self, base_name: str):
        self.index_name = f"{base_name}-index"
        self.skillset_name = f"{base_name}-skillset"
        self.index_client = SearchIndexClient(
            endpoint=os.getenv("AI_SEARCH_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AI_SEARCH_KEY")),
        )
        self.indexer_client = SearchIndexerClient(
            endpoint=os.getenv("AI_SEARCH_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AI_SEARCH_KEY")),
        )
        self.connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
        self.cognitive_services_key = os.getenv("AZURE_FOUNDRY_API_KEY")
        self.foundry_api_key = os.getenv("AZURE_FOUNDRY_API_KEY")

    def create_index(self):
        fields = [
            SearchField(
                name='parent_id', 
                type=SearchFieldDataType.String,     
                sortable=True, 
                filterable=True, 
                facetable=True
            ),
            SearchField(
                name="document_id", 
                type=SearchFieldDataType.String, 
                facetable=True,
                sortable=True, 
                filterable=True,
                key=True,
                analyzer_name="keyword",
            ),
            SearchField(
                name="metadata_storage_path", 
                type=SearchFieldDataType.String, 
                facetable=True,
                sortable=True, 
                filterable=True
            ),
            SearchField(
                name="image_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1024,
                vector_search_profile_name="VisionEmbeddingProfile"
            )
        ]

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="Hnsw",
                    kind=VectorSearchAlgorithmKind.HNSW,
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric=VectorSearchAlgorithmMetric.COSINE,
                    ),
                ),
                ExhaustiveKnnAlgorithmConfiguration(
                    name="ExhaustiveKnn",
                    kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                    parameters=ExhaustiveKnnParameters(
                        metric=VectorSearchAlgorithmMetric.COSINE,
                    ),
                ),
            ],
            # Hnsw is good/fast for large datasets, but is approximative
            profiles=[
                VectorSearchProfile(
                    name="HnswProfile",
                    algorithm_configuration_name="Hnsw",
                ),
                VectorSearchProfile(
                    name="ExhaustiveKnnProfile",
                    algorithm_configuration_name="ExhaustiveKnn",
                ),
                VectorSearchProfile(
                    name="VisionEmbeddingProfile",
                    algorithm_configuration_name="ExhaustiveKnn",
                    vectorizer_name="aiServicesVision",
                ),
            ],
            vectorizers=[
                AIServicesVisionVectorizer(
                    vectorizer_name="aiServicesVision",
                    ai_services_vision_parameters=AIServicesVisionParameters(
                        model_version="2023-04-15",
                        resource_uri="https://design-helper-foundry.cognitiveservices.azure.com/",
                        api_key=self.foundry_api_key
                    )
                )
            ]
        )

        index = SearchIndex(
            name=self.index_name, fields=fields, vector_search=vector_search
        )

        result = self.index_client.create_or_update_index(index)

        print(f"{result.name} created")

    def create_data_source(self, container_name: str, folder_name: str = None):
        """
        Creates a data source connection for Azure Blob Storage.

        Args:
            container_name (str): The name of the Azure Blob Storage container.
            folder_name (str, optional): The name of the folder within the container. Defaults to None.
        """
        # Define the data source connection
        container = SearchIndexerDataContainer(name=container_name, query=folder_name)
        data_source_connection = SearchIndexerDataSourceConnection(
            name=f"{self.index_name}-blob",
            type=SearchIndexerDataSourceType.AZURE_BLOB,
            connection_string=self.connection_string,
            container=container,
        )

        # Create or update the data source connection
        self.data_source = self.indexer_client.create_or_update_data_source_connection(
            data_source_connection
        )

        # Create the data source in Azure Search
        print(f"Data source: {self.data_source.name} was created successfully.")

    def create_skillset(self):
        skills = [
            VisionVectorizeSkill(
                model_version="2023-04-15",
                context="/document",
                inputs=[
                    InputFieldMappingEntry(
                        name="url", source="/document/metadata_storage_path"
                    ),
                    InputFieldMappingEntry(
                        name="queryString",
                        source="/document/metadata_storage_sas_token"
                    )
                ],
                outputs=[
                    OutputFieldMappingEntry(
                        name="vector",
                        target_name="image_vector"
                    )
                ]
            )
        ]

        index_projection = SearchIndexerIndexProjection(
            selectors=[
                SearchIndexerIndexProjectionSelector(
                    target_index_name=self.index_name,
                    parent_key_field_name="parent_id",
                    source_context="/document",
                    mappings=[
                        InputFieldMappingEntry(
                            name="metadata_storage_path", source="/document/metadata_storage_path"
                        ),
                        InputFieldMappingEntry(
                            name="image_vector", source="/document/image_vector"
                        )
                    ],
                ),
            ],
            parameters=SearchIndexerIndexProjectionsParameters(
                projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS
            ),
        )


        cognitive_services_account_key = CognitiveServicesAccountKey(
            key=self.cognitive_services_key
        )

        # Create the skillset
        skillset = SearchIndexerSkillset(
            name=self.skillset_name,
            description="Skillset to generate metadata and embeddings",
            skills=skills, 
            index_projection=index_projection, 
            cognitive_services_account=cognitive_services_account_key
        )


        self.indexer_client.create_or_update_skillset(skillset)
        print(f"{skillset.name} created")

    def create_indexer(self):
        """
        Creates an indexer with the specified skillset and data source.
        """
        # Create an indexer
        indexer_name = f"{self.index_name}-indexer"

        if not hasattr(self, "data_source"):
            raise Exception(
                "Data source not defined. Please create a data source before creating an indexer."
            )

        try:
            self.indexer_client.get_skillset(self.skillset_name)
        except ResourceNotFoundError:
            raise Exception(
                "Skillset not defined. Please create a skillset before creating an indexer"
            )

        indexer = SearchIndexer(
            name=indexer_name,
            description="Indexer to index documents and generate embeddings",
            skillset_name=self.skillset_name,
            target_index_name=self.index_name,
            data_source_name=self.data_source.name,
            parameters=IndexingParameters(
                configuration=IndexingParametersConfiguration(
                    parsing_mode=BlobIndexerParsingMode.DEFAULT,
                    query_timeout=None,
                    allow_skillset_to_read_file_data=True, 
                    image_action="generateNormalizedImages"
                )
            ),
        )

        self.indexer_client.create_or_update_indexer(indexer)
        print(f"{indexer.name} created")

if __name__ == "__main__":
    base_name = "design-helper"

    ai_search_setup = AISearchSetup(base_name=base_name)

    ai_search_setup.create_index()
    ai_search_setup.create_data_source(container_name="website-screens-test")
    ai_search_setup.create_skillset()
    ai_search_setup.create_indexer()