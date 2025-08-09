import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

moedas = {
    "USD": "USDBRL=X",
    "EUR": "EURBRL=X",
    "JPY": "JPYBRL=X",
    "GBP": "GBPBRL=X",
    "CHF": "CHFBRL=X",
    "CAD": "CADBRL=X",
    "AUD": "AUDBRL=X",
}


def baixar_dados_par(ticker, start, end):
    dados = yf.download(
        ticker, start=start, end=end, interval="1mo", progress=False, auto_adjust=True
    )
    return dados


def tem_dados_na_data(dados, data):
    return any(dados.index.to_period("M") == pd.Period(data, freq="M"))


def ajustar_data_inicio(moedas_dict, start, end):
    data_inicio = pd.to_datetime(start)
    data_fim = pd.to_datetime(end)
    max_tentativas = 60  # até 5 anos

    moedas_disponiveis = moedas_dict.copy()

    for _ in range(max_tentativas):
        pares_sem_dados = []
        dados_por_moeda = {}

        for nome, ticker in list(moedas_disponiveis.items()):
            dados = baixar_dados_par(ticker, data_inicio, data_fim)
            if dados.empty or not tem_dados_na_data(dados, data_inicio):
                pares_sem_dados.append(nome)
            else:
                dados_por_moeda[nome] = dados

        if not pares_sem_dados:
            # Todos disponíveis
            return data_inicio, dados_por_moeda

        for nome in pares_sem_dados:
            moedas_disponiveis.pop(nome)

        data_inicio += pd.DateOffset(months=1)

    raise RuntimeError(
        "Não foi possível encontrar data inicial com todos os pares disponíveis."
    )


def simular_valorizacao(df_cotacoes, aporte_inicial=200):
    n_moedas = len(df_cotacoes.columns)
    aporte_por_moeda_reais = aporte_inicial / n_moedas

    cotacao_inicial = df_cotacoes.iloc[0]
    quantidade_moeda = aporte_por_moeda_reais / cotacao_inicial

    valor_reais = df_cotacoes.multiply(quantidade_moeda, axis=1)

    valor_total = valor_reais.sum(axis=1)

    return valor_total, valor_reais


def encontrar_datas_metas(
    df_valor_total, metas=[1000, 10000, 100000, 1000000, 1000000000]
):
    resultados = {}
    for meta in metas:
        alcancou = df_valor_total[df_valor_total >= meta]
        if not alcancou.empty:
            resultados[meta] = alcancou.index[0].strftime("%Y-%m")
        else:
            resultados[meta] = None
    return resultados


if __name__ == "__main__":
    start_original = "2015-08-01"
    end = "2025-05-01"
    print(
        "Procurando a primeira data onde todos os pares cambiais estão disponíveis..."
    )

    try:
        data_inicio_ajustada, dados_por_moeda = ajustar_data_inicio(
            moedas.copy(), start_original, end
        )
        print(
            f"Data inicial ajustada para: {data_inicio_ajustada.strftime('%Y-%m-%d')}"
        )
    except RuntimeError as e:
        print(str(e))
        exit(1)

    dfs = []
    print("Moedas disponíveis para concatenação:")
    for nome, df in dados_por_moeda.items():
        if df.empty or "Close" not in df.columns:
            print(f" - Ignorando {nome}: dados vazios ou sem 'Close'")
            continue
        print(f" - Incluindo {nome}, {len(df)} linhas")
        df_temp = df[["Close"]].rename(columns={"Close": nome})
        dfs.append(df_temp)

    if not dfs:
        raise RuntimeError("Nenhum dado válido para concatenação, abortando.")

    df_cotacoes = pd.concat(dfs, axis=1, join="inner")
    df_cotacoes.dropna(inplace=True)

    df_valor_total, valor_por_moeda = simular_valorizacao(
        df_cotacoes, aporte_inicial=200
    )

    metas = encontrar_datas_metas(df_valor_total)
    print(f"\nValor inicial investido: R$200")
    print("Datas estimadas para alcançar metas financeiras:")
    for meta, data in metas.items():
        if data:
            print(f"  R${meta:,.0f}: {data}")
        else:
            print(f"  R${meta:,.0f}: meta não alcançada nos dados históricos")

    if isinstance(valor_por_moeda.columns, pd.MultiIndex):
        valor_por_moeda.columns = valor_por_moeda.columns.get_level_values(0)

    fig = go.Figure()

    for moeda in valor_por_moeda.columns:
        fig.add_trace(
            go.Scatter(
                x=valor_por_moeda.index,
                y=valor_por_moeda[moeda],
                mode="lines",
                name=str(moeda),  # garante string simples
            )
        )

    fig.update_layout(
        title=f"Simulação valorização moedas fortes vs BRL (início {data_inicio_ajustada.strftime('%Y-%m')})",
        xaxis_title="Ano",
        yaxis_title="Valor acumulado (BRL)",
        legend_title="Moedas",
        template="plotly_white",
    )

    # Salvar gráfico em arquivo HTML
    fig.write_html("simulacao_moedas.html")
    print("Gráfico salvo em simulacao_moedas.html")
