# scanner/models.py

from django.db import models

class Setor(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


class Ativo(models.Model):
    TIPO_CHOICES = [
        ('Ação', 'Ação'),
        ('BDR', 'BDR'),
        ('Cripto', 'Cripto'),
    ]

    ticker = models.CharField(max_length=20, unique=True)
    nome_empresa = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE, related_name='ativos')

    def __str__(self):
        return f"{self.ticker} ({self.nome_empresa})"
    

class Oportunidade(models.Model):
    ativo = models.ForeignKey(Ativo, on_delete=models.CASCADE)
    data_analise = models.DateTimeField(auto_now_add=True)
    preco_maximo = models.DecimalField(max_digits=10, decimal_places=2)
    preco_atual = models.DecimalField(max_digits=10, decimal_places=2)
    percentual_queda = models.DecimalField(max_digits=5, decimal_places=2)
    grafico_base64 = models.TextField()

    def __str__(self):
        return f"Oportunidade em {self.ativo.ticker} em {self.data_analise.strftime('%d/%m/%Y')}"