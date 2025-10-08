import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ===================================================================
# 1. CONFIGURAÇÕES GLOBAIS DO SCANNER
# ===================================================================
ACOES_PARA_MONITORAR = [
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'WEGE3.SA',
    'MGLU3.SA', 'ABEV3.SA', 'BBAS3.SA'
]
CRIPTOS_PARA_MONITORAR = [
    'BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'XRP-USD'
]
PERIODO_ANALISE = "3mo"
PERCENTUAL_QUEDA_GATILHO = 0.15

# ===================================================================
# 2. FUNÇÃO PARA GERAR O GRÁFICO (sem alterações)
# ===================================================================
def plotar_grafico(ticker, dados, maxima, data_maxima, atual, data_atual, queda_percentual):
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.figure(figsize=(12, 6))
    plt.plot(dados.index, dados['Close'], label='Preço de Fechamento', color='deepskyblue')
    plt.plot(data_maxima, maxima, 'ro', markersize=10, label=f'Máxima em 3M: ${maxima:.2f}')
    plt.plot(data_atual, atual, 'go', markersize=10, label=f'Preço Atual: ${atual:.2f}')
    plt.plot([data_maxima, data_atual], [maxima, atual], 'r--', alpha=0.7)
    titulo = f'{ticker} | Queda de {abs(queda_percentual):.2%} da Máxima em {PERIODO_ANALISE}'
    plt.title(titulo, fontsize=16)
    plt.ylabel('Preço', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.show()

# ===================================================================
# 3. FUNÇÃO DE PROCESSAMENTO EM LOTE (Nova Lógica)
# ===================================================================
def processar_lote_de_dados(dados_completos):
    """
    Processa um DataFrame contendo dados de múltiplos ativos.
    """
    # Quando baixamos vários tickers, os nomes das colunas são ('Close', 'PETR4.SA'), ('High', 'PETR4.SA'), etc.
    # Vamos pegar a lista de tickers únicos do segundo nível das colunas.
    tickers = dados_completos.columns.levels[1]

    for ticker in tickers:
        try:
            # Seleciona os dados de 'High' e 'Close' apenas para o ticker atual
            high_series = dados_completos['High'][ticker]
            close_series = dados_completos['Close'][ticker]

            # Remove dias sem negociação (NaN) para evitar erros nos cálculos
            high_series = high_series.dropna()
            close_series = close_series.dropna()

            if close_series.empty:
                print(f"⚠️  Dados de preço de fechamento vazios para '{ticker}' após limpeza. Pulando.")
                continue

            # Calcula os pontos de interesse
            preco_maximo = high_series.max()
            data_maximo = high_series.idxmax()
            preco_atual = close_series.iloc[-1] # .item() não é mais necessário aqui
            data_atual = close_series.index[-1]

            # Verifica se a queda atingiu o nosso gatilho
            if preco_atual <= preco_maximo * (1 - PERCENTUAL_QUEDA_GATILHO):
                queda_real_percentual = (preco_atual - preco_maximo) / preco_maximo
                
                print("\n" + "="*50)
                print(f"🦅 ALERTA FALCÃO ENCONTRADO! 🦅")
                print(f"Ticker: {ticker}")
                print(f"Queda Detectada: {abs(queda_real_percentual):.2%}")
                print(f"Preço Máximo em {PERIODO_ANALISE}: {preco_maximo:.2f} (em {data_maximo.strftime('%d/%m/%Y')})")
                print(f"Preço Atual: {preco_atual:.2f}")
                print("="*50 + "\n")
                
                # Para plotar, precisamos dos dados do ticker individual
                dados_ticker_individual = dados_completos.xs(ticker, level=1, axis=1)
                plotar_grafico(ticker, dados_ticker_individual, preco_maximo, data_maximo, preco_atual, data_atual, queda_real_percentual)
        
        except Exception as e:
            print(f"❌ Erro ao processar o ticker {ticker} do lote: {e}")


# ===================================================================
# 4. PONTO DE ENTRADA DO SCRIPT (Lógica de Download Alterada)
# ===================================================================
if __name__ == "__main__":
    print("---==[ PROJETO FALCÃO: Iniciando Scanner de Mercado (v2) ]==---")
    
    # --- Análise de Ações em Lote ---
    print("\n--- Baixando dados de TODAS as Ações de uma vez... ---")
    dados_acoes = yf.download(ACOES_PARA_MONITORAR, period=PERIODO_ANALISE, progress=False, auto_adjust=True)
    if not dados_acoes.empty:
        print("--- Processando Ações... ---")
        processar_lote_de_dados(dados_acoes)
        
    # --- Análise de Criptos em Lote ---
    print("\n--- Baixando dados de TODAS as Criptomoedas de uma vez... ---")
    dados_criptos = yf.download(CRIPTOS_PARA_MONITORAR, period=PERIODO_ANALISE, progress=False, auto_adjust=True)
    if not dados_criptos.empty:
        print("--- Processando Criptomoedas... ---")
        processar_lote_de_dados(dados_criptos)

    print("\n---==[ Scanner Finalizado ]==---")