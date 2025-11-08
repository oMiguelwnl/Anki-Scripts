import re
import requests

# === CONFIGURAÇÕES ===
ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = "Francês"           # Nome do baralho no Anki
MODEL_NAME = "Cards"      # Nome do modelo com os fields
FILE_NAME = "Parte 3.md"        # Nome do arquivo no Obsidian

# === FUNÇÃO PARA ADICIONAR NOTA (com verificação de duplicata) ===
def add_note(palavra, significado, ipa, exemplo):
    # Verifica se já existe uma nota com a mesma palavra neste baralho
    query = {
        "action": "findNotes",
        "version": 6,
        "params": {"query": f'"Palavra:{palavra}" deck:"{DECK_NAME}"'}
    }
    try:
        res = requests.post(ANKI_CONNECT_URL, json=query).json()
        if res.get("result"):
            print(f"⚠️ '{palavra}' já existe no baralho, ignorando.")
            return
    except Exception as e:
        print(f"Erro ao consultar duplicata para '{palavra}':", e)
        return

    # Se não existir, cria a nota normalmente
    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": DECK_NAME,
                "modelName": MODEL_NAME,
                "fields": {
                    "Palavra": palavra,
                    "Significado": significado,
                    "IPA": ipa,
                    "Exemplo": exemplo
                },
                "options": {"allowDuplicate": False},
                "tags": ["obsidian"]
            }
        }
    }
    try:
        r = requests.post(ANKI_CONNECT_URL, json=payload)
        result = r.json()
        if result.get("error"):
            print(f"❌ Erro ao adicionar '{palavra}': {result['error']}")
        else:
            print(f"✅ '{palavra}' adicionada com exemplo: {exemplo[:60]}...")
    except Exception as e:
        print("Erro ao conectar ao AnkiConnect:", e)


# === LER O ARQUIVO ===
try:
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        text = f.read()
except FileNotFoundError:
    print(f"Arquivo '{FILE_NAME}' não encontrado.")
    exit()

# === DIVIDIR O ARQUIVO EM BLOCOS ===
entries = re.split(r"(?m)^## ", text)
entries = [e.strip() for e in entries if e.strip()]

# === PROCESSAR CADA BLOCO ===
for entry in entries:
    first_line = entry.split("\n", 1)[0].strip()
    palavra = first_line

    significado = ""
    ipa = ""
    exemplo = ""

    # Extrai Signification
    sig_match = re.search(r"\*\*Signification\*\*\s*:\s*(.+?)(?:\n|$)", entry, re.DOTALL)
    if sig_match:
        significado = sig_match.group(1).strip()

    # Extrai Prononciation
    ipa_match = re.search(r"\*\*Prononciation\*\*\s*:\s*(.+?)(?:\n|$)", entry, re.DOTALL)
    if ipa_match:
        ipa = ipa_match.group(1).strip()

    # Extrai Exemple (singular)
    ex_match = re.search(r"\*\*Exemple\*\*\s*:\s*(?:- )?(.+?)(?:\n|$)", entry, re.DOTALL)
    if ex_match:
        exemplo = ex_match.group(1).strip()

    # Adiciona nota apenas se houver palavra e significado
    if palavra and significado:
        add_note(palavra, significado, ipa, exemplo)
    else:
        print(f"⚠️ Campos faltando em: {palavra}")
