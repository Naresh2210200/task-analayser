"""
URL configuration for task_analyzer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include 


def root_view(request):
  """
  Simple root endpoint so / doesn't 404.
  Points users to the API and frontend.
  """
  return JsonResponse(
      {
          "message": "Smart Task Analyzer backend is running.",
          "api_base": "/api/tasks/",
          "health": "/api/tasks/health/",
          "frontend_hint": "Open frontend/index.html in your browser to use the UI.",
      }
  )

urlpatterns = [
    path("", root_view, name="root"),
    path("admin/", admin.site.urls),
    path("api/tasks/", include("tasks.urls")),
]
