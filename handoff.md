# Handoff — Discord Docs (YAGPDB, mídia, sprites RO)

## Sprites Ragnarok direto da fonte (pipeline novo, maio/2026)

- **Fonte**: GRF do Latam extraído pelo GRF Editor v1.9.1.8 (Tokei) para
  `C:\Users\Eduardo F\Downloads\sprite\` (~7GB, ~194k arquivos).
  Nomes de pasta coreanos viram mojibake na extração (ex.: `ÀÌ¸®Áö`,
  `¸ó½ºÅÍ` = monsters) — inofensivo, os `.spr`/`.act` que interessam têm
  nomes latin (baphomet, 4_*, etc.).
- **Decodificador**: `tools/spr_reader.py` — lê `.spr` v1.2 (paleta RLE)
  e v2.0, e exporta PNG/contact sheet. Testado com `npc/baphomet.spr`
  (43 frames, pixel-perfect). Formato de referência: `libgrf/sprite.c`
  (OpenKore/neoncube) — magic `SP 01 02`, imagens no offset 8,
  por imagem w/h/compressed_len **u16**, RLE com byte-0 = contagem de
  zeros, paleta nos últimos 1024 bytes.
- **SPR v2.0** (`SP 00 02`, magic revisado empiricamente; 64/65 flores
  do dump validam a leitura): igual v1.2 mas **sem RLE e sem
  compressed_len** — entrada = u16 w, u16 h + w*h bytes crus de índice
  de paleta; paleta igual (últimos 1024 bytes). `n_imagens == 0` é
  possível (arquivo degenerado, ex. `ÀÌÆÑÆ®/ef_snow.spr`). Varredura do
  dump: 86.528 arquivos v1.2 e 65 v2.0 (todas asas/robe) — **não existe
  SPR 2.1+ (RGBA zlib/TGA) neste GRF**; suporte fica fora de escopo
  até aparecer uma amostra real.
- **Fix de nomes zuados**: `tools/fix_names.py` — a extração do GRF
  Editor em Windows pt-BR decodificou os nomes EUC-KR (coreano) como
  CP1252. O script refaz o caminho (nome -> encode cp1252 -> decode
  euc-kr) e renomeia; seco com relatório em UTF-8
  (`fix_names_report.txt`, console não imprime coreano). Foi aplicado à
  pasta extraída: diretórios como `¸ó½ºÅÍ` viraram `몬스터`.
- **Pendências do leitor**: nenhuma bloqueante; se aparecer um `.spr`
  2.1+ (RGBA zlib/TGA), não confiar na ordem de campos sem amostra.
  O parser de `.act` existe e funciona: `tools/act_reader.py`
  (v2.0-2.5, lê actions/frames/layers com offsets, mirror, escala e
  rotação; `render_frame`/`export_action`/`export_act_grid` pra render).
  Mapa de ações de monstro: 0-7 idle, 8-15 walk, 16-23 attack,
  24-31 flinch (6f), 32 die (5f), por direção. Spec de referência:
  `media/_src/act_spec.md` (gitignored) (rdw-archive ACT.MD) + baphomet.act v2.1!? (kRO
  Latam): stride fixo 72B/frame c/ 1 layer, bloco 8B unknown entre
  layers e soundId (o loader do GRF Editor omite), sensível a região
  fantasma de actions declaradas no header (parser lê parcial).
  O "arcebispo morto" não apareceu com nome latin no dump (procurar
  NPC/QS ou sheets da web).
- **Preview atual**: composição de `baphomet-up.png` feita com as
  sheets antigas; a imagem final aprovada está em `media/baphomet-up.png`
  e publicada (raw link no GitHub). Caso precise refazer usar os frames
  do GRF: baphomet = `Downloads/sprite/npc/baphomet.spr`.
  O "arcebispo morto" não apareceu com nome latin no dump (procurar
  NPC/QS ou sheets da web).

## Jobs do GRF com paleta externa (24/11/2026)

- Renderizados com `render_jobs.py` (media/_src, gitignored) usando as
  paletas oficiais de `Downloads\palette\¸ö\` (mojibake de `몸통`):
  `ab_m-pal0/1.png` (Arc Bishop macho, 118 imgs), `ab_f-pal0/1.png`
  (fêmea), `hp_m-pal0/1.png` (High Priest macho, 117). Saíram com a
  cor certa do jogo (bege/azul). Página de candidatos atualizada com
  elas no topo: `media/_src/candidatos.html` (preview em
  http://localhost:8734/candidatos.html).
- Corpo dos jobs fica em `sprite\인간족\몸통\{남,여}\`, cabeça em
  `palette\¸Ó¸®\` (do lado de onde eu procurava). Paleta por job:
  `palette\¸ö\{job}_{남|여}_{0..7}.pal`.

## GRFs padrão vs customizados (achados do dia)

- Todos os GRFs do Latam testados são **customizados**:
  - `G:\Ragnarok\data.grf` (4.5GB): "Event Horizon", formato b64+CSV
    próprio — inviável sem GUI.
  - `Downloads\data-custom.grf` e `Downloads\official_data.grf`:
    "Event Horizon" também.
  - `Downloads\data.grf` (2.6GB, Jun/2020): magic e tabela clássicos
    ("Master of Magic", versão 0x200) **mas** a file table vem partida
    em 23 snapshots zlib espalhados pelo arquivo (header perde o
    offset). Com o parser corrigido, **lê praticamente tudo**: amostra
    aleatória de 300 arquivos -> 245 com magic confirmado (SPR/ACT/BMP),
    52 com extensão sem magic conhecido lendo sem erro, 3 `.pal` que
    só não batem com o header de paleta que assumi (falso negativo
    provável). Os sprites dos jobs (ex. `아크비숍_남.spr`, 231.060
    bytes) leem inteiros e com magic certo (a soma dos tamanhos
    comprimidos da tabela fecha com os 2.6GB do arquivo).
  - `tools/grf_extract.py` agora: (a) corrige o parser da entrada
    (offset era u32 DEPOIS do byte de flags; o "<IIII" antigo engolia
    o bitmap de flags junto e quebrava qualquer offset > 16MB) e
    (b) faz fallback multi-snapshot: escaneia o arquivo por streams
    zlib que começam com caminhos `data\`, agrupa os snapshots e na
    leitura tenta um por um (o mais recente primeiro, valida
    `len == declen`).
- Consequência prática: pipeline próprio **funciona de novo** no
  data.grf oficial de 2020 (caminho valioso pra extrair coisas que não
  entraram no GRF Editor). Pro GRF do Latam instalado (Event Horizon)
  o GRF Editor segue sendo o caminho; pasta extraída
  `Downloads\sprite\` + spr_reader/act_reader renderizando com .pal.

## Infra


- Backup do laro na VM: cron 04:00 UTC, script `~/backup_laro.sh`
  (pg_dump → gzip → PAR OCI → healthchecks). Falha pontual em
  24/11/2026 resolvida; crontab agora redireciona pra
  `~/backup_laro/cron.log` (`>> ... 2>&1`) pra não falhar em silêncio.
