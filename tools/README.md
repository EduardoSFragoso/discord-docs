# Tools — caixa de ferramentas do wrestling com GRF de ragnarok (kRO)

Tudo roda com Python 3.x, a partir da raiz do repo. Só `emotes_gift.py`
precisa de extras: `pip install pillow numpy`.

## Leitores (biblioteca, reutilizáveis)

| Tool | O quê | Uso |
|---|---|---|
| [`grf_extract.py`](grf_extract.py) | Leitor `.grf` v2xx/v3xx (kRO incluso, com obfuscação de tabela e fallback multi-snapshot p/ GRFs custom tipo Event Horizon) | `from grf_extract import Grf; g = Grf(path); g.read(r'data\sprite\...')` |
| [`grf_index.py`](grf_index.py) | Indexa um GRF em JSON (`nome → [srcpos, srclen, saligned, declen, ftype]`) com nomes cp949 corretos; também extrai por prefixo | `python tools/grf_index.py build <arquivo.grf> <saida.json> [--prefix data\palette]` · `sample` · `extract` |
| [`grf_pack.py`](grf_pack.py) | Reempacota GRFs num único GRF com nomes corretos: payloads zlib copiados verbatim, dedup por md5, header no layout canônico kRO (o que o GRF Editor aceita sem pedir senha) | `python tools/grf_pack.py <saida.grf> <base.json> [override.json ...]` — o **último** JSON é o primário |
| [`spr_reader.py`](spr_reader.py) | Leitor `.spr` v1.2/v2.0 → imagens paletadas (index 0 = transparente); suporta paleta externa | `from spr_reader import read_spr` · CLI: `python tools/spr_reader.py <in.spr> <out.png> [external.pal]` |
| [`act_reader.py`](act_reader.py) | Leitor `.act` (todas as versões 2.x, incl. a cauda v2.4/+ das sprites de player) + composição/render de frames e contact sheets | `from act_reader import read_act, render_frame, export_action` |
| [`fix_names.py`](fix_names.py) | Conserta nomes mojibake de pastas extraídas (cp1252 ↔ euc-kr roundtrip) | `python tools/fix_names.py <pasta>` (dry-run) · `--apply` |

## Geradores

| Tool | O quê | Uso |
|---|---|---|
| [`emotes_gift.py`](emotes_gift.py) | 98 emoticons do kRO (`emotion.spr/.act`) → GIF **lossless** (paleta global exata, timing do campo `speed` do ACT). Saída em `media/emotes/` + legenda | `python tools/emotes_gift.py` |

## Scripts históricos (one-shot — os GRFs de Downloads foram apagados)

São o registro de **como** os JSONs de `media/_src/grf_index/` nasceram;
só rodam de novo se você recriar os GRFs/pastas de referência.

| Tool | O quê |
|---|---|
| [`custom_v2_index.py`](custom_v2_index.py) | Higienizou os 30.2k nomes quebrados do custom_decoded (match por sufixo de nome + md5 de payload) → `custom_v2.json` |
| [`custom_v2_round2.py`](custom_v2_round2.py) | Rodada 2: reparou prefixos de pasta via árvore de parent-paths (custom v1 + classic) |
| [`idx_fresh_official.py`](idx_fresh_official.py) | Regenerou o `official_fresh.json` do GRF oficial re-baixado |
| [`cross_validate.py`](cross_validate.py) | Provou que offsets do índice leem os mesmos bytes da extração do GRF Editor (amostra de 300) |

## Convenções do ecossistema

- **Índices** (`media/_src/grf_index/*.json`, comitados com `-f`):
  `nome cp949 unicode → [srcpos, srclen, saligned, declen, ftype]`;
  payload = `seek(srcpos + 0x2E) → saligned bytes → zlib → declen`.
  São a única sobrevivência dos GRFs originais apagados.
- **Header canônico do `grf_pack.py`** (por que o GRF Editor aceita): bytes
  `0x0F-0x1D` = `00 01 02 … 0E`; `0x1E` = offset da tabela relativo a `0x2E`
  (nosso layout = `0`); `0x22` seed = 0; `0x26` = n+7; `0x2A` = versão 0x200.
  GRF Editor pedindo senha 99% das vezes = header em offset errado.
- **Nomes de arquivo GRF** são bytes cp949 (coreano). Mojibake em tela:
  GRF Editor → Settings → Display encoding → Korean (949). Em código,
  `nome.encode('cp1252').decode('euc-kr')` volta do mojibake.
- **Dados extraídos vivem no GRF-fonte vivo** `G:\Ragnarok\data.grf`
  (Event Horizon custom): nada extraído precisa de backup — reextrair.
