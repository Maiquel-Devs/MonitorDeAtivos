# scanner/views.py

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from .models import Ativo

# --- PARÂMETROS DA ANÁLISE ---
PERIODO_ANALISE = "3mo"
PERCENTUAL_QUEDA_GATILHO = 0.15

def gerar_grafico_base64(ticker, setor, dados, maxima, data_maxima, atual, data_atual, queda_percentual):
    """Função auxiliar para criar os gráficos em base64."""
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(dados.index, dados['Close'], label='Preço de Fechamento', color='deepskyblue')
    ax.plot(data_maxima, maxima, 'ro', markersize=8, label=f'Máxima: ${maxima:.2f}')
    ax.plot(data_atual, atual, 'go', markersize=8, label=f'Atual: ${atual:.2f}')
    ax.plot([data_maxima, data_atual], [maxima, atual], 'r--', alpha=0.7)
    
    titulo = f"Setor: {setor}\n{ticker} | Queda de {abs(queda_percentual):.2%} da Máxima"
    ax.set_title(titulo)
    ax.set_ylabel('Preço')
    ax.legend()
    ax.grid(True)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def dashboard_view(request):
    """
    Esta é a nossa view principal. Ela executa o scanner e renderiza a página.
    """
    print("---==[ PROJETO FALCÃO: Iniciando Análise Dinâmica ]==---")

    oportunidades_encontradas = []
    todos_ativos = Ativo.objects.all().select_related('setor')
    tickers = [ativo.ticker for ativo in todos_ativos]
    mapa_tickers = {ativo.ticker: ativo for ativo in todos_ativos}

    if tickers:
        print(f'Baixando dados para {len(tickers)} ativos...')
        dados_completos = yf.download(tickers, period=PERIODO_ANALISE, progress=False, auto_adjust=True)
        
        if not dados_completos.empty:
            print('Processando dados e procurando oportunidades...')
            for ticker in tickers:
                try:
                    high_series = dados_completos['High'][ticker] if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos['High']
                    close_series = dados_completos['Close'][ticker] if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos['Close']

                    high_series = high_series.dropna()
                    close_series = close_series.dropna()

                    if close_series.empty: continue

                    preco_maximo = high_series.max()
                    data_maximo = high_series.idxmax()
                    preco_atual = close_series.iloc[-1]
                    data_atual = close_series.index[-1]

                    if preco_atual <= preco_maximo * (1 - PERCENTUAL_QUEDA_GATILHO):
                        queda_percentual = (preco_atual - preco_maximo) / preco_maximo
                        ativo_obj = mapa_tickers[ticker]
                        
                        print(f'🦅 Oportunidade encontrada em {ticker}!')

                        grafico_base64 = gerar_grafico_base64(ticker, ativo_obj.setor.nome, dados_completos.xs(ticker, level=1, axis=1) if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos, preco_maximo, data_maximo, preco_atual, data_atual, queda_percentual)
                        
                        oportunidades_encontradas.append({
                            'ativo': ativo_obj, 'queda_percentual': f"{abs(queda_percentual):.2%}",
                            'preco_maximo': f"{preco_maximo:.2f}", 'data_maximo': data_maximo.strftime('%d/%m/%Y'),
                            'preco_atual': f"{preco_atual:.2f}", 'grafico_base64': grafico_base64
                        })
                except Exception as e:
                    print(f'❌ Erro ao processar {ticker}: {e}')

    context = {
        'oportunidades': oportunidades_encontradas,
        'total_analisado': len(tickers),
        'total_encontrado': len(oportunidades_encontradas),
        'PERIODO_ANALISE': PERIODO_ANALISE,
        'PERCENTUAL_QUEDA_GATILHO': PERCENTUAL_QUEDA_GATILHO,
    }
    
    # Aqui usamos o nome do template que você escolheu
    return render(request, 'scanner/relatorio_template.html', context)