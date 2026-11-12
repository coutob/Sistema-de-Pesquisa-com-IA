import json
import urllib.request

# ==============================================================
# PROJETO 4: CATÁLOGO DE PRODUTOS COM TABELA HASH E IA
# Disciplina: Estrutura de Dados (Sistemas de Informação)
# Versão Simplificada: Somente Funções e Tipos Básicos (Sem Classes)
# ==============================================================


# --------------------------------------------------------------
# 1. FUNÇÕES DA TABELA HASH (ESTRUTURA DE DADOS)
# --------------------------------------------------------------

def criar_tabela(tamanho=500):
    """
    Cria uma Tabela Hash com um vetor de tamanho fixo inicial (padrão: 101).
    Cada posição (bucket) começa como uma lista vazia para tratar colisões.
    """
    return [[] for _ in range(tamanho)]


def funcao_hash(tag, tamanho=500):
    """
    Função Hash Simples (Soma dos códigos ASCII):
    Soma os valores numéricos de cada caractere da palavra e pega
    o resto da divisão (%) pelo tamanho da tabela para obter um índice válido.
    """
    soma = 0
    for letra in tag:
        soma += ord(letra)
    return soma % tamanho


def inserir_na_tabela(tabela, tag, produto):
    """
    Insere um produto associado a uma tag na tabela hash.
    Trata colisão por encadeamento: adiciona itens na lista do mesmo bucket.
    """
    tag = tag.strip().lower()
    if not tag:
        return

    indice = funcao_hash(tag, len(tabela))
    bucket = tabela[indice]

    # 1. Verifica se a tag já existe nesse bucket
    for item in bucket:
        if item["tag"] == tag:
            # Se o produto ainda não estiver na lista dessa tag, adiciona
            for p in item["produtos"]:
                if p["id"] == produto["id"]:
                    return  # Evita duplicar o mesmo produto sob a mesma tag
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
    """Busca produtos associados a uma ou mais tags, sem retornar duplicados. Limita a quantidade retornada."""
    encontrados = []
    ids_vistos = set()

    for tag in tags:
        for prod in buscar_por_tag(tabela, tag):
            if prod["id"] not in ids_vistos:
                ids_vistos.add(prod["id"])
                encontrados.append(prod)
                if len(encontrados) >= max_resultados:
                    return encontrados
    return encontrados


def inspecionar_tabela(tabela):
    """Exibe no terminal a distribuição dos buckets, colisões e encadeamento."""
    print("\n-- Estrutura Interna da Tabela Hash (Buckets e Colisões) --")
    buckets_ocupados = 0

    for i, bucket in enumerate(tabela):
        if bucket:
            buckets_ocupados += 1
            cadeia = [f"'{item['tag']}' ({len(item['produtos'])} prod)" for item in bucket]
            print(f"  Bucket [{i:03d}] -> {' -> '.join(cadeia)}")

    print(f"\nTotal de buckets ocupados: {buckets_ocupados} de {len(tabela)}")


# --------------------------------------------------------------
# 2. INTEGRAÇÃO SIMPLES COM O OLLAMA (IA LOCAL)
# --------------------------------------------------------------

def gerar_tags_com_ia(texto, modelo="qwen2.5-coder:1.5b", max_tags=5):
    """
    Envia uma requisição HTTP simples para o Ollama local (porta 11434).
    Retorna uma lista de tags sugeridas pela IA.
    """
    prompt = (
    f"Extraia de 3 a {max_tags} palavras chave curtas e relevantes "
    f"para este produto: '{texto}'. "
    "Responda apenas em JSON: {\"tags\": [\"tag1\", \"tag2\", ...]}. "
    "Não inclua palavras genéricas, repetições, ou termos com menos de 3 "
    "ou mais de 15 letras. Me retorne no máximo 10 tags"
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
        # Tenta conectar ao Ollama local
        with urllib.request.urlopen(requisicao, timeout=15) as resposta:
            corpo = json.loads(resposta.read().decode("utf-8"))
            texto_resposta = corpo.get("response", "{}")
            json_tags = json.loads(texto_resposta)
            lista_tags = json_tags.get("tags", [])

            # Limpa e formata as tags
            tags_finais = [t.strip().lower() for t in lista_tags if isinstance(t, str) and t.strip()]
            if tags_finais:
                return tags_finais
    except Exception:
        # Fallback de segurança: se o Ollama estiver desligado ou der erro,
        # divide o texto em palavras simples para o programa nunca quebrar na apresentação
        pass

    # Tags automáticas simples a partir das palavras do texto
    palavras = texto.lower().replace(",", " ").replace(".", " ").split()
    return [p for p in palavras if len(p) > 3][:4]


# --------------------------------------------------------------
# 3. PERSISTÊNCIA DE DADOS EM ARQUIVO JSON
# --------------------------------------------------------------

ARQUIVO_PRODUTOS = "produtos(500_itens_aaaaa).json"


def salvar_produtos_em_disco(produtos):
    """Salva a lista completa de produtos diretamente em formato JSON."""
    with open(ARQUIVO_PRODUTOS, "w", encoding="utf-8") as arquivo:
        json.dump(produtos, arquivo, ensure_ascii=False, indent=2)


def carregar_produtos_do_disco():
    """Lê os produtos salvos no arquivo JSON se ele existir."""
    try:
        with open(ARQUIVO_PRODUTOS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (FileNotFoundError, Exception):
        return []


# --------------------------------------------------------------
# 4. PROGRAMA PRINCIPAL (MENU NO TERMINAL)
# --------------------------------------------------------------

def main():
    tabela = criar_tabela(500)
    produtos_cadastrados = carregar_produtos_do_disco()
    proximo_id = 1

    # Reindexa os produtos salvos na Tabela Hash
    for prod in produtos_cadastrados:
        for tag in prod.get("tags", []):
            inserir_na_tabela(tabela, tag, prod)

        if prod.get("id", 0) >= proximo_id:
            proximo_id = prod["id"] + 1

    #print("\n" + "=" * 50)
    #print("  SISTEMA DE CATÁLOGO DE PRODUTOS (ESTRUTURA DE DADOS)")
    #print("=" * 50)
    if produtos_cadastrados:
        print(f"-> {len(produtos_cadastrados)} produto(s) carregados do arquivo '{ARQUIVO_PRODUTOS}'.")
    else:
        print("-> Nenhum produto salvo anteriormente. Catálogo iniciado vazio.")

    while True:
        print("\n--- MENU PRINCIPAL ---\nLojinha de Roupas :)\n\n")
        print("1. Cadastrar novo produto")
        print("2. Buscar produto por termo/tags")
        print("3. Listar todos os produtos")
        print("4. Inspecionar Tabela Hash (buckets e colisões)")
        print("0. Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        # OPÇÃO 1: CADASTRAR PRODUTO
        if opcao == "1":
            print("\n-- Cadastro de Produto --")
            nome = input("Nome do produto: ").strip()
            descricao = input("Descrição detalhada: ").strip()

            if not nome or not descricao:
                print("Aviso: Nome e descrição não podem ser vazios!")
                continue

            print("\nGerando tags semânticas via IA...")
            tags = gerar_tags_com_ia(f"{nome}. {descricao}")
            print(f"Tags geradas: {tags}")

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

            # Indexa o produto na Tabela Hash para cada tag
            for tag in tags:
                inserir_na_tabela(tabela, tag, novo_produto)

            # Salva no arquivo de persistência
            salvar_produtos_em_disco(produtos_cadastrados)
            print(f"\nProduto ID {novo_produto['id']} ('{novo_produto['nome']}') cadastrado e salvo com sucesso!")

        # OPÇÃO 2: BUSCAR PRODUTOS
        elif opcao == "2":
            print("\n-- Busca no Catálogo --")
            consulta = input("O que você procura? ").strip()
            if not consulta:
                print("Digite algo para buscar.")
                continue

            # Extrai tags da própria consulta usando a IA (ou quebra em palavras)
            tags_busca = gerar_tags_com_ia(consulta)
            print(f"Tags identificadas para a busca: {tags_busca}")

            resultados = buscar_por_varias_tags(tabela, tags_busca)

            if not resultados:
                print("\nNenhum produto encontrado para essas tags.")
            else:
                print(f"\nEncontrado(s) {len(resultados)} produto(s):")
                for prod in resultados:
                    print("-" * 40)
                    print(f"ID: {prod['id']} | Nome: {prod['nome']}")
                    print(f"Descrição: {prod['descricao']}")
                    print(f"Tags: {', '.join(prod['tags'])}")

        # OPÇÃO 3: LISTAR TODOS
        elif opcao == "3":
            print("\n-- Lista de Produtos Cadastrados --")
            if not produtos_cadastrados:
                print("Nenhum produto cadastrado até o momento.")
            else:
                for prod in produtos_cadastrados:
                    print(f"[{prod['id']}] {prod['nome']} | Tags: {', '.join(prod['tags'])}")

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
