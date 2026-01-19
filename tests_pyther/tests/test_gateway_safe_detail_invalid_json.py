
import httpx
from clientes_api.app.routers.contas import _safe_detail

def _http_status_error_invalid_json(status: int, raw: bytes):
    req = httpx.Request("GET", "http://x")
    resp = httpx.Response(status, content=raw)
    return httpx.HTTPStatusError("err", request=req, response=resp)

def test_safe_detail_quando_response_json_quebra_usa_fallback():
    err = _http_status_error_invalid_json(502, b"<<<not-json>>>")
    out = _safe_detail(err)
    assert out["status"] == 502
    assert out["code"] == "ERRO_CLIENTES_DB"
    assert "Erro no serviço clientes_db" in out["message"]
