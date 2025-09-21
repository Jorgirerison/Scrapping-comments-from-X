# Analisar de Sentimentos

## Sobre o Projeto

Este projeto é um script de automação e web scraping em Python que coleta e analisa sentimentos de comentários em posts de um perfil específico no X (antigo Twitter).

O script:

1. Navega até um perfil do X.
2. Coleta os posts mais recentes.
3. Extrai os comentários de cada post.
4. Limpa os textos (remoção de links, menções e hashtags).
5. Realiza uma análise de sentimento (positivo, negativo ou neutro) utilizando a biblioteca LeIA.
6. Gera:
   - Um arquivo CSV com os dados brutos e processados.
   - Um gráfico em PNG com a distribuição de sentimentos.

### 1. Clone o Repositório

```bash
git clone git@github.com:Jorgirerison/Scrapping-comments-from-X.git
cd <NOME_DO_DIRETORIO_CLONADO>
```

### 2. Crie e ative o ambiente virtual

- no Windows:

```bash
python -m venv venv
.\venv\Scripts\activate
```

- no Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

- no Windows:

```bash
$env:USERNAME_TWITTER="seu_usuario_aqui"
$env:PASSWORD_TWITTER="sua_senha_aqui"
```

- no Linux:

```bash
export USERNAME_TWITTER="seu_usuario_aqui"
export PASSWORD_TWITTER="sua_senha_aqui"
```

Substitua pelas suas credenciais reais

### 5. Execute o script
```bash
python main.py
```

#### Alguns parametros essenciais do usuário
```python
USERNAME_EXTRA = "jorgirerison"  # Nome de usuário do twitter para possíveis bloqueios
NOME_DO_PORTAL = "PortalHOTD"    # Perfil alvo do X (sem o @)
META_DE_POSTS = 30               # Quantidade de posts a coletar
LIMITE_DE_COMENTARIOS_POR_POST = None  # Limite de comentários (ou None para todos)
```

#### Saída do projeto
Após a execução, os seguintes arquivos serão gerados:

- <NOME_DO_PORTAL>_posts_comentarios.csv: Dados brutos e analisados (posts, comentários, sentimentos).

- <NOME_DO_PORTAL>_grafico.png: Gráfico de barras com distribuição de sentimentos.
