# Handoff — Discord Docs (YAGPDB, mídia, sprites RO)

## Sprites Ragnarok direto da fonte (pipeline novo, maio/2026)

- **Fonte**: GRF do Latam extraído pelo GRF Editor v1.9.1.8 (Tokei) para
  `C:\Users\Eduardo F\Downloads\sprite\` (~7GB, ~194k arquivos).
  Nomes de pasta coreanos viram mojibake na extração (ex.: `ÀÌ¸®Áö`,
  `¸ó½ºÅÍ` = monsters) — inofensivo, os `.spr`/`.act` que interessam têm
  nomes latin (baphomet, 4_*, etc.).
- **Decodificador**: `_src/spr_reader.py` — lê `.spr` v1.2 (paleta RLE)
  e exporta PNG/contact sheet. Testado com `npc/baphomet.spr` (43 frames,
  pixel-perfect). Formato de referência: `libgrf/sprite.c`
  (OpenKore/neoncube) — magic `SP 01 02`, imagens no offset 8,
  por imagem w/h/compressed_len **u16**, RLE com byte-0 = contagem de
  zeros, paleta nos últimos 1024 bytes.
- **Pendências do leitor**: suporte a `.spr` 2.1+ (imagens RGBA zlib e
  TGA) e parser de `.act` (animações/estados). No `.act` v2.5+:
  frames com index de sprite, offset e zoom — é o caminho pra montar
  composições por estado (idle/atk/death) sem recorte manual.
- **Preview atual**: composição de `baphomet-up.png` feita com as
  sheets antigas; a imagem final aprovada está em `media/baphomet-up.png`
  e publicada (raw link no GitHub). Caso precise refazer usar os frames
  do GRF: baphomet = `Downloads/sprite/npc/baphomet.spr`.
  O "arcebispo morto" não apareceu com nome latin no dump (procurar
  NPC/QS ou sheets da web).

## Infra

- Backup do laro na VM: cron 04:00 UTC, script `~/backup_laro.sh`
  (pg_dump → gzip → PAR OCI → healthchecks). Falha pontual em
  24/11/2026 resolvida; crontab agora redireciona pra
  `~/backup_laro/cron.log` (`>> ... 2>&1`) pra não falhar em silêncio.
