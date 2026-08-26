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

# URL oficial com os dados da tabela da Série B no Globo Esporte
URL_GE_TABELA = "https://api.globoesporte.globo.com/tabela/d1a66e5d-114d-4e90-a931-158913988636/fase/fase-unica-serie-b-2024/classificacao/"

@app.get("/")
def inicio():
    return {
        "status": "online",
        "endpoints": ["/tabela", "/jogos"]
    }

@app.get("/tabela")
def obter_tabela():
    try:
        resposta = requests.get(URL_GE_TABELA, headers=HEADERS, timeout=15)
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
        raise HTTPException(status_code=500, detail=f"Erro ao obter tabela: {str(e)}")

@app.get("/jogos")
def obter_jogos():
    try:
        # Busca a rodada atual a partir dos dados da tabela
        resposta = requests.get(URL_GE_TABELA, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        dados_json = resposta.json()
        
        # Pega os jogos da rodada
        jogos_formatados = []
        if dados_json and len(dados_json) > 0:
            rodada_jogos = dados_json[0].get("jogos", [])
            for jogo in rodada_jogos:
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
