from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(
    title="API Brasileirão Série B",
    description="API com tabela de classificação e jogos em tempo real",
    version="2.0.0"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Endpoint público direto de dados de futebol da Globo
URL_GE_FUTEBOL = "https://ge.globo.com/futebol/brasileirao-serie-b/"

@app.get("/")
def inicio():
    return {
        "status": "online",
        "endpoints": ["/tabela", "/jogos"]
    }

@app.get("/tabela")
def obter_tabela():
    # Faz chamada para a API dinâmica de classificação do GE
    url_api = "https://api.globoesporte.globo.com/tabela/fase/fase-unica-serie-b/classificacao"
    try:
        res = requests.get(url_api, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            # Fallback direto caso a estrutura exija o parâmetro da edição atual
            res = requests.get("https://a.ge.globo.com/futebol/brasileirao-serie-b/classificacao.json", headers=HEADERS, timeout=15)
            
        res.raise_for_status()
        dados = res.json()

        tabela_formatada = []
        # Normaliza o formato recebido
        lista_classificacao = dados if isinstance(dados, list) else dados.get("classificacao", [])
        
        for item in lista_classificacao:
            equipe = item.get("equipe", {})
            pontos = item.get("pontos", {})
            tabela_formatada.append({
                "posicao": item.get("posicao"),
                "time": equipe.get("nome_popular"),
                "sigla": equipe.get("sigla"),
                "escudo": equipe.get("escudo"),
                "pontos": pontos.get("pontos"),
                "jogos": pontos.get("jogos"),
                "vitorias": pontos.get("vitorias"),
                "empates": pontos.get("empates"),
                "derrotas": pontos.get("derrotas"),
                "saldo_gols": pontos.get("saldo_gols")
            })

        return {"tabela": tabela_formatada}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter tabela: {str(e)}")

@app.get("/jogos")
def obter_jogos():
    url_api = "https://api.globoesporte.globo.com/tabela/fase/fase-unica-serie-b/jogos"
    try:
        res = requests.get(url_api, headers=HEADERS, timeout=15)
        res.raise_for_status()
        dados = res.json()

        jogos_formatados = []
        lista_jogos = dados if isinstance(dados, list) else dados.get("jogos", [])

        for jogo in lista_jogos:
            mandante = jogo.get("equipes", {}).get("mandante", {})
            visitante = jogo.get("equipes", {}).get("visitante", {})
            placar = jogo.get("placar", {})

            jogos_formatados.append({
                "status": jogo.get("status"),
                "tempo_jogo": jogo.get("periodo"),
                "mandante": {
                    "nome": mandante.get("nome_popular"),
                    "escudo": mandante.get("escudo"),
                    "placar": placar.get("mandante")
                },
                "visitante": {
                    "nome": visitante.get("nome_popular"),
                    "escudo": visitante.get("escudo"),
                    "placar": placar.get("visitante")
                },
                "data": jogo.get("data_realizacao"),
                "local": jogo.get("estadio", {}).get("nome_popular")
            })

        return {"rodada_atual": jogos_formatados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogos: {str(e)}")
