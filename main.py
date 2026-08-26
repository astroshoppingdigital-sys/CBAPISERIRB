from fastapi import FastAPI, HTTPException
import requests
import json
from bs4 import BeautifulSoup

app = FastAPI(
    title="API Brasileirão Série B",
    description="API com tabela de classificação e jogos em tempo real extraídos do GE",
    version="2.0.0"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@app.get("/")
def inicio():
    return {
        "status": "online",
        "endpoints": ["/tabela", "/jogos"]
    }

@app.get("/tabela")
def obter_tabela():
    url = "https://ge.globo.com/futebol/brasileirao-serie-b/"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")
        
        script_dados = soup.find("script", id="flux-dados-classificacao")
        if not script_dados or not script_dados.string:
            raise HTTPException(status_code=404, detail="Dados da tabela não encontrados")

        dados_json = json.loads(script_dados.string)
        tabela_formatada = []

        for item in dados_json.get("classificacao", []):
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jogos")
def obter_jogos():
    url = "https://ge.globo.com/futebol/brasileirao-serie-b/"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")
        
        # O GE injeta os dados de jogos ao vivo e da rodada nesse script
        script_jogos = soup.find("script", id="flux-dados-jogos")
        
        if not script_jogos or not script_jogos.string:
            # Fallback para busca de script alternativo de jogos do GE
            script_jogos = soup.find("script", id="script-jogos")
            if not script_jogos or not script_jogos.string:
                raise HTTPException(status_code=404, detail="Dados de jogos não encontrados no HTML")

        dados_json = json.loads(script_jogos.string)
        jogos_formatados = []

        lista_jogos = dados_json.get("jogos", [])
        for jogo in lista_jogos:
            mandante = jogo.get("equipes", {}).get("mandante", {})
            visitante = jogo.get("equipes", {}).get("visitante", {})
            placar = jogo.get("placar", {})
            
            jogos_formatados.append({
                "status": jogo.get("status"),  # Ex: "EM_ANDAMENTO", "ENCERRADO", "AGENDA"
                "tempo_jogo": jogo.get("periodo"), # Ex: "1º Tempo 35'"
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
                "gols": jogo.get("gols", []), # Lista com autores e minutos dos gols
                "data": jogo.get("data_realizacao"),
                "local": jogo.get("estadio", {}).get("nome_popular")
            })

        return {"rodada_atual": jogos_formatados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogos: {str(e)}")