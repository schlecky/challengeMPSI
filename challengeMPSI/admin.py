from django.contrib import admin
from django.utils.html import format_html
from .models import Etudiant, Classe, Epreuve, Succes, Domaine, Chapitre, Image

class EpreuveAdmin(admin.ModelAdmin):
    model = Epreuve
    ordering = ('domaine', 'etoiles')

class ImageAdmin(admin.ModelAdmin):
    list_display = ('image_url','image_preview')

    def image_url(self, obj):
        if obj.image:
            return obj.image.url
        return "-"

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 60px;" />', obj.image.url)
        return "-"
    image_url.short_description = "Image URL"

# Register your models here.

admin.site.register(Etudiant)
admin.site.register(Classe)
admin.site.register(Epreuve, EpreuveAdmin)
admin.site.register(Domaine)
admin.site.register(Chapitre)
admin.site.register(Succes)
admin.site.register(Image, ImageAdmin)

