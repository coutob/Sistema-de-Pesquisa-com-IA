
import json
import urllib.request
import sys
import io

#Estava dando erro em pesquisas com mais de uma palavra, isso resolveu:
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='ignore')


def criar_tabela(tamanho=500):
    # Cria a tabela com listas para guardar os produtos
    return [[] for _ in range(tamanho)]


def funcao_hash(tag, tamanho=500):
    # Soma os caracteres e calcula a posição na tabela
    soma = 0
    for letra in tag:
        soma += ord(letra)
    return soma % tamanho


def inserir_na_tabela(tabela, tag, produto):
    tag = tag.strip().lower()
    if not tag:
        return

    indice = funcao_hash(tag, len(tabela))
    bucket = tabela[indice]

    # Verifica se a tag já está cadastrada
    for item in bucket:
        if item["tag"] == tag:
            for p in item["produtos"]:
                if p["id"] == produto["id"]:
                    return
            item["produtos"].append(produto)
            return

    # Adiciona uma nova tag na tabela
    bucket.append({
        "tag": tag,
        "produtos": [produto]
    })


def buscar_por_tag(tabela, tag):
    tag = tag.strip().lower()
    indice = funcao_hash(tag, len(tabela))
    bucket = tabela[indice]

    for item in bucket:
        if item["tag"] == tag:
            return item["produtos"]
    return []


def buscar_por_varias_tags(tabela, tags, max_resultados=10):
    relevancia = {}

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

    # Mostra primeiro os produtos que combinaram com mais tags
    ordenados = sorted(
        relevancia.values(),
        key=lambda item: item["pontos"],
        reverse=True
    )

    return [item["produto"] for item in ordenados[:max_resultados]]


def inspecionar_tabela(tabela):
    print("\n-- Estrutura Interna da Tabela Hash (Buckets e Colisões) --")
    buckets_ocupados = 0

    for i, bucket in enumerate(tabela):
        if bucket:
            buckets_ocupados += 1
            cadeia = [f"'{item['tag']}' ({len(item['produtos'])} prod)" for item in bucket]
            print(f"  Bucket [{i:03d}] -> {' -> '.join(cadeia)}")

    print(f"\nTotal de buckets ocupados: {buckets_ocupados} de {len(tabela)}")


def extrair_tags_simples(texto):
    palavras = texto.lower().replace(",", " ").replace(".", " ").replace("-", " ").split()
    stopwords = {"para", "com", "sem", "por", "dos", "das", "uma", "uns", "que", "mais", "manga"}
    return [p for p in palavras if len(p) > 2 and p not in stopwords]


def gerar_tags_com_ia(texto, modelo="qwen2.5-coder:1.5b", max_tags=5):
    # Monta o pedido que será enviado para a IA
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
        # Se a IA não responder, o programa continua normalmente
        pass

    # Usa as palavras da própria busca como alternativa
    return extrair_tags_simples(texto)[:max_tags]


def carregar_produtos_do_disco():
    # Lê os produtos do arquivo JSON
    caminhos = [
        "produtos.json"
    ]
    for caminho in caminhos:
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                return dados, caminho
        except (FileNotFoundError, Exception):
            continue
    return [], "Nenhum arquivo encontrado"


def main():
    tabela = criar_tabela(500)
    produtos_cadastrados, arquivo_origem = carregar_produtos_do_disco()
    proximo_id = 1

    # Coloca os produtos do JSON na tabela hash
    for prod in produtos_cadastrados:
        tags = prod.get("tags")
        if not tags:
            texto = f"{prod.get('nome', '')} {prod.get('descricao', '')}"
            tags = extrair_tags_simples(texto)
            prod["tags"] = tags

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

            # Adiciona o novo produto na tabela
            for tag in tags:
                inserir_na_tabela(tabela, tag, novo_produto)

            print(f"\nProduto ID {novo_produto['id']} ('{novo_produto['nome']}') indexado na Tabela Hash!")
            print("(Cadastrado apenas nesta sessão em memória, sem salvar em disco)")

        elif opcao == "2":
            print("\n-- Busca no Catálogo com IA --")
            consulta = input("O que você procura? ").strip()
            if not consulta:
                print("Digite algo para buscar.")
                continue

            print("Identificando tags com a IA...")
            tags_busca = gerar_tags_com_ia(consulta, max_tags=4)
            tags_busca = [t for tag in tags_busca for t in tag.split() if t]
            print(f"Tags geradas para a busca: {tags_busca}")

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

        elif opcao == "4":
            inspecionar_tabela(tabela)

        elif opcao == "0":
            print("\nEncerrando o programa. Até mais!")
            break

        else:
            print("Opção inválida! Tente novamente.")


if __name__ == "__main__":
    main()
