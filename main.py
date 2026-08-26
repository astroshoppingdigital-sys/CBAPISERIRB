from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(
    title="API Brasileirão Série B",
    description="API de classificação e jogos via ESPN",
    version="3.0.0"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Endpoint público e gratuito da ESPN para a Série B do Brasil
URL_ESPN_TABELA = "https://site.api.espn.com/apis/v2/sports/soccer/bra.2/standings"
URL_ESPN_JOGOS = "https://site.api.espn.com/apis/site/v2/sports/soccer/bra.2/scoreboard"

@app.get("/")
def inicio():
    return {
        "status": "online",
        "provedor": "ESPN",
        "endpoints": ["/tabela", "/jogos"]
    }

@app.get("/tabela")
def obter_tabela():
    try:
        resposta = requests.get(URL_ESPN_TABELA, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()

        tabela_formatada = []
        entries = dados.get("children", [{}])[0].get("standings", {}).get("entries", [])

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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar tabela da ESPN: {str(e)}")

@app.get("/jogos")
def obter_jogos():
    try:
        resposta = requests.get(URL_ESPN_JOGOS, headers=HEADERS, timeout=15)
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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar jogos da ESPN: {str(e)}")
