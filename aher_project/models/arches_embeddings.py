import uuid, json
from django.contrib.gis.db import models
from django.db import connection
from arches.app.models.models import TileModel
from arches.app.models.resource import Resource
from arches.app.models.system_settings import settings
from pgvector.django import VectorField, HnswIndex
from typing import List, Dict, Any

from aher_project.ai_utils.embedding import get_embedder

class TileEmbeddingDocument(models.Model):
    tileembeddingid = models.UUIDField(primary_key=True)
    tile = models.ForeignKey("models.TileModel", db_column="tileid", null=True, on_delete=models.CASCADE)
    resourceinstance = models.ForeignKey(Resource, db_column="resourceinstanceid", null=True, on_delete=models.CASCADE)
    document = models.TextField()
    embedding = VectorField(dimensions=768)

    # during initialization, generate a UUID for the tileembeddingid
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tileembeddingid = uuid.uuid4()

    class Meta:
        managed = True
        db_table = "tile_embeddings"
        indexes = [
            HnswIndex(
                name='idx_tile_embedding',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops']
            )
        ]

    @classmethod
    def find_similar(cls, query_text, limit=5, similarity_threshold=0.7):
        """
        Find similar documents using cosine similarity.
        
        Args:
            query_embedding: The embedding vector to compare against
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (between 0 and 1)
        
        Returns:
            QuerySet of TileEmbeddingDocument ordered by similarity
        """
        embedder = get_embedder()
        query_embedding = embedder.embed_text(query_text)
        return cls.objects.filter(
            embedding__cosine_distance=query_embedding
        ).order_by(
            'embedding__cosine_distance'
        )[:limit]

    @classmethod
    def aggregate_by_resource(cls, queryset: List[Any]) -> List[Any]:
        """
        Aggregate tile embeddings by resource instance.
        
        Args:
            queryset: An iterable of TileEmbeddingDocument objects
            
        Returns:
            dict: A dictionary where keys are resource instance IDs and values are dictionaries containing:
                - documents: List of documents for that resource
                - resourceinstance: Object containing resource details including name and description
        """
        aggregated = {}
        
        for embedding_doc in queryset:
            resource_id = str(embedding_doc.resourceinstance.resourceinstanceid)
            
            if resource_id not in aggregated:
                aggregated[resource_id] = {
                    'order': 0, #embedding_doc.embedding__cosine_distance,
                    'document': f"# Title: {embedding_doc.resourceinstance.displayname()}\n ## Summary Description: {embedding_doc.resourceinstance.displaydescription()}\n ## Content:",
                    'document_source_url': f"{settings.PUBLIC_SERVER_ADDRESS}/report/{str(embedding_doc.resourceinstance.resourceinstanceid)}"
                }
            
            aggregated[resource_id]['document'] = f"{aggregated[resource_id]['document']}\n\n{embedding_doc.document}"
            aggregated[resource_id]['order'] += embedding_doc.distance

        # convert aggregate dict to list
        print(aggregated.values)
        return list(aggregated.values())

# add a class that extends TileModel to create a proxy model so a tile 

class TileEmbedding(TileModel):
    class Meta:
        proxy = True

    def get_tile_display(self):
        display_data = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT public.__arches_display_tiledata_compact(%s::jsonb, %s::text, %s::boolean)::text;
                    """,
                    [json.dumps(self.data), 'en', True]
                )
                
                return json.dumps(cursor.fetchone()[0])
        except Exception as e:
            print(e)
        
        return display_data
        
    def get_embedding(self):
        embedder = get_embedder()
        return embedder.embed_text(self.get_tile_display())

# cd /aher_project && python3 manage.py shell

# from aher_project.models.arches_embeddings import TileEmbedding
# qt = TileEmbedding.objects.filter(resourceinstance='0ba43fbd-b757-4bfd-914b-2f6c87c03b66')[:10]
# qt[1].get_embedding()
# http://host.docker.internal:11434