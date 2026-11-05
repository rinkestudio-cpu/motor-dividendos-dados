# Motor de Dividendos B3: dados

Este repositório alimenta a planilha **Motor de Dividendos B3** no Google Sheets.

O GitHub Actions roda `coletor.py` em dias úteis (10h10, 13h10, 16h10 e 19h10, horário de Brasília), baixa os indicadores públicos do [Fundamentus](https://www.fundamentus.com.br) e grava em `data/`:

| Arquivo | Conteúdo |
|---|---|
| `mercado.csv` | Indicadores de todas as ações da B3 (cotação, P/L, P/VP, DY, ROE, margens, liquidez, dívida, crescimento) |
| `proventos.csv` | Dividendos e JCP dos últimos 7 anos das ações que pagam proventos (data-com, valor, tipo, pagamento) |
| `setores.csv` | Empresa, setor e subsetor |
| `meta.csv` | Data e hora da última atualização |

Formato: separador `;`, decimal `,` e datas `dd/mm/aaaa`.

A planilha lê os arquivos com `IMPORTDATA`. Para forçar uma atualização: aba **Actions** > **Atualizar dados da B3** > **Run workflow**.

Dados públicos, sem garantia. Não é recomendação de investimento.
