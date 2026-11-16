import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Libera o acesso para o seu painel no Google AI Studio ou qualquer domínio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Escudos personalizados atualizados (incluindo variações de nome da ESPN)
ESCUDOS_PLAYOFFS = {
    "Criciúma": "https://i.postimg.cc/X7SV8rHH/images.png",
    "Fortaleza": "https://i.postimg.cc/C1F21Ndn/3vwixmwbhl6f1-removebg-preview.png",
    "Atlético-GO": "https://i.postimg.cc/d0SH9TBN/escudo-fundo-vermelho-(1).png",
    "Atlético Goianiense": "https://i.postimg.cc/d0SH9TBN/escudo-fundo-vermelho-(1).png",
    "Vila Nova": "https://i.postimg.cc/2Sr4L84j/db07ea497d7012235c90871e9450759e.png"
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
        "data": "2026-11-22T19:00:00Z",  # 16h00 BRT
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
        "data": "2026-11-27T23:00:00Z",  # 20h00 BRT
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
        "data": "2026-11-28T23:00:00Z",  # 20h00 BRT
        "local": "Arena Castelão, Fortaleza (CE)"
    }
]

def normalizar_nome(nome: str) -> str:
    if nome == "Atlético Goianiense":
        return "Atlético-GO"
    return nome

@app.get("/jogos")
def obter_jogos():
    url = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/bra.2/scoreboard"
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        dados = resposta.json()

        jogos_espn = []
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

            nome_mandante = normalizar_nome(mandante.get("team", {}).get("displayName", ""))
            nome_visitante = normalizar_nome(visitante.get("team", {}).get("displayName", ""))

            logo_mandante = ESCUDOS_PLAYOFFS.get(nome_mandante, mandante.get("team", {}).get("logo"))
            logo_visitante = ESCUDOS_PLAYOFFS.get(nome_visitante, visitante.get("team", {}).get("logo"))

            jogos_espn.append({
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

        # Verifica se a ESPN já está mostrando os jogos futuros/ao vivo dos playoffs (após 18/11/2026)
        jogos_playoffs_ao_vivo_ou_novos = [
            j for j in jogos_espn if j.get("data", "") >= "2026-11-18"
        ]

        if jogos_playoffs_ao_vivo_ou_novos:
            confrontos_espn = {
                (j["mandante"]["nome"], j["visitante"]["nome"])
                for j in jogos_playoffs_ao_vivo_ou_novos
            }
            jogos_restantes = [
                fb for fb in JOGOS_PLAYOFFS_FALLBACK
                if (fb["mandante"]["nome"], fb["visitante"]["nome"]) not in confrontos_espn
            ]
            historico_anterior = [j for j in jogos_espn if j.get("data", "") < "2026-11-18"]
            return {"rodada_atual": historico_anterior + jogos_playoffs_ao_vivo_ou_novos + jogos_restantes}

        # Enquanto a ESPN só tiver a 38ª rodada encerrada, entrega o histórico + os 4 jogos agendados dos playoffs
        return {"rodada_atual": jogos_espn + JOGOS_PLAYOFFS_FALLBACK}

    except Exception:
        return {"rodada_atual": JOGOS_PLAYOFFS_FALLBACK}
