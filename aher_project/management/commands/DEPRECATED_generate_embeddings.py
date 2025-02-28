from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from django.db.utils import IntegrityError, InternalError
from arches.app.models.system_settings import settings
from arches.app.models.resource import Resource
from arches.app.utils.betterJSONSerializer import JSONSerializer
from aher_project.models import ResourceDocument
import numpy as np

class Command(BaseCommand):
    help = 'Generate disambiguated resource instance json, create embeddings, and save them to the ResourceDocument model'

    def handle(self, *args, **options):
        hide_hidden_nodes = True
        compact = True
        version = 'beta'
        user = User.objects.get(username='anonymous')
        perm = "read_nodegroup"
        serializer = JSONSerializer()
        print("Generating disambiguated resource instance json, creating embeddings, and saving them to the ResourceDocument model...")
        
        for resource in Resource.objects.all().prefetch_related("graph"):
            if resource.graph.isresource and str(resource.graph.graphid) != settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID:
                doc = self.remove_empty_dict_items(resource.to_json(
                    compact=compact, version=version, hide_hidden_nodes=hide_hidden_nodes, user=user, perm=perm
                ))
                doc["resource_type"] = resource.graph.name
                embedding = self.create_embedding(doc)

                try:
                    ResourceDocument.objects.update_or_create(
                        resourceinstanceid=resource.pk,
                        defaults={'document': doc, 'embedding': embedding}
                    )
                    #print(f"Resource {resource.pk} has been saved to the ResourceDocument model")
                except IntegrityError:
                    #print(f"Resource {resource.pk} already exists in the ResourceDocument model")
                    continue
                except InternalError as e:
                    print(f"Resource {resource.pk} could not be saved to the ResourceDocument model")
                    print(f"... {e}")
                    continue

        print("Done!")

    ignore_keys = [
        "valueid",
        "concept_id",
        "language_id",
        "valueid",
        "valuetype_id",
        "instance_details",
        "direction",
        "Geospatial Coordinates",
        "inverseOntologyProperty",
        "ontologyProperty",
        "resourceId",
        "resourceXresourceId",
        "graph_id",
        "legacyid",
        "map_popup",
        "concept_details",
        "@display_value"
    ]

    def remove_empty_dict_items(self, d):
        if not isinstance(d, (dict, list)):
            return d
        if isinstance(d, list):
            return [v for v in (self.remove_empty_dict_items(v) for v in d) if v]
        return {k: v for k, v in ((k, self.remove_empty_dict_items(v)) for k, v in d.items()) if v and not k in self.ignore_keys and v not in ["null", "Undefined"] and "Metatype" not in str(k)}

    def create_embedding(self, doc):
        # Placeholder for actual embedding logic
        return np.random.rand(128).tolist()


