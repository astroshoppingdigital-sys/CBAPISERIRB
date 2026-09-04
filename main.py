
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

            # Tratativa blindada de estado para evitar encerramento falso
            state = status_type.get("state") # "pre", "in", "post"
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

            jogos_formatados.append({
                "status": status_real,
                "status_original": description,
                "estado": state,          # "pre", "in", "post"
                "concluido": completed,   # True se acabou de fato, False caso contrário
                "tempo_jogo": status_obj.get("displayClock"),
                "periodo": status_obj.get("period"),         # 1 para 1º tempo, 2 para 2º tempo, etc.
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
