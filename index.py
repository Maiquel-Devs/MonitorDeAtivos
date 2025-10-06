import yfinance as yf

def buscar_precos_atuais():
    """
    Busca o preço de mercado atual para uma lista de tickers.
    """
    # Tickers para Petrobras (PN) e Banco do Brasil (ON)
    tickers_para_buscar = ['PETR4.SA', 'BBAS3.SA']
    
    print("\n--- Buscando Preços Atuais (B3) ---")

    for ticker_str in tickers_para_buscar:
        try:
            # Cria o objeto Ticker para o ativo específico
            ativo = yf.Ticker(ticker_str)
            
            # O dicionário .info contém os dados mais recentes da ação
            # 'regularMarketPrice' é a chave para o preço atual durante o pregão
            info = ativo.info
            
            nome_empresa = info.get('shortName', ticker_str)
            preco_atual = info.get('regularMarketPrice')

            if preco_atual:
                print(f"✅ {nome_empresa}: R$ {preco_atual:.2f}")
            else:
                # Se o mercado estivesse fechado, poderíamos usar o preço de fechamento anterior
                preco_fechamento = info.get('previousClose')
                if preco_fechamento:
                    print(f"ℹ️ {nome_empresa}: R$ {preco_fechamento:.2f} (Fechamento anterior)")
                else:
                    print(f"⚠️ Preço não encontrado para {nome_empresa}")

        except Exception as e:
            print(f"❌ Erro ao buscar dados para {ticker_str}: {e}")

# Ponto de entrada do script
if __name__ == "__main__":
    buscar_precos_atuais()