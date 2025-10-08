# scanner/admin.py

from django.contrib import admin
from .models import Setor, Ativo

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'nome_empresa', 'setor', 'tipo')
    list_filter = ('setor', 'tipo')
    search_fields = ('ticker', 'nome_empresa')