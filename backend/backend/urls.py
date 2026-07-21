from django.contrib import admin
from django.urls import path, include
from api.utils import short_link_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<str:short_link>/',
        short_link_redirect,
        name='short-link-redirect'
    ),
]
