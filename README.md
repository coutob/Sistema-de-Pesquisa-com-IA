# Sistema de Pesquisa de E-Commerce ficticío com produtos categorizados usando IA

## Visão geral
Este é um pequeno aplicativo de linha de comando escrito em **Python** que demonstra como usar uma **tabela hash** para indexar produtos e buscar por eles usando **tags geradas automaticamente** por um modelo de IA local (Ollama).

- Os 500 produtos de partida vêm de um arquivo JSON, criado para o usuário não ter que criar na mão exemplos de produtos.
- O arquivo JSON contém apenas exemplos de peças comuns de roupa, com variações de cor e tecido.
- As tags são criadas **na memória** a cada execução – nada é gravado de volta no disco.
- O programa funciona totalmente offline, desde que o **Ollama** esteja rodando e o modelo `qwen2.5-coder:1.5b` esteja disponível.

## Por que eu fiz isso?
Estou no segundo período do curso de **Sistemas de Informação** e esse é meu trabalho de Estrutura de Dados utilizando tabelas hash de forma prática. Também foi a primeira vez que configurei o Ollama para gerar sugestões de tags a partir de textos. O objetivo foi unir a teoria (hash) com algo mais “real” (IA), além de configurar tudo no Linux.


### Requisitos
1. **Python 3.9+**
2. **Ollama** instalado e rodando localmente (`http://127.0.0.1:11434`).
3. Modelo `qwen2.5-coder:1.5b` instalado no Ollama, bem leve e rápido.

### Passo a passo
```bash
# 1. Clone o repositório (ou copie a pasta)

# 2. Instale dependências (apenas a padrão da lib std, nada extra)
#    Não há pacotes externos, então nada a instalar.

# 3. Certifique‑se de que o Ollama está ativo
ollama serve  # deixa o servidor rodando em background

# 4. Execute o programa pelo terminal
python projeto4.py
```

### Menu interativo
```
1 – Cadastrar novo produto (apenas em memória)
2 – Buscar produto por termo/tags (IA)
3 – Listar todos os produtos carregados
4 – Inspecionar a tabela hash (mostra buckets e colisões)
0 – Sair
```
Todas as operações são temporárias; ao fechar o programa nada é salvo.

## Estrutura de arquivos
```
projeto_ed1/
│   projeto4.py          # código principal
│   produtos.json  # 500 produtos de exemplo (sem tags)
│   README.md            # este arquivo
```

## Pontos de aprendizagem
- **Tabela hash**: implementei `criar_tabela`, `funcao_hash`, `inserir_na_tabela` e consultas rápidas por tag.
- **IA local**: usei a API do próprio Ollama para gerar tags a partir de nomes e descrições.
- **Persistência zero**: todo o catálogo fica em RAM, o que facilita testes e evita escrita acidental.

---
*Feito por alguém que ainda tem muito a aprender e está bem feliz por ter conseguido criar um primeiro programa funcional, útil e com implementação de IA*
