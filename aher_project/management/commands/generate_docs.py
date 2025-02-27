from django.core.management.base import BaseCommand
from aher_project.management.commands.util.scraper import main as scraper_main

class Command(BaseCommand):
    help = 'Generate documentation by scraping resources'

    def handle(self, *args, **options):
        self.stdout.write('Starting document generation...')
        scraper_main()
        self.stdout.write(self.style.SUCCESS('Successfully generated documents'))