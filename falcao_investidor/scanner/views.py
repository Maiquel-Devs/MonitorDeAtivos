# scanner/views.py

from django.shortcuts import render
# Importamos o modelo 'Oportunidade' para buscar os resultados salvos
from .models import Oportunidade
# Importamos a nossa nova tarefa do Celery
from .tasks import analisar_mercado_task

def dashboard_view(request):
    

    # Dispara a tarefa de análise em segundo plano.
    # O .delay() diz ao Celery: "pegue esta tarefa e execute quando puder".
    # O site não espera a tarefa terminar.
    analisar_mercado_task.delay()

    # Busca no banco de dados todas as oportunidades que foram salvas pela última análise
    # e as ordena pela maior queda.
    oportunidades_salvas = Oportunidade.objects.all().order_by('-percentual_queda')

    # Prepara os dados para enviar ao template
    context = {
        'oportunidades': oportunidades_salvas,
    }
    
    # Renderiza o template com os resultados já prontos, carregando a página instantaneamente.
    # Note que troquei o nome do template para não confundir (mas você pode usar o nome que preferir)
    return render(request, 'scanner/dashboard_celery.html', context)