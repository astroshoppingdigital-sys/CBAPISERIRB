from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(
    title="API Brasileirão Série B",
    description="API com tabela de classificação e jogos em tempo real extraídos do GE",
    version="2.0.0"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# IDs oficiais do Globo Esporte para a Série B do Brasileirão
ID_CAMPEONATO = "41"      # Campeonato Brasileiro Série B
ID_EDICAO = "1023"        # Edição atual / vigente

@app.get("/")
def inicio():
    return {
        "status": "online",
        "endpoints": ["/tabela", "/jogos"]
    }

@app.get("/tabela")
def obter_tabela():
    # Endpoint oficial do GE para tabela de classificação
    url = f"https://api.ge.globo.com/tabela/v1/campeonatos/{ID_CAMPEONATO}/edicoes/{ID_EDICAO}/classificacao"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        
        # Fallback caso precise consultar via endpoint de contingência
        if resposta.status_code != 200:
            url_alt = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/default.png" # Exemplo de verificação
            resposta = requests.get("https://ge.globo.com/futebol/brasileirao-serie-b/", headers=HEADERS, timeout=15)
            
        resposta.raise_for_status()
        dados_json = resposta.json()
        
        tabela_formatada = []
        for item in dados_json:
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
        # Tenta rota resiliente de contingência em JSON do GE se a API principal falhar
        try:
            res_ge = requests.get("https://api.ge.globo.com/tabela/v1/campeonatos/41/edicoes/1023/classificacao", headers=HEADERS)
            if res_ge.status_code == 200:
                return {"tabela": res_ge.json()}
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Erro ao obter tabela: {str(e)}")

@app.get("/jogos")
def obter_jogos():
    # Endpoint oficial de jogos da rodada atual do GE
    url = f"https://api.ge.globo.com/tabela/v1/campeonatos/{ID_CAMPEONATO}/edicoes/{ID_EDICAO}/jogos"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        lista_jogos = resposta.json()

        jogos_formatados = []
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
