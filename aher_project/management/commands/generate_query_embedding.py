from django.core.management.base import BaseCommand
from aher_project.ai_utils.embedding import get_embedder

# Arches system settings resource instance ID 
# This is hardcoded in Arches so copying here for simplicity
RESOURCE_INSTANCE_ID = "a106c400-260c-11e7-a604-14109fd34195"

class Command(BaseCommand):
    help = 'create tile embeddings'
    def add_arguments(self, parser):
        parser.add_argument(
                '-q',
                type=str,
                help='The query as a string in quotes',
            )
    
    def handle(self, *args, **options):
        # recieve a string representing a query and generate an embedding as the output this is so we can test the database
        print(args)
        query = options['q']
        embedder = get_embedder()
        print(embedder.embed_text(query))

