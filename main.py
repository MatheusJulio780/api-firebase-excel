import os
import json
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
import firebase_admin
from firebase_admin import credentials, firestore

# Configuração da Chave de Acesso da API (Security Token)
API_KEY_NAME = "X-API-KEY"
API_KEY_VALUE = os.environ.get("EXCEL_API_KEY", "MinhaChaveSegura2026")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def validar_token(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY_VALUE:
        raise HTTPException(status_code=403, detail="Acesso negado: Token inválido")
    return api_key

# Inicializa o SDK do Firebase usando a chave JSON local ou variável de ambiente
if not firebase_admin._apps:
    firebase_cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if firebase_cred_json:
        cred_dict = json.loads(firebase_cred_json)
        cred = credentials.Certificate(cred_dict)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
    else:
        raise RuntimeError("Arquivo de credenciais do Firebase não encontrado.")
    
    firebase_admin.initialize_app(cred)

db = firestore.client()
app = FastAPI(title="API Firebase para Excel - Monitoramento")

@app.get("/api/v1/notas", dependencies=[Depends(validar_token)])
def get_notas_fiscais():
    try:
        docs = db.collection("notas_fiscais_diario").stream()
        lista_notas = []

        for doc in docs:
            data_operacao = doc.id
            dados = doc.to_dict() or {}
            notas = dados.get("notas", [])

            for nota in notas:
                peso_raw = str(nota.get("peso", 0)).replace(".", "").replace(",", ".") if isinstance(nota.get("peso"), str) else nota.get("peso", 0)
                try:
                    peso_val = float(peso_raw)
                except ValueError:
                    peso_val = 0.0

                lista_notas.append({
                    "data_operacao": data_operacao,
                    "nf": str(nota.get("nf", "")),
                    "placa": str(nota.get("placa", "")),
                    "tipo_viagem": str(nota.get("tipo_viagem", "")),
                    "motorista": str(nota.get("motorista", "")),
                    "telefone": str(nota.get("telefone", "")),
                    "peso": peso_val,
                    "qtde": int(str(nota.get("qtde", 0)).replace(".", "") or 0),
                    "viagem": str(nota.get("viagem", ""))
                })

        return lista_notas

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/painel", dependencies=[Depends(validar_token)])
def get_painel_rotas():
    try:
        docs = db.collection("painel_diario").stream()
        lista_rotas = []

        for doc in docs:
            data_operacao = doc.id
            dados = doc.to_dict() or {}
            rotas = dados.get("rotas", [])

            for r in rotas:
                lista_rotas.append({
                    "data_operacao": data_operacao,
                    "placa": str(r.get("placa", "")),
                    "troca": str(r.get("troca", "")),
                    "status": str(r.get("status", "")),
                    "motorista": str(r.get("motorista", "")),
                    "contato": str(r.get("contato", "")),
                    "transporte": str(r.get("transporte", ""))
                })

        return lista_rotas

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))