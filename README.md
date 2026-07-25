# YkMedia

Central de recebimento de arquivos para sonoplastia usando WhatsApp e Evolution API.

## Primeira etapa

Esta versão contém:

- API FastAPI;
- rota de saúde;
- webhook da Evolution API;
- identificação de `messages.upsert`;
- classificação inicial do tipo da mensagem;
- bloqueio de mensagens enviadas pelo próprio número;
- testes automatizados.

Ainda não contém download de mídia nem respostas automáticas.

## Instalação no Windows PowerShell

```powershell
cd ykmedia
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Abra:

- API: http://127.0.0.1:8000
- Documentação: http://127.0.0.1:8000/docs
- Saúde: http://127.0.0.1:8000/health

## Testes

```powershell
pytest -q
```

## Webhook

Configure a Evolution API para enviar eventos ao endpoint:

```text
http://SEU-IP:8000/webhooks/evolution
```

Durante desenvolvimento local fora da mesma rede, será necessário um túnel HTTPS.
