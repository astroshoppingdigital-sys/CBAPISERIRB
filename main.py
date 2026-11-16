import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Escudos personalizados dos playoffs da Série B
ESCUDOS_PLAYOFFS = {
    "Criciúma": "https://i.postimg.cc/C54L8J4V/crr-removebg-preview-(1).png",
    "Fortaleza": "https://i.postimg.cc/C1F21Ndn/3vwixmwbhl6f1-removebg-preview.png",
    "Atlético-GO": "https://i.postimg.cc/XJJgmDr3/5b2f9501cda0080a87f039a9340f5d16.png",
    "Vila Nova": "https://i.postimg.cc/2ynT7L1s/brasao-oficial-vila-nova-futebol-clube-logo-png-seeklogo-22129.png"
}

# Fallback estruturado com os jogos de ida e volta dos Playoffs da Série B 2026
JOGOS_PLAYOFFS_FALLBACK = [
    {
        "status": "Agendado",
        "status_original": "Scheduled",
        "estado": "pre",
        "concluido": False,
        "tempo_jogo": None,
        "periodo": None,
        "mandante": {
            "nome": "Criciúma",
            "escudo": ESCUDOS_PLAYOFFS["Criciúma"],
            "placar": None
        },
        "visitante": {
            "nome": "Fortaleza",
            "escudo": ESCUDOS_PLAYOFFS["Fortaleza"],
            "placar": None
        },
        "data": "2026-11-22T19:00:00Z",  # 16h BRT
        "local": "Heriberto Hülse, Criciúma (SC)"
    },
    {
        "status": "Agendado",
        "status_original": "Scheduled",
        "estado": "pre",
        "concluido": False,
        "tempo_jogo": None,
        "periodo": None,
        "mandante": {
            "nome": "Atlético-GO",
            "escudo": ESCUDOS_PLAYOFFS["Atlético-GO"],
            "placar": None
        },
        "visitante": {
            "nome": "Vila Nova",
            "escudo": ESCUDOS_PLAYOFFS["Vila Nova"],
            "placar": None
        },
        "data": "2026-11-22T21:30:00Z",  # 18h30 BRT
        "local": "Antônio Accioly, Goiânia (GO)"
    },
    {
        "status": "Agendado",
        "status_original": "Scheduled",
        "estado": "pre",
        "concluido": False,
        "tempo_jogo": None,
        "periodo": None,
        "mandante": {
            "nome": "Vila Nova",
            "escudo": ESCUDOS_PLAYOFFS["Vila Nova"],
            "placar": None
        },
        "visitante": {
            "nome": "Atlético-GO",
            "escudo": ESCUDOS_PLAYOFFS["Atlético-GO"],
            "placar": None
        },
        "data": "2026-11-27T23:00:00Z",  # 20h BRT
        "local": "Onésio Brasileiro Alvarenga, Goiânia (GO)"
    },
    {
        "status": "Agendado",
        "status_original": "Scheduled",
        "estado": "pre",
        "concluido": False,
        "tempo_jogo": None,
        "periodo": None,
        "mandante": {
            "nome": "Fortaleza",
            "escudo": ESCUDOS_PLAYOFFS["Fortaleza"],
            "placar": None
        },
        "visitante": {
            "nome": "Criciúma",
            "escudo": ESCUDOS_PLAYOFFS["Criciúma"],
            "placar": None
        },
        "data": "2026-11-28T23:00:00Z",  # 20h BRT
        "local": "Arena Castelão, Fortaleza (CE)"
    }
]

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

            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {})

            state = status_type.get("state")  # "pre", "in", "post"
            completed = status_type.get("completed", False)
            description = status_type.get("description", "")

            if state == "post" or completed:
                status_real = "Encerrado"
            elif state == "in":
                status_real = "Ao Vivo"
            elif state == "pre":
                status_real = "Agendado"
            else:
                status_real = description or "Aguardando"

            nome_mandante = mandante.get("team", {}).get("displayName")
            nome_visitante = visitante.get("team", {}).get("displayName")

            # Substitui pelo escudo personalizado se for um dos times dos playoffs
            logo_mandante = ESCUDOS_PLAYOFFS.get(nome_mandante, mandante.get("team", {}).get("logo"))
            logo_visitante = ESCUDOS_PLAYOFFS.get(nome_visitante, visitante.get("team", {}).get("logo"))

            jogos_formatados.append({
                "status": status_real,
                "status_original": description,
                "estado": state,
                "concluido": completed,
                "tempo_jogo": status_obj.get("displayClock"),
                "periodo": status_obj.get("period"),
                "mandante": {
                    "nome": nome_mandante,
                    "escudo": logo_mandante,
                    "placar": mandante.get("score")
                },
                "visitante": {
                    "nome": nome_visitante,
                    "escudo": logo_visitante,
                    "placar": visitante.get("score")
                },
                "data": event.get("date"),
                "local": competition.get("venue", {}).get("fullName")
            })

        # Se a ESPN estiver vazia (fim de campeonato), usa o fallback dos playoffs garantido
        if not jogos_formatados:
            return {"rodada_atual": JOGOS_PLAYOFFS_FALLBACK}

        return {"rodada_atual": jogos_formatados}

    except Exception as e:
        # Em caso de falha na requisição externa, entrega o fallback para o painel não quebrar
        return {"rodada_atual": JOGOS_PLAYOFFS_FALLBACK}
