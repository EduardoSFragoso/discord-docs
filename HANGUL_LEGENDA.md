# Legenda HANGUL dos GRFs decodificados

> Os GRFs do Ragnarok kRO usam caminhos em coreano (EUC-KR/cp949).
> Esta legenda traduz os termos que aparecem nos caminhos de
> `classic_decoded.grf`, `custom_decoded.grf` e `official_decoded.grf`,
> e o que representam. GRF Editor: Settings → **Display encoding: Korean (949)**.

## Estrutura raiz
| caminho | tradução | o que é |
|---|---|---|
| `data\sprite\인간족` | "raça humana" | sprites de personagens humanóides |
| `data\sprite\도람족` | "raça doram" | sprites dos gatinhos (Summoner) |
| `data\sprite\몬스터` | "monstros" | monstros |
| `data\sprite\로브` | "capa/robe" | mantos, asas, capas |
| `data\sprite\아이템` | "item" | sprites de itens no chão / drop |
| `data\sprite\방패` | "escudo" | escudos |
| `data\sprite\악세사리` | "acessório" | acessórios equipáveis |
| `data\sprite\이팩트` | "efeito" | efeitos visuais + **emotes** (`emotion.spr/.act`) |
| `data\palette\` | — | paletas de corespor `body\` e `head\` |
| `data\texture\미리보기이미지` | "image prévia" | thumbs da seleção de char |

## Dentro de `인간족` (humanoide)
| pasta | tradução | o que é |
|---|---|---|
| `몸통` | "corpo (torso)" | sprites de **corpo** (o `mt` do sistema de paleta) |
| `머리통` | "cabeça" | sprites de **cabeça** (a chave do sistema de paleta) |
| `남` | "homem" | sprites masculinos |
| `여` | "mulher" | sprites femininos |

Sufixo padrão de arquivo: `{job}_{남|여}_{paleta}.act/.spr`.

## Jobs (nomes de pasta diretamente sob `인간족\`)
| hangul | classe |
|---|---|
| `초보자` | Novice |
| `검사` | Swordsman |
| `기사` | Knight |
| `페코페코_기사` | Knight (a Peco) |
| `궁수` | Archer |
| `마법사` | Mage |
| `성직자` | Acolyte |
| `상인` | Merchant |
| `도둑` | Thief |
| `어세신` | Assassin |
| `로그` | Rogue |
| `몽크` | Monk |
| `바드` | Bard |
| `무희` | Dancer |
| `세이지` | Sage |
| `위저드` | Wizard |
| `제철공` | Blacksmith |
| `연금술사` | Alchemist |
| `크루세이더` | Crusader |
| `구페코크루세이더` / `신페코크루세이더` | Crusader sem/com Peco (variante) |
| `쉐도우체이서` | Stalker / Shadow Chaser |
| `태권소년` | Taekwon |
| `슈퍼노비스` | Super Novice |
| `마도기어` | MADO Gear (Mechanic) |
| `건너` | Gunslinger |
| `레인져늑대` | Ranger (co lobo) |
| `용병` | Mercenário |
| `운영자` | Administrador (GM) |
| `kagerou`, `oboro`, `rebellion`, `summoner` | classes novas (nome em inglês mesmo) |

Classes 3ª/4ª e transcendentais tendem a virar sub-pastas/`c_` de **capa** (`로브`)
e nomes novos em inglês (ex.: `meister_riding`, `sky_emperor`).

## `texture\` (texturas de mapa/UI)
| hangul | tradução |
|---|---|
| `유저인터페이스` | interface do usuário |
| `필드바닥` | chão de campo |
| `내부소품` | adereço interno |
| `외부소품` | adereço externo |
| `나무잡초꽃` | árvores/mato/flor |
| `워터` | água |
| `프론테라` / `페이욘` / `모로코` / `게페니아` | Prontera / Payon / Morocc / Geffenia |
| `기타마을` | caminho de outras vilas |
| `워프대기실내부` | sala de espera de warp |
