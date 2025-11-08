# 🧠 English Vocabulary Generator & Anki Sync

Um sistema automatizado para **gerar vocabulário com IA** e **enviar para o Anki**.  
O projeto utiliza múltiplas APIs (Groq, Gemini e OpenRouter) para criar definições, pronúncias e exemplos de palavras em inglês, salvando tudo em Markdown e integrando com o Anki via **AnkiConnect**.

---

## 📂 Estrutura do Projeto

```

├── vocabGenarator.py         # Script que gera o vocabulário automaticamente via múltiplos provedores
├── english_vocab_model.md    # Arquivo gerado como modelo final com todas as palavras e exemplos
├── sendToAnki.py             # Script que envia o conteúdo para o Anki (com verificação de duplicatas)
└── .progress.json            # Armazena o progresso do último processamento

````

---

## ⚙️ Gerar vocabulário (`vocabGenarator.py`)

O script lê arquivos Markdown com listas de palavras (por exemplo: `send1.md`, `send2.md`) e cria um arquivo de saída no formato `english_vocab_model.md`, contendo as definições completas.

### ✨ Recursos
- Suporte a múltiplos provedores de IA (**Groq**, **Gemini**, **OpenRouter**)
- Alternância automática em caso de erro ou limite de requisição
- Armazena progresso para retomada automática
- Gera saída em formato Markdown organizada e limpa

### 🔧 Configuração
Edite a classe `Config` no início do arquivo para ajustar:
```python
input_pattern = "send*.md"     # Padrão dos arquivos de entrada
output_file = "english_vocab_model.md"
````

### ▶️ Execução

```bash
python vocabGenarator.py
```

O resultado será salvo em `english_vocab_model.md`.

---

## 🧩 Estrutura do arquivo `english_vocab_model.md`

O arquivo gerado segue sempre o mesmo formato:

```markdown
## Word
**Signification**: Definition of the word.
**Prononciation**: /IPA/
**Exemple**:
- Example sentence using the word.

---
```

Esse formato é compatível com o script `sendToAnki.py`, que faz a leitura automática dos campos para importar no Anki.

---

## 🪶 Enviar para o Anki (`sendToAnki.py`)

O script lê o arquivo `english_vocab_model.md` (ou outro especificado) e envia cada entrada como um card para o Anki via API **AnkiConnect**.

### ⚙️ Requisitos

* Anki instalado
* Plugin **AnkiConnect** ativo (porta padrão `8765`)

### 🔧 Configuração

Edite as variáveis no início do arquivo:

```python
ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = "Francês"           # Nome do baralho
MODEL_NAME = "Cards"            # Nome do modelo
FILE_NAME = "english_vocab_model.md"
```

### ▶️ Execução

```bash
python sendToAnki.py
```

O script vai:

* Ler o arquivo Markdown
* Extrair os campos (palavra, significado, pronúncia, exemplo)
* Verificar duplicatas antes de adicionar
* Criar automaticamente as notas no Anki

---

## 📦 Dependências

Instale as dependências necessárias:

```bash
pip install requests
```

---

## 🧰 Requisitos mínimos

* Python 3.8+
* Conexão com as APIs Groq, Gemini e OpenRouter
* Anki + AnkiConnect em execução

---

## 🧾 Licença

Projeto de uso pessoal e educacional.
Sinta-se à vontade para modificar, estudar e adaptar.

---

## ✨ Autor

Desenvolvido por **Miguel Rafael**
[github.com/oMiguelwnl](https://github.com/oMiguelwnl)

```
