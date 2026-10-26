# ArkPedra — backend e administração

O FastAPI serve a landing page, a API de configuração e o painel do proprietário no mesmo endereço.

## Executar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-backend.txt
cp .env.example .env
uvicorn backend.main:app --reload --env-file .env
```

- Site: http://127.0.0.1:8000/
- Administração: http://127.0.0.1:8000/admin
- Documentação da API: http://127.0.0.1:8000/docs

Sem configuração, o ambiente local usa o usuário `admin` e a senha `arkpedra`, mostrando um alerta no painel. Troque ambos antes de publicar.

## Persistência

- Os preços, textos e referências de imagens ficam em `backend/data/arkpedra.db`.
- Novas imagens ficam em `uploads/`.
- Ambos são ignorados pelo Git para evitar publicar dados operacionais por engano.
- A landing mantém os valores embutidos como fallback para continuar utilizável quando aberta diretamente como arquivo.

## Variáveis opcionais

- `ARKPEDRA_DATABASE_PATH`: caminho alternativo para o banco SQLite.
- `ARKPEDRA_COOKIE_SECURE=1`: exige HTTPS para o cookie de administração (recomendado em produção).
- `ARKPEDRA_ENV=production`: desativa `/docs`, `/redoc` e `/openapi.json`, exige credenciais próprias e ativa cookies seguros por padrão.

## Catálogo administrável

O proprietário pode criar, editar, ativar, desativar e excluir pedras e opções de cubas, frontões, bordas e instalação. O sistema sempre preserva ao menos uma pedra e uma opção ativa em cada grupo.

Esta versão usa um único catálogo e uma única conta administrativa. Para vender como SaaS para várias marmorarias, a próxima etapa é separar os dados por empresa, armazenar usuários com senhas criptografadas e migrar SQLite/uploads locais para banco e armazenamento gerenciados.
