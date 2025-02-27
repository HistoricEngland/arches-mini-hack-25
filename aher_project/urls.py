from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from aher_project.views.ai import AIAPIView, ChatAPIView

# COPIED FROM ./arches_her/docker/aher_project/docker/urls.py

urlpatterns = [
    path('', include('arches.urls')),
   path("", include("arches_her.urls")),
   path('aiapi/', AIAPIView.as_view(), name='ai-api'),
   path('chatapi/', ChatAPIView.as_view(), name='chat-api'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.SHOW_LANGUAGE_SWITCH is True:
#     urlpatterns = i18n_patterns(*urlpatterns)
