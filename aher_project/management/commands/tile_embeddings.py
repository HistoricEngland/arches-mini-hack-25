from django.core.management.base import BaseCommand
from aher_project.models.arches_embeddings import TileEmbedding, TileEmbeddingDocument

# Arches system settings resource instance ID 
# This is hardcoded in Arches so copying here for simplicity
RESOURCE_INSTANCE_ID = "a106c400-260c-11e7-a604-14109fd34195"

class Command(BaseCommand):
    help = 'create tile embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--truncate',
            action='store_true',
            help='Truncate existing tile embeddings before creating new ones',
        )
        parser.add_argument(
            '--resource',
            type=str,
            help='UUID of specific resource instance to index',
        )

    def handle(self, *args, **options):
        if options['truncate']:
            self.stdout.write('Truncating existing tile embeddings...')
            TileEmbeddingDocument.objects.all().delete()
        
        # get all tiles where the resource instance is not the Arches system settings
        tiles = TileEmbedding.objects.exclude(resourceinstance='a106c400-260c-11e7-a604-14109fd34195')
        
        # filter by resource instance if specified
        if options['resource']:
            tiles = tiles.filter(resourceinstance=options['resource'])
            self.stdout.write(f'Indexing tiles for resource instance: {options["resource"]}')
            
        count = tiles.count()
        for tile in tiles:
            # try to get existing document or create new one
            ted, created = TileEmbeddingDocument.objects.get_or_create(tile=tile)
            
            # update document and embedding regardless of whether it's new or existing
            ted.document = tile.get_tile_display()
            ted.embedding = tile.get_embedding()
            ted.save()
            
            action = 'Created' if created else 'Updated'
            count -= 1
            self.stdout.write(f'{action} embedding for tile. {count} tiles remaining')
            
        self.stdout.write(self.style.SUCCESS('Successfully created/updated tile embeddings'))
