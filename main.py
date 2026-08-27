from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(
    title="API Brasileirão Série B",
    description="API com dados da Série B",
    version="4.2.0"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

@app.get("/")
def inicio():
    return {
        "status": "online",
        "endpoints": ["/tabela", "/jogos", "/artilheiros"]
    }

@app.get("/tabela")
def obter_tabela():
    url = "https://site.web.api.espn.com/apis/v2/sports/soccer/bra.2/standings"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        if resposta.status_code == 403:
            url_alt = "https://cdn.espn.com/core/soccer/standings?league=bra.2&xhr=1"
            resposta = requests.get(url_alt, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()

        tabela_formatada = []
        entries = dados.get("children", [{}])[0].get("standings", {}).get("entries", [])
        if not entries and "content" in dados:
            entries = dados.get("content", {}).get("standings", {}).get("groups", [{}])[0].get("standings", {}).get("entries", [])

        for idx, entry in enumerate(entries, 1):
            team = entry.get("team", {})
            stats = {stat.get("name"): stat.get("value") for stat in entry.get("stats", [])}

            tabela_formatada.append({
                "posicao": idx,
                "time": team.get("displayName"),
                "sigla": team.get("abbreviation"),
                "escudo": team.get("logos", [{}])[0].get("href") if team.get("logos") else None,
                "pontos": int(stats.get("points", 0)),
                "jogos": int(stats.get("gamesPlayed", 0)),
                "vitorias": int(stats.get("wins", 0)),
                "empates": int(stats.get("ties", 0)),
                "derrotas": int(stats.get("losses", 0)),
                "saldo_gols": int(stats.get("pointDifferential", 0))
            })

        return {"tabela": tabela_formatada}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter tabela: {str(e)}")

@app.get("/jogos")
def obter_jogos():
    url = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/bra.2/scoreboard"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()

        jogos_formatados = []
        events = dados.get("events", [])

        for event in events:
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])

            mandante = next((c for c in competitors if c.get("homeAway") == "home"), {})
            visitante = next((c for c in competitors if c.get("homeAway") == "away"), {})

            jogos_formatados.append({
                "status": event.get("status", {}).get("type", {}).get("description"),
                "tempo_jogo": event.get("status", {}).get("displayClock"),
                "mandante": {
                    "nome": mandante.get("team", {}).get("displayName"),
                    "escudo": mandante.get("team", {}).get("logo"),
                    "placar": mandante.get("score")
                },
                "visitante": {
                    "nome": visitante.get("team", {}).get("displayName"),
                    "escudo": visitante.get("team", {}).get("logo"),
                    "placar": visitante.get("score")
                },
                "data": event.get("date"),
                "local": competition.get("venue", {}).get("fullName")
            })

        return {"rodada_atual": jogos_formatados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogos: {str(e)}")

@app.get("/artilheiros")
def obter_artilheiros():
    url = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/bra.2/scoreboard"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()

        artilheiros_dict = {}
        events = dados.get("events", [])

        for event in events:
            competition = event.get("competitions", [{}])[0]
            details = competition.get("details", []) # Detalhes de lances, gols e cartões da partida
            
            for detail in details:
                # Verifica se o lance foi um gol
                tipo_acao = detail.get("type", {}).get("text", "").lower()
                if "gol" in tipo_acao or detail.get("scoringPlay", False):
                    atleta = detail.get("athlete", {})
                    nome_jogador = atleta.get("displayName")
                    time_jogador = detail.get("team", {}).get("displayName")
                    
                    if nome_jogador:
                        if nome_jogador not in artilheiros_dict:
                            artilheiros_dict[nome_jogador] = {
                                "jogador": nome_jogador,
                                "time": time_jogador,
                                "gols": 0,
                                "foto": atleta.get("headshot")
                            }
                        artilheiros_dict[nome_jogador]["gols"] += 1

        # Transforma o dicionário em lista e ordena do que tem mais gols para o menor
        lista_artilheiros = list(artilheiros_dict.values())
        lista_artilheiros.sort(key=lambda x: x["gols"], reverse=True)

        # Adiciona a posição sequencial
        for idx, art in enumerate(lista_artilheiros, 1):
            art["posicao"] = idx

        return {"artilheiros": lista_artilheiros}
    except Exception as e:
        return {"artilheiros": [], "erro": str(e)}
