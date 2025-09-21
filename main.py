import os
import re
import time

import matplotlib.pyplot as plt
import pandas as pd
from LeIA import SentimentIntensityAnalyzer
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

analyzer = SentimentIntensityAnalyzer()


def setup_driver():
    """Configura e retorna uma instância do WebDriver do Chrome."""
    print("Configurando as opções do Google Chrome...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def login_x(driver, username, password, username_extra):
    """Executa o processo de login no X (Twitter)."""
    print("Iniciando processo de login...")
    wait = WebDriverWait(driver, 15)
    url = "https://x.com/i/flow/login"
    driver.get(url)

    input_username = wait.until(EC.presence_of_element_located((By.NAME, "text")))
    input_username.send_keys(username)
    driver.find_element(By.XPATH, "//span[text()='Next']").click()
    print("Usuário inserido.")

    # autenticação extra (se houver)
    try:

        locator_auth_extra = (
            By.CSS_SELECTOR,
            "input[data-testid='ocfEnterTextTextInput']",
        )

        campo_auth_extra = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(locator_auth_extra)
        )

        print("Autenticação extra encontrada! Preenchendo...")
        campo_auth_extra.send_keys(
            username_extra + Keys.ENTER
        )  # Combina o texto e o Enter
        print("Login extra confirmado.")

    except TimeoutException:
        print("Autenticação extra não foi necessária. Continuando...")
        pass

    input_password = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    input_password.send_keys(password)
    driver.find_element(By.XPATH, "//span[text()='Log in']").click()
    print("Senha inserida. Aguardando login...")

    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a[data-testid="AppTabBar_Home_Link"]')
        )
    )
    print("Login realizado com sucesso!")


def coletar_links_dos_posts(driver, profile_name, meta_posts):
    """
    Fase 1: Navega pela timeline de um perfil e coleta os links de uma quantidade
    definida de posts.
    """
    print(
        f"\n--- FASE 1: Coletando links de {meta_posts} posts do perfil '{profile_name}' ---"
    )
    driver.get(f"https://x.com/{profile_name}")
    time.sleep(3)

    posts_coletados = []
    links_processados = set()
    tentativas_sem_novos_posts = 0
    LIMITE_TENTATIVAS = 5
    body = driver.find_element(By.TAG_NAME, "body")

    while len(posts_coletados) < meta_posts:
        posts_na_tela = driver.find_elements(
            By.CSS_SELECTOR, 'article[data-testid="tweet"]'
        )
        links_na_tela = set()
        for post in posts_na_tela:
            link_elements = post.find_elements(By.XPATH, ".//a[time]")
            if link_elements:
                links_na_tela.add(link_elements[0].get_attribute("href"))

        if not bool(links_na_tela - links_processados):
            tentativas_sem_novos_posts += 1
            print(
                f"Nenhum post novo visível. Pressionando Page Down... (Tentativa {tentativas_sem_novos_posts}/{LIMITE_TENTATIVAS})"
            )
            if tentativas_sem_novos_posts >= LIMITE_TENTATIVAS:
                print(
                    "Limite de tentativas atingido. A página pode ter chegado ao fim."
                )
                break
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(5)
            continue

        tentativas_sem_novos_posts = 0
        for post_element in posts_na_tela:
            link_elements = post_element.find_elements(By.XPATH, ".//a[time]")
            if not link_elements:
                continue

            link = link_elements[0].get_attribute("href")
            if link in links_processados:
                continue

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                post_element,
            )
            time.sleep(1)

            text_elements = post_element.find_elements(
                By.CSS_SELECTOR, 'div[data-testid="tweetText"]'
            )
            texto = text_elements[0].text if text_elements else ""
            posts_coletados.append({"link": link, "texto": texto})
            links_processados.add(link)
            print(f"Post {len(posts_coletados)}/{meta_posts} coletado.")

            if len(posts_coletados) >= meta_posts:
                break

    print(f"\n--- COLETA DE LINKS FINALIZADA ---")
    print(f"Total de links de posts coletados: {len(posts_coletados)}\n")
    return posts_coletados


def extrair_comentarios_de_post(driver, post_url, limite_comentarios=None):
    """
    Fase 2: Visita a URL de um post, extrai os comentários até o limite
    definido. Se o limite for None, extrai todos.
    """
    print(f"Processando: {post_url}")
    driver.get(post_url)
    time.sleep(3)

    body = driver.find_element(By.TAG_NAME, "body")
    comentarios_extraidos = []
    links_processados_neste_post = set()
    tentativas_scroll_sem_novos_comentarios = 0
    LIMITE_TENTATIVAS_SCROLL = 5

    while True:
        if (
            limite_comentarios is not None
            and len(comentarios_extraidos) >= limite_comentarios
        ):
            print(
                f" -> Limite de {limite_comentarios} comentários atingido para este post."
            )
            break

        todos_os_artigos = driver.find_elements(
            By.CSS_SELECTOR, 'article[data-testid="tweet"]'
        )
        elementos_de_comentario = todos_os_artigos[1:]

        total_comentarios_antes = len(links_processados_neste_post)

        for comentario_element in elementos_de_comentario:
            if (
                limite_comentarios is not None
                and len(comentarios_extraidos) >= limite_comentarios
            ):
                break

            link_elements = comentario_element.find_elements(By.XPATH, ".//a[time]")
            if not link_elements:
                continue

            link_comentario = link_elements[0].get_attribute("href")
            if link_comentario in links_processados_neste_post:
                continue

            texto_elements = comentario_element.find_elements(
                By.CSS_SELECTOR, 'div[data-testid="tweetText"]'
            )
            texto = texto_elements[0].text if texto_elements else "N/A"

            comentarios_extraidos.append(
                {"texto_comentario": texto, "link_comentario": link_comentario}
            )
            links_processados_neste_post.add(link_comentario)

            # Mensagem de progresso
            progresso = f"Comentário #{len(comentarios_extraidos)}"
            if limite_comentarios is not None:
                progresso += f"/{limite_comentarios}"
            print(f" -> {progresso} encontrado.")

        if len(links_processados_neste_post) == total_comentarios_antes:
            tentativas_scroll_sem_novos_comentarios += 1
            if tentativas_scroll_sem_novos_comentarios >= LIMITE_TENTATIVAS_SCROLL:
                print(
                    " -> Limite de tentativas de scroll atingido. Fim dos comentários para este post."
                )
                break
        else:
            tentativas_scroll_sem_novos_comentarios = 0

        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(2.5)

    return comentarios_extraidos


def limpar_texto_completo(texto):
    """
    Esta função remove links, hashtags, menções e caracteres especiais de um texto.
    """
    if isinstance(texto, str):
        # 1. Remover links (URLs)
        texto = re.sub(r"http\S+|www\S+", "", texto)
        # 2. Remover hashtags (#palavra)
        texto = re.sub(r"#\w+", "", texto)
        # 3. Remover menções (@usuario)
        texto = re.sub(r"@\w+", "", texto)
        # 4. Remover caracteres especiais (tudo que não for letra, número ou espaço)
        texto = re.sub(r"[^\w\s]", "", texto)
        # 5. Remover espaços extras
        texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def analisar_sentimento(texto):
    """Analisa o sentimento de um texto e o classifica."""
    if not texto or not isinstance(texto, str):
        return "neutro"

    # Calcula os scores de polaridade
    score = analyzer.polarity_scores(texto)
    compound = score["compound"]

    # Classifica com base no score 'compound'
    if compound >= 0.05:
        return "positivo"
    elif compound <= -0.05:
        return "negativo"
    else:
        return "neutro"


def main():
    """
    Função principal que orquestra todo o processo de scraping.
    """
    # --- CONFIGURAÇÕES ---
    USERNAME = os.environ.get("USERNAME_TWITTER")
    # twitter com o passar dos testes pede o seu usuário
    USERNAME_EXTRA = "jorgirerison"
    PASSWORD = os.environ.get("PASSWORD_TWITTER")
    NOME_DO_PORTAL = "PortalHOTD"
    META_DE_POSTS = 30
    LIMITE_DE_COMENTARIOS_POR_POST = None  # ou 5, 10, etc.
    # --- FIM CONFIGURAÇÕES ---

    driver_principal = setup_driver()

    try:
        login_x(driver_principal, USERNAME, PASSWORD, USERNAME_EXTRA)

        posts_para_analisar = coletar_links_dos_posts(
            driver_principal, NOME_DO_PORTAL, META_DE_POSTS
        )

        # --- FASE 2 (SEQUENCIAL) ---
        dados_finais = []
        for i, post_info in enumerate(posts_para_analisar):
            print(
                f"\nAnalisando comentários do Post Principal {i + 1}/{len(posts_para_analisar)}"
            )

            comentarios = extrair_comentarios_de_post(
                driver_principal,
                post_info["link"],
                limite_comentarios=LIMITE_DE_COMENTARIOS_POR_POST,
            )

            dados_finais.append(
                {
                    "link_post_principal": post_info["link"],
                    "texto_post_principal": post_info["texto"],
                    "comentarios": comentarios,
                }
            )

        # --- GERAÇÃO DO DATAFRAME FINAL ---
        print("\n\n--- RESULTADO FINAL DA COLETA ---")

        dados_para_df = []

        for item in dados_finais:
            link_principal = item["link_post_principal"]
            texto_principal = item["texto_post_principal"]

            if not item["comentarios"]:
                dados_para_df.append(
                    {
                        "codigo_da_postagem": link_principal,
                        "texto_da_postagem": texto_principal,
                        "texto_do_comentario": None,
                        "link_comentario": None,
                    }
                )
            else:
                for comentario in item["comentarios"]:
                    dados_para_df.append(
                        {
                            "codigo_da_postagem": link_principal,
                            "texto_da_postagem": texto_principal,
                            "texto_do_comentario": comentario["texto_comentario"],
                            "link_comentario": comentario["link_comentario"],
                        }
                    )

        df = pd.DataFrame(dados_para_df)
        df["nome_portal"] = "@" + NOME_DO_PORTAL

        colunas_para_limpar = ["texto_da_postagem", "texto_do_comentario"]

        print("Iniciando a limpeza dos textos...")
        for coluna in colunas_para_limpar:
            if coluna in df.columns:
                df[coluna] = df[coluna].apply(limpar_texto_completo)
            else:
                print(f"Aviso: A coluna '{coluna}' não foi encontrada no arquivo CSV.")

        print("Iniciando análise de sentimentos")
        df["sentimento"] = df["texto_do_comentario"].apply(analisar_sentimento)
        print("Análise de sentimentos concluída.")

        print("\nSalvando os resultados em arquivos...")
        df.to_csv(f"{NOME_DO_PORTAL}_posts_comentarios.csv", index=False, encoding="utf-8-sig")

        print("Começando análise de dados...")
        sentiment_counts = (
            df.groupby(["codigo_da_postagem", "sentimento"])
            .size()
            .unstack(fill_value=0)
        )

        # Garante que todas as colunas de sentimento existam para consistência de cores
        for sent in ["positivo", "negativo", "neutro"]:
            if sent not in sentiment_counts.columns:
                sentiment_counts[sent] = 0

        # Para tornar os rótulos do eixo X mais legíveis, extraímos o ID do post
        def formatar_link_post(link):
            match = re.search(r"status/(\d+)", link)
            return f"Post {match.group(1)}" if match else link

        sentiment_counts.index = sentiment_counts.index.map(formatar_link_post)

        # Gerar o gráfico de barras empilhadas
        sentiment_counts.plot(
            kind="bar",
            stacked=True,
            figsize=(14, 8),
            color={
                "positivo": "forestgreen",
                "negativo": "crimson",
                "neutro": "silver",
            },
            width=0.8,
        )

        # Customizar o gráfico
        plt.title("Contagem de Sentimentos por Post Principal", fontsize=16, pad=20)
        plt.ylabel("Quantidade de Comentários", fontsize=12)
        plt.xlabel("Post Principal (ID)", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.legend(title="Sentimento", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout(
            rect=[0, 0, 0.85, 1]
        )  # Ajusta o layout para a legenda não cortar

        # Salvar o gráfico em um arquivo de imagem
        plt.savefig(f"{NOME_DO_PORTAL}_grafico.png")
        print("Gráfico 'sentimentos_por_post.png' salvo com sucesso!")

    finally:
        print("\nProcesso finalizado. Fechando o navegador principal.")
        driver_principal.quit()


if __name__ == "__main__":
    main()
