from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    return HttpResponse("Welcome to the Home Page")

urlpatterns = [
    # path("grappelli/", include("grappelli.urls")),
    path('admin/', admin.site.urls),
    path('api/v1/', include('courses.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', home, name='home'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
