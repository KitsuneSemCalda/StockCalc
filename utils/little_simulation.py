import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

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
    return yf.download(
        ticker, start=start, end=end, interval="1mo", progress=False, auto_adjust=True
    )


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
            return data_inicio, dados_por_moeda

        for nome in pares_sem_dados:
            moedas_disponiveis.pop(nome)

        data_inicio += pd.DateOffset(months=1)

    raise RuntimeError(
        "Não foi possível encontrar data inicial com todos os pares disponíveis."
    )


def simular_valorizacao(df_cotacoes, aporte_inicial=(200 * 100)):
    n_moedas = len(df_cotacoes.columns)
    aporte_por_moeda_reais = aporte_inicial / n_moedas

    cotacao_inicial = df_cotacoes.iloc[0]
    quantidade_moeda = aporte_por_moeda_reais / cotacao_inicial

    valor_reais = df_cotacoes.multiply(quantidade_moeda, axis=1)
    valor_total = valor_reais.sum(axis=1)

    return valor_total, valor_reais


def encontrar_datas_metas(df_valor_total, metas=None):
    if metas is None:
        metas = [1000, 10000, 100000, 1000000, 1000000000]

    resultados = {}
    for meta in metas:
        alcancou = df_valor_total[df_valor_total >= meta]
        resultados[meta] = (
            alcancou.index[0].strftime("%Y-%m") if not alcancou.empty else None
        )
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
        dfs.append(df[["Close"]].rename(columns={"Close": nome}))

    if not dfs:
        raise RuntimeError("Nenhum dado válido para concatenação, abortando.")

    df_cotacoes = pd.concat(dfs, axis=1, join="inner").dropna()

    df_valor_total, valor_por_moeda = simular_valorizacao(
        df_cotacoes, aporte_inicial=200
    )

    if isinstance(valor_por_moeda.columns, pd.MultiIndex):
        valor_por_moeda.columns = valor_por_moeda.columns.get_level_values(0)

    valor_por_moeda["BRL"] = 200

    cols = [col for col in valor_por_moeda.columns if col != "BRL"] + ["BRL"]
    valor_por_moeda = valor_por_moeda[cols]

    metas = encontrar_datas_metas(df_valor_total)
    print("Valor inicial investido: R$200")
    print("Datas estimadas para alcançar metas financeiras:")
    for meta, data in metas.items():
        print(
            f"  R${meta:,.0f}: {data if data else 'meta não alcançada nos dados históricos'}"
        )

    # Calcular valorização percentual (base 100 no início)
    valor_percentual = valor_por_moeda / valor_por_moeda.iloc[0] * 100

    fig_pct = go.Figure()
    for moeda in valor_percentual.columns:
        if moeda == "BRL":
            fig_pct.add_trace(
                go.Scatter(
                    x=valor_percentual.index,
                    y=valor_percentual[moeda],
                    mode="lines",
                    name="BRL (baseline)",
                    line=dict(color="black", dash="dash"),
                )
            )
        else:
            fig_pct.add_trace(
                go.Scatter(
                    x=valor_percentual.index,
                    y=valor_percentual[moeda],
                    mode="lines",
                    name=moeda,
                )
            )

    fig_pct.update_layout(
        title="Valorização percentual de moedas vs BRL",
        xaxis_title="Ano",
        yaxis_title="Valorização (%)",
        legend_title="Moedas",
        template="plotly_white",
    )

    fig_pct.write_html("simulacao_moedas_percentual.html")
    print("Gráfico percentual salvo em simulacao_moedas_percentual.html")
