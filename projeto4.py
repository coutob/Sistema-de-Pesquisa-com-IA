import json
import urllib.request
import sys
import io
# Reconfigure stdin to ignore decoding errors that may appear in some terminal settings
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='ignore')

# ==============================================================
# PROJETO 4: CATÁLOGO DE PRODUTOS COM TABELA HASH E IA
# Disciplina: Estrutura de Dados (Sistemas de Informação)
# Versão: Sem Persistência em Disco (Tudo em Memória / Somente Leitura)
# ==============================================================


# --------------------------------------------------------------
# 1. FUNÇÕES DA TABELA HASH (ESTRUTURA DE DADOS)
# --------------------------------------------------------------

def criar_tabela(tamanho=500):
    """
    Cria uma Tabela Hash com um vetor de tamanho fixo inicial (padrão: 500).
    Cada bucket é uma lista para tratar colisões por encadeamento.
    """
    return [[] for _ in range(tamanho)]


def funcao_hash(tag, tamanho=500):
    """
    Função Hash Simples (Soma dos códigos ASCII):
    Soma os valores ASCII dos caracteres e calcula o resto da divisão.
    """
    soma = 0
    for letra in tag:
        soma += ord(letra)
    return soma % tamanho


def inserir_na_tabela(tabela, tag, produto):
    """
    Insere um produto associado a uma tag na Tabela Hash em memória.
    Trata colisão por encadeamento.
    """
    tag = tag.strip().lower()
    if not tag:
        return

    indice = funcao_hash(tag, len(tabela))
    bucket = tabela[indice]

    # 1. Verifica se a tag já existe nesse bucket
    for item in bucket:
        if item["tag"] == tag:
            for p in item["produtos"]:
                if p["id"] == produto["id"]:
                    return  # Evita duplicar o produto sob a mesma tag
            item["produtos"].append(produto)
            return

    # 2. Se a tag não existe no bucket, cria uma nova entrada
    bucket.append({
        "tag": tag,
        "produtos": [produto]
    })


def buscar_por_tag(tabela, tag):
    """Busca produtos associados a uma tag específica."""
    tag = tag.strip().lower()
    indice = funcao_hash(tag, len(tabela))
    bucket = tabela[indice]

    for item in bucket:
        if item["tag"] == tag:
            return item["produtos"]
    return []


def buscar_por_varias_tags(tabela, tags, max_resultados=10):
    """
    Busca produtos associados a uma ou mais tags.
    Ranqueia por relevância: produtos que combinam com mais tags aparecem primeiro.
    """
    relevancia = {}  # id -> {"produto": prod, "pontos": int}

    for tag in tags:
        tag_limpa = tag.strip().lower()
        produtos = buscar_por_tag(tabela, tag_limpa)
        for prod in produtos:
            pid = prod["id"]
            if pid not in relevancia:
                relevancia[pid] = {"produto": prod, "pontos": 0}
            relevancia[pid]["pontos"] += 1

    if not relevancia:
        return []

    # Ordena decrescente pelo número de tags correspondentes (maior relevância no topo)
    ordenados = sorted(
        relevancia.values(),
        key=lambda item: item["pontos"],
        reverse=True
    )

    return [item["produto"] for item in ordenados[:max_resultados]]


def inspecionar_tabela(tabela):
    """Exibe no terminal a distribuição dos buckets, colisões e nós em memória."""
    print("\n-- Estrutura Interna da Tabela Hash (Buckets e Colisões) --")
    buckets_ocupados = 0

    for i, bucket in enumerate(tabela):
        if bucket:
            buckets_ocupados += 1
            cadeia = [f"'{item['tag']}' ({len(item['produtos'])} prod)" for item in bucket]
            print(f"  Bucket [{i:03d}] -> {' -> '.join(cadeia)}")

    print(f"\nTotal de buckets ocupados: {buckets_ocupados} de {len(tabela)}")


# --------------------------------------------------------------
# 2. INTEGRAÇÃO COM IA E GERAÇÃO DE TAGS
# --------------------------------------------------------------

def extrair_tags_simples(texto):
    """Extrai palavras-chave significativas para uso em memória."""
    palavras = texto.lower().replace(",", " ").replace(".", " ").replace("-", " ").split()
    stopwords = {"para", "com", "sem", "por", "dos", "das", "uma", "uns", "que", "mais", "manga"}
    return [p for p in palavras if len(p) > 2 and p not in stopwords]


def gerar_tags_com_ia(texto, modelo="qwen2.5-coder:1.5b", max_tags=5):
    """
    Envia requisição para a IA (Ollama local) gerar tags a partir do texto de consulta.
    Retorna apenas a lista de tags em memória, sem persistência.
    """
    prompt = (
        f"Extraia de 2 a {max_tags} palavras-chave curtas e diretas sobre este produto ou busca: '{texto}'. "
        "Responda SOMENTE em JSON no formato: {\"tags\": [\"tag1\", \"tag2\"]}. "
        "Não inclua explicações ou texto adicional."
    )

    dados = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    url = "http://127.0.0.1:11434/api/generate"
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(dados).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=15) as resposta:
            corpo = json.loads(resposta.read().decode("utf-8"))
            texto_resposta = corpo.get("response", "{}")
            json_tags = json.loads(texto_resposta)
            lista_tags = json_tags.get("tags", [])

            tags_finais = [t.strip().lower() for t in lista_tags if isinstance(t, str) and t.strip()]
            if tags_finais:
                return tags_finais[:max_tags]
    except Exception:
        # Fallback de segurança: caso o Ollama esteja offline
        pass

    # Fallback automático: extrai as palavras-chave do texto
    return extrair_tags_simples(texto)[:max_tags]


# --------------------------------------------------------------
# 3. LEITURA DE DADOS INICIAIS (SOMENTE LEITURA - SEM GRAVAÇÃO)
# --------------------------------------------------------------

def carregar_produtos_do_disco():
    """
    Lê os produtos do arquivo JSON original apenas para carregar na memória.
    Não altera nem grava nada no disco.
    """
    caminhos = [
        "produtos.json",
        "/home/stl/Documents/vscode/projeto_ed1/produtos.json",
        "produtos.json",
        "/home/stl/produtos.json"
    ]
    for caminho in caminhos:
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                return dados, caminho
        except (FileNotFoundError, Exception):
            continue
    return [], "Nenhum arquivo encontrado"


# --------------------------------------------------------------
# 4. PROGRAMA PRINCIPAL (MENU NO TERMINAL)
# --------------------------------------------------------------

def main():
    tabela = criar_tabela(500)
    produtos_cadastrados, arquivo_origem = carregar_produtos_do_disco()
    proximo_id = 1

    # Indexa os produtos na Tabela Hash exclusivamente em memória RAM
    for prod in produtos_cadastrados:
        # Se o produto não tiver tags predefinidas no arquivo, gera em memória pelo nome
        tags = prod.get("tags")
        if not tags:
            texto = f"{prod.get('nome', '')} {prod.get('descricao', '')}"
            tags = extrair_tags_simples(texto)
            prod["tags"] = tags  # apenas no objeto em memória

        for tag in tags:
            inserir_na_tabela(tabela, tag, prod)

        if prod.get("id", 0) >= proximo_id:
            proximo_id = prod["id"] + 1

    print("\n" + "=" * 55)
    print("  CATÁLOGO DE PRODUTOS (TABELA HASH + IA EM MEMÓRIA)")
    print("=" * 55)
    if produtos_cadastrados:
        print(f"-> {len(produtos_cadastrados)} produtos carregados do arquivo '{arquivo_origem}'.")
        print("-> Modo: SOMENTE MEMÓRIA (Nenhuma tag é salva em disco).")
    else:
        print("-> Nenhum arquivo encontrado. Catálogo iniciado vazio.")

    while True:
        print("\n--- MENU PRINCIPAL ---")
        print("1. Cadastrar novo produto")
        print("2. Buscar produto por termo/tags (IA)")
        print("3. Listar todos os produtos em memória")
        print("4. Inspecionar Tabela Hash (buckets e colisões)")
        print("0. Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        # OPÇÃO 1: CADASTRAR PRODUTO (APENAS EM MEMÓRIA)
        if opcao == "1":
            print("\n-- Cadastro de Produto --")
            nome = input("Nome do produto: ").strip()
            descricao = input("Descrição detalhada: ").strip()

            if not nome:
                print("Aviso: O nome do produto não pode ser vazio!")
                continue

            print("\nGerando tags semânticas via IA...")
            tags = gerar_tags_com_ia(f"{nome}. {descricao}")
            print(f"Tags geradas pela IA: {tags}")

            # Permite ao usuário adicionar tags extras se quiser
            extras = input("Deseja adicionar mais tags separadas por vírgula? (Enter para pular): ").strip()
            if extras:
                for extra in extras.split(","):
                    tag_limpa = extra.strip().lower()
                    if tag_limpa and tag_limpa not in tags:
                        tags.append(tag_limpa)

            novo_produto = {
                "id": proximo_id,
                "nome": nome,
                "descricao": descricao,
                "tags": tags
            }
            proximo_id += 1
            produtos_cadastrados.append(novo_produto)

            # Indexa o produto na Tabela Hash em memória
            for tag in tags:
                inserir_na_tabela(tabela, tag, novo_produto)

            print(f"\nProduto ID {novo_produto['id']} ('{novo_produto['nome']}') indexado na Tabela Hash!")
            print("(Cadastrado apenas nesta sessão em memória, sem salvar em disco)")

        # OPÇÃO 2: BUSCAR PRODUTOS VIA IA (SEM PERSISTÊNCIA)
        elif opcao == "2":
            print("\n-- Busca no Catálogo com IA --")
            consulta = input("O que você procura? ").strip()
            if not consulta:
                print("Digite algo para buscar.")
                continue

            print("Identificando tags com a IA...")
            tags_busca = gerar_tags_com_ia(consulta, max_tags=4)
            # Separe tags compostas (ex.: "sapato social") em palavras individuais
            tags_busca = [t for tag in tags_busca for t in tag.split() if t]
            print(f"Tags geradas para a busca: {tags_busca}")

            # Busca e ranqueia por relevância
            resultados = buscar_por_varias_tags(tabela, tags_busca, max_resultados=10)

            if not resultados:
                print("\nNenhum produto encontrado para essas tags.")
            else:
                print(f"\nEncontrado(s) {len(resultados)} produto(s) mais relevante(s):")
                for prod in resultados:
                    print("-" * 45)
                    print(f"ID: {prod['id']} | Nome: {prod['nome']}")
                    if prod.get("descricao"):
                        print(f"Descrição: {prod['descricao']}")
                    print(f"Tags em memória: {', '.join(prod.get('tags', []))}")

        # OPÇÃO 3: LISTAR TODOS
        elif opcao == "3":
            print(f"\n-- Produtos no Catálogo ({len(produtos_cadastrados)} itens em memória) --")
            if not produtos_cadastrados:
                print("Nenhum produto cadastrado até o momento.")
            else:
                limite_exibicao = 20
                for prod in produtos_cadastrados[:limite_exibicao]:
                    print(f"[{prod['id']}] {prod['nome']} | Tags: {', '.join(prod.get('tags', []))}")
                if len(produtos_cadastrados) > limite_exibicao:
                    print(f"\n... e mais {len(produtos_cadastrados) - limite_exibicao} produtos (total: {len(produtos_cadastrados)}).")

        # OPÇÃO 4: DEMONSTRAÇÃO DIDÁTICA DA TABELA HASH
        elif opcao == "4":
            inspecionar_tabela(tabela)

        # OPÇÃO 0: SAIR
        elif opcao == "0":
            print("\nEncerrando o programa. Até mais!")
            break

        else:
            print("Opção inválida! Tente novamente.")


if __name__ == "__main__":
    main()
