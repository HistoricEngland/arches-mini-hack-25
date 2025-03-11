from django.core.management.base import BaseCommand
from aher_project.models.arches_embeddings import TileEmbedding, TileEmbeddingDocument

# Arches system settings resource instance ID 
# This is hardcoded in Arches so copying here for simplicity
RESOURCE_INSTANCE_ID = "a106c400-260c-11e7-a604-14109fd34195"

class Command(BaseCommand):
    """
    Command for generating and managing tile embeddings.
    """
    
    help = "Generate embeddings for arches tile data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--truncate',
            action='store_true',
            help='Truncate existing embeddings before regenerating',
        )
        parser.add_argument(
            '--resource',
            help='Only process tiles for a specific resource instance',
        )

    def handle(self, *args, **options):
        if options['truncate']:
            self.stdout.write('Truncating existing tile embeddings...')
            TileEmbeddingDocument.objects.all().delete()
        
        # get all tiles where the resource instance is not the Arches system settings
        tiles = TileEmbedding.objects.exclude(resourceinstance=RESOURCE_INSTANCE_ID)
        
        # filter by resource instance if specified
        if options['resource']:
            tiles = tiles.filter(resourceinstance=options['resource'])
            self.stdout.write(f'Indexing tiles for resource instance: {options["resource"]}')
            
        count = tiles.count()
        for tile in tiles:
            # try to get existing document or create new one
            ted, created = TileEmbeddingDocument.objects.get_or_create(tile=tile)
            
            # update document, embedding, and resourceinstance regardless of whether it's new or existing
            ted.document = tile.get_tile_display()
            ted.embedding = tile.get_embedding()
            ted.resourceinstance = tile.resourceinstance
            ted.save()
            
            if created:
                self.stdout.write(f'Created new embedding for tile {tile.tileid}')
            else:
                self.stdout.write(f'Updated embedding for tile {tile.tileid}')

        self.stdout.write(f'Successfully processed {count} tiles')
