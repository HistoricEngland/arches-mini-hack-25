# create a django migration that installes the pgvector extension

from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('aher_project', '0006_alter_tileembeddingdocument_tileembeddingid'),
    ]

    def add_plugins(apps, schema_editor):
        Plugin = apps.get_model("models", "Plugin")

        # Add chat
        Plugin.objects.update_or_create(
            pluginid="f15c864b-d76a-4222-89a1-23406fb66862",
            name="Chat",
            icon="fa fa-comments",
            component="views/components/plugins/chat",
            componentname="chat",
            slug="chat",
            config={},
            sortorder=0
        )

    def remove_plugins(apps, schema_editor):
        Plugin = apps.get_model("models", "Plugin")
        Plugin.objects.filter(pluginid="f15c864b-d76a-4222-89a1-23406fb66862").delete()



    operations = [
         migrations.RunPython(add_plugins, remove_plugins),
    ]