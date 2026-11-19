from django.urls import path
from django.views.generic import TemplateView

app_name = "personal"


def page(template):
    return TemplateView.as_view(template_name=f"personal/{template}.html")


urlpatterns = [
    path("", page("index"), name="index"),
    path("cv/", page("cv"), name="cv"),
    path("resume/", page("resume"), name="resume"),
    path("links/", page("links"), name="links"),
    path("planetarium/", page("planetarium"), name="planetarium"),
]
