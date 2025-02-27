# create a django migration that installes the pgvector extension

from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('aher_project', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS vector;',
            reverse_sql='DROP EXTENSION IF EXISTS vector;'
        )
    ]