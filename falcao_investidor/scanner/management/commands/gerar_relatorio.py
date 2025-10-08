# scanner/management/commands/gerar_relatorio.py

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from scanner.models import Ativo, Setor

# --- PARÂMETROS DA ANÁLISE ---
PERIODO_ANALISE = "3mo"
PERCENTUAL_QUEDA_GATILHO = 0.15

class Command(BaseCommand):
    help = 'Executa o scanner de mercado e gera um relatório HTML estático.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('---==[ PROJETO FALCÃO: Iniciando Geração de Relatório ]==---'))

        oportunidades_encontradas = []

        # 1. Buscar todos os ativos do banco de dados
        todos_ativos = Ativo.objects.all().select_related('setor')
        tickers = [ativo.ticker for ativo in todos_ativos]
        mapa_tickers = {ativo.ticker: ativo for ativo in todos_ativos}

        if not tickers:
            self.stdout.write(self.style.WARNING('Nenhum ativo cadastrado no banco de dados.'))
            return

        # 2. Baixar todos os dados em um único lote
        self.stdout.write(f'Baixando dados para {len(tickers)} ativos...')
        dados_completos = yf.download(tickers, period=PERIODO_ANALISE, progress=False, auto_adjust=True)
        
        if dados_completos.empty:
            self.stdout.write(self.style.ERROR('Falha ao baixar dados do Yahoo Finance.'))
            return

        self.stdout.write('Processando dados e procurando oportunidades...')
        
        # 3. Processar cada ticker individualmente
        for ticker in tickers:
            try:
                # O yfinance pode retornar colunas com um ou dois níveis
                high_series = dados_completos['High'][ticker] if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos['High']
                close_series = dados_completos['Close'][ticker] if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos['Close']

                high_series = high_series.dropna()
                close_series = close_series.dropna()

                if close_series.empty: continue

                preco_maximo = high_series.max()
                data_maximo = high_series.idxmax()
                preco_atual = close_series.iloc[-1]
                data_atual = close_series.index[-1]

                # 4. Verificar o gatilho de queda
                if preco_atual <= preco_maximo * (1 - PERCENTUAL_QUEDA_GATILHO):
                    queda_percentual = (preco_atual - preco_maximo) / preco_maximo
                    ativo_obj = mapa_tickers[ticker]
                    
                    self.stdout.write(self.style.SUCCESS(f'🦅 Oportunidade encontrada em {ticker}!'))

                    # Gerar gráfico e converter para base64
                    grafico_base64 = self.gerar_grafico_base64(ticker, ativo_obj.setor.nome, dados_completos.xs(ticker, level=1, axis=1) if isinstance(dados_completos.columns, pd.MultiIndex) else dados_completos, preco_maximo, data_maximo, preco_atual, data_atual, queda_percentual)
                    
                    oportunidades_encontradas.append({
                        'ativo': ativo_obj,
                        'queda_percentual': f"{abs(queda_percentual):.2%}",
                        'preco_maximo': f"{preco_maximo:.2f}",
                        'data_maximo': data_maximo.strftime('%d/%m/%Y'),
                        'preco_atual': f"{preco_atual:.2f}",
                        'grafico_base64': grafico_base64
                    })

            except KeyError:
                self.stdout.write(self.style.WARNING(f'Dados para {ticker} não encontrados no lote baixado. Pulando.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao processar {ticker}: {e}'))

        # 5. Renderizar o template HTML com os dados
        self.stdout.write('Renderizando o arquivo HTML final...')
        context = {
            'oportunidades': oportunidades_encontradas,
            'total_analisado': len(tickers),
            'total_encontrado': len(oportunidades_encontradas),
            'PERIODO_ANALISE': PERIODO_ANALISE,
            'PERCENTUAL_QUEDA_GATILHO': PERCENTUAL_QUEDA_GATILHO,
        }
        html_content = render_to_string('scanner/relatorio_template.html', context)

        # 6. Salvar o arquivo HTML estático
        with open('relatorio_falcao.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.stdout.write(self.style.SUCCESS(f'\nRelatório "relatorio_falcao.html" gerado com sucesso! {len(oportunidades_encontradas)} oportunidades encontradas.'))

    def gerar_grafico_base64(self, ticker, setor, dados, maxima, data_maxima, atual, data_atual, queda_percentual):
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