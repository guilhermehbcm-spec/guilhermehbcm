# QualCID Off-line

Versão off-line do [qualcid.com.br](https://www.qualcid.com.br/): busca um CID e mostra os
procedimentos SUS compatíveis (e o inverso: procedimento → CIDs). Os dados vêm da tabela
oficial **SIGTAP** do DATASUS (`rl_procedimento_cid`), a mesma fonte do site.

Sem servidor, sem bibliotecas externas, sem internet depois de carregado.

## Funcionalidades

- Busca por código (`A09`, `A00.0`, `0303010061`, `03.03.01.006-1`) ou nome, sem acento.
- Tela do CID com todos os procedimentos compatíveis, marcando **principal** / **secundário**, com filtro.
- Tela do procedimento com todos os CIDs compatíveis, sexo e faixa etária.
- Opcional: classificação (dupla/cruz-asterisco), excluídos e referências, carregando o `CID-10-SUBCATEGORIAS.CSV` do DATASUS.

## Obter os dados

Baixe o ZIP mais recente (`TabelaUnificada_AAAAMM_vXXXXXXXXXX.zip`) em
<http://sigtap.datasus.gov.br/tabela-unificada/app/download.jsp>. A SIGTAP é atualizada
mensalmente; repita o processo quando quiser atualizar.

## Opção A — HTML único com os dados embutidos (mais simples)

```bash
python3 build.py TabelaUnificada_202610_v2610XXXXXX.zip [CID-10-SUBCATEGORIAS.CSV] -o qualcid-offline.html
```

Gera um único arquivo que abre direto no navegador (duplo clique), sem precisar importar nada.

## Opção B — App (PWA) no celular

1. Publique esta pasta em qualquer hospedagem HTTPS (ex.: GitHub Pages).
2. Abra no Safari/Chrome do celular, selecione o ZIP da SIGTAP na primeira tela
   (o processamento é feito no próprio aparelho).
3. "Adicionar à Tela de Início". Daqui em diante funciona sem internet; os dados ficam salvos
   no aparelho (IndexedDB). Use "Atualizar tabela" para trocar a competência.

Também funciona abrindo `index.html` localmente num navegador de computador.

## Arquivos

| Arquivo | Função |
|---|---|
| `index.html` | App completo (interface, leitor de ZIP, parser SIGTAP, armazenamento local) |
| `build.py` | Gera o HTML único com dados embutidos |
| `sw.js`, `manifest.webmanifest`, `icon.svg` | Funcionamento off-line / instalação como app |
