from django.db import migrations, models
import django.db.models.deletion

def populate_resource_instance(apps, schema_editor):
    TileEmbeddingDocument = apps.get_model('aher_project', 'TileEmbeddingDocument')
    TileModel = apps.get_model('models', 'TileModel')
    
    # Update all TileEmbeddingDocuments with their resource instance IDs
    for ted in TileEmbeddingDocument.objects.all():
        if ted.tile:
            ted.resourceinstance_id = ted.tile.resourceinstance_id
            ted.save()

class Migration(migrations.Migration):

    dependencies = [
        ('aher_project', '0007_chatplugin'),
    ]

    operations = [
        migrations.AddField(
            model_name='tileembeddingdocument',
            name='resourceinstance',
            field=models.ForeignKey(
                db_column='resourceinstanceid',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='models.resourceinstance'
            ),
        ),
        migrations.RunPython(
            populate_resource_instance,
            reverse_code=migrations.RunPython.noop
        ),
    ]