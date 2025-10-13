# scanner/tasks.py
from celery import shared_task
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from .models import Ativo, Oportunidade

PERIODO_ANALISE = "3mo"
PERCENTUAL_QUEDA_GATILHO = 0.15

@shared_task
def analisar_mercado_task():
    print("---[CELERY] Iniciando tarefa de análise de mercado.---")
    Oportunidade.objects.all().delete() # Limpa as oportunidades antigas
    
    todos_ativos = Ativo.objects.all()
    tickers = [ativo.ticker for ativo in todos_ativos]
    mapa_tickers = {ativo.ticker: ativo for ativo in todos_ativos}

    if not tickers: return "Nenhum ativo para analisar."

    dados_completos = yf.download(tickers, period=PERIODO_ANALISE, progress=False, auto_adjust=True)
    if dados_completos.empty: return "Falha ao baixar dados."

    for ticker in tickers:
        try:
            high_series = dados_completos['High'][ticker] if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos['High']
            close_series = dados_completos['Close'][ticker] if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos['Close']
            high_series = high_series.dropna(); close_series = close_series.dropna()
            if close_series.empty: continue

            preco_maximo = high_series.max()
            preco_atual = close_series.iloc[-1]

            if preco_atual <= preco_maximo * (1 - PERCENTUAL_QUEDA_GATILHO):
                queda_percentual = ((preco_atual - preco_maximo) / preco_maximo) * 100
                ativo_obj = mapa_tickers[ticker]
                
                print(f"---[CELERY] Oportunidade encontrada em {ticker}! ---")

                # Salva a oportunidade no banco de dados
                Oportunidade.objects.create(
                    ativo=ativo_obj,
                    preco_maximo=preco_maximo,
                    preco_atual=preco_atual,
                    percentual_queda=abs(queda_percentual),
                    # A geração de gráfico pode ser otimizada depois, por enquanto deixamos vazio
                    grafico_base64="" 
                )
        except Exception as e:
            print(f"---[CELERY] Erro ao processar {ticker}: {e} ---")
    
    return f"Análise concluída. {Oportunidade.objects.count()} oportunidades salvas."