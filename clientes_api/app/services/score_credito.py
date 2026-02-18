def calcular_score_credito(conta: dict) -> int:
    score = 500
    saldo = float(conta.get("saldo_cc", 0.0))

    if saldo > 5000:
        score += 200
    elif saldo > 1000:
        score += 100
    elif saldo < 0:
        score -= 150

    if conta.get("cheque_especial_contratado"):
        if saldo < 0:
            score -= 100
        else:
            score -= 50

    perfil = conta.get("perfil_investidor", "MODERADO")
    if perfil == "ARROJADO":
        score += 50
    elif perfil == "CONSERVADOR":
        score -= 20

    if conta.get("investimentos"):
        score += 50

    return max(0, min(score, 1000))
