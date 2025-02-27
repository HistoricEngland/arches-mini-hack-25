# create a django migration that installes the pgvector extension

from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    
    dependencies = [
        ('aher_project', '0001_initial'),
    ]

    operations = [
        VectorExtension()
    ]