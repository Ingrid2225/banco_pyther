PYTHER – SISTEMA DE BANCO COM MICROSERVIÇOS

Projeto em Python usando FastAPI com arquitetura de microserviços, simulando um sistema bancário de contas.  

O sistema é dividido em dois serviços que se comunicam via HTTP usando httpx:

clientes_db→ serviço interno responsável por persistência e regras de negócio.  
clientes_api→ gateway público que expõe a API, calcula score e encaminha operações.  


☑️ VISÃO GERAL

O sistema permite:

- Criar contas bancárias  
- Listar contas  
- Buscar conta por agência e número  
- Atualizar dados  
- Depositar  
- Sacar  
- Utilizar cheque especial  
- Calcular score de crédito  
- Desativar contas  

O clientes_api funciona como porta de entrada, enquanto o clientes_db cuida do SQLite e das regras de negócio.



☑️ ARQUITETURA

Cliente (HTTP)
   |
   v
clientes_api (Gateway / Público)
   |
   | HTTP (httpx)
   v
clientes_db (Interno / SQLite)



☑️ RESPONSABILIDADES
 
🔹 CLIENTES_API

• Validação de entrada

• Tratamento de erros do serviço interno

• Cálculo de score de crédito

• Encaminhamento das operações

🔹 CLIENTES_DB

• Persistência em SQLite

• Controle de saldo

• Regras de negócio

• Cheque especial

• Unicidade por CPF e (agência + conta)



☑️ TECNOLOGIAS

• Python 3.10+

• FastAPI

• SQLAlchemy

• SQLite

• httpx

• Pytest

• Pydantic



☑️ ESTRUTURA DE PASTAS
.
├── clientes_api/
│   └── app/
│       ├── main.py
│       ├── routers/
│       │   └── contas.py
│       └── services/
│           ├── db_conta.py
│           ├── models.py
│           └── schemas.py
│
├── clientes_db/
│   └── app/
│       ├── main.py
│       ├── db.py
│       ├── models.py
│       ├── schemas.py
│       └── routers/
│           └── contas.py
│
├── tests/
│   ├── conftest.py
│   ├── test_clientes_api.py
│   ├── test_clientes_db.py
│   └── demais testes...
│
├── requirements.txt
└── README.md



☑️ INSTALAÇÃO

python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt



☑️ COMO RODAR OS SERVIÇOS
Você precisa subir os dois serviços.



☑️ SUBIR CLIENTES_DB

python -m uvicorn clientes_db.app.main:app --reload --host 0.0.0.0 --port 8001



☑️ SUBIR CLIENTES_API

python -m uvicorn clientes_api.app.main:app --reload --host 0.0.0.0 --port 8000



☑️ URLs
Serviço	URL

clientes_api	http://localhost:8000

clientes_db	http://localhost:8001



☑️ SWAGGER

Após subir os serviços:

clientes_api → http://localhost:8000/docs

clientes_db → http://localhost:8001/docs



☑️ VARIÁVEL DE AMBIENTE

O gateway usa a variável:
CLIENTES_DB_URL=http://localhost:8001

Se não existir, o padrão é:

http://localhost:8001



☑️ COMO RODAR OS TESTES

Na raiz do projeto:
coverage run -m pytest -c tests_pyther/pytest.ini -q



☑️ EXEMPLOS DE USO

  1. CRIAR A CONTA
  
  POST /contas
  {
    "agencia": "1234",
    "numero_conta": "5678",
    "nome": "Maria",
    "cpf": "12345678901",
    "telefone": 11999999999,
    "email": "maria@email.com",
    "saldo_cc": 100
  }
  ✔ Cria a conta
  ✔ Garante unicidade de CPF e conta
  
  2. LISTAR TODAS AS CONTAS
  
  O gerente deseja visualizar todas as contas cadastradas
  GET /contas
  Resposta:
  
  {
      "agencia": "0001",
      "numero_conta": "12345",
      "nome": "João Silva",
      "saldo_cc": 200
    }
  
  ✔ Retorna todas as contas ativas
  
  3. BUSCAR UMA CONTA ESPECÍFICA
  
  Consultar uma conta por agência e número.
  
  GET /contas/{agencia}/{numero_conta}
  
  Exemplo:
  GET /contas/0001/12345
  ✔ Retorna os dados da conta
  ✔ Não expõe ID interno
  
  4. ATUALIZAR DADOS DA CONTA
  
  O cliente atualiza seus dados cadastrais.
  
  PUT /contas/{agencia}/{numero_conta}
  {
    "nome": "João da Silva",
    "email": "joao.silva@email.com"
  }
  
  ✔ Atualiza dados permitidos
  ✔ Mantém regras de integridade
  
  5. DEPOSITAR
  
  POST /contas/operacoes/depositar
  {
    "agencia": "1234",
    "numero_conta": "5678",
    "saldo": 50
  }
  ✔ Soma o valor ao saldo atual
  
  6. SACAR
  Retirar dinheiro da conta.
  
  POST /contas/operacoes/sacar
  {
    "agencia": "1234",
    "numero_conta": "5678",
    "saldo": 20
  }
  ✔ Valida saldo + cheque especial
  ✔ Impede saque indevido
  
  7. CADASTRAR/AJUSTAR CHEQUE ESPECIAL 
  
  Habilitar ou ajustar limite de cheque especial.
  
  PUT /contas/{agencia}/{numero_conta}/cheque_especial/cadastrar
  {
    "limite": 500,
    "habilitado": true
  }
  
  ✔ Define limite
  ✔ Permite uso quando saldo fica negativo
  
  8. SCORE DE CRÉDITO
  O banco calcula o score do cliente.
  
  GET /contas/{agencia}/{numero_conta}/score_credito
  {
    "agencia": "1234",
    "numero_conta": "5678",
    "score_credito": 10.0
  }
  ✔ Score = 10% do saldo
  ✔ Arredondado corretamente
  
  9. DESATIVAR CONTA
  Encerrar uma conta bancária.
  
  DELETE /contas/{agencia}/{numero_conta}/desativar
  {
    "agencia": "1234",
    "numero_conta": "5678",
  }
  
  ✔ Só permite se saldo for zero
  ✔ Protege contra exclusão indevida

  

☑️ REGRAS DE NEGÓCIO

✔ CPF é único

✔ Agência + número são únicos

✔ Não pode sacar sem saldo ou limite

✔ Cheque especial não pode ser desativado com saldo negativo

✔ Conta só é desativada com saldo zerado

✔ Score = 10% do saldo


✅ PROJETO FINALIZADO PARA FINS DE TRABALHO E DEMONSTRAÇÃO DE MICROSERVIÇOS COM FastAPI.











