# YAGPDB — Roles & Media: Operational Guide

Day-to-day guide for role rewards, the reaction role menu, Discord role management and the media store commands.
Code/setup for the underlying custom commands: [yagpdb-leveling-setup.md](yagpdb-leveling-setup.md) (commands 1–7) and [yagpdb-commands-8-14.md](yagpdb-commands-8-14.md) (commands 8–14).

---

## 1. Role creation in Discord (prerequisite for everything)

Server Settings → **Roles**:

1. Locate the **YAGPDB** role — it must stay **above every role the bot manages** (rewards and menu roles), otherwise `addRoleID` fails silently and the error shows up in the command's *Last error* panel.
2. Create a role: **Create Role** → name → pick a color → save.
3. Drag roles into position (list is drag-and-drop). Recommended order, top to bottom:
   - Staff/admin roles
   - YAGPDB bot role
   - Level reward roles — **highest level on top** (100 first, descending)
   - Role-menu roles (below rewards, above `@everyone`)
4. On cosmetic roles (rewards + menu), keep **"Display members separately" off** to avoid cluttering the online list.
5. To grab a role ID anywhere: enable Developer Mode (Settings → Advanced) → right-click the role → **Copy ID**.

## 2. Role rewards (leveling) — command 4 (`-rr`)

Manages which role is granted at which level. Requires commands 1–7 (leveling system) installed and activated with `-leveling use-default`.

| Command | What it does |
|---|---|
| `-rr add <level> <role_name>` | Links a role to a level (1 role per level, levels 1–200) |
| `-rr remove <level>` | Removes the reward from that level |
| `-rr set-type <stack\|highest>` | `stack` = keep all earned roles; `highest` = only the highest remains |
| `-rr view` | Shows the current setup |
| `-rr reset` | Clears all rewards |
| `-rr` (no args) | Help embed |

Aliases: `role-rewards`, `rolerewards`, `rr`. Staff-restricted.

### Current configuration (agreed setup)

Mode: **`highest`** — the user keeps only the top role, so their chat color always reflects their latest reward.

| Level | Role | Color |
|---|---|---|
| 1 | `Level 1 · Neófito` | 🩶 `#95A5A6` |
| 10 | `Level 10 · Errante` | 🟢 `#2ECC71` |
| 20 | `Level 20 · Caçador` | 🩵 `#1ABC9C` |
| 30 | `Level 30 · Gladiador` | 🔵 `#3498DB` |
| 40 | `Level 40 · Campeão` | 🟣 `#9B59B6` |
| 50 | `Level 50 · Guardião` | 🌸 `#E91E63` |
| 60 | `Level 60 · Paladino` | 🟢 `#1F8B4C` (verde-escuro) |
| 70 | `Level 70 · Grão-Mestre` | 🟤 `#C27C0E` (bronze) |
| 80 | `Level 80 · Lenda` | 🔴 `#E74C3C` |
| 90 | `Level 90 · Titã` | ⚫ `#2C3E50` |
| 100 | `Level 100 · Colosso` | 🟡 `#F1C40F` (ouro) |

Colors: the Discord role color picker accepts **custom hex** (aside from the preset swatches) — the hexes above can be entered directly. Bronze/gold: Grão-Mestre = dark yellow (`#C27C0E`), Colosso = bright yellow (`#F1C40F`), so the metal still reads as an upgrade.

Naming convention (updated 2026-11-24): the ladder reads as a single epic progression — Neófito → Errante → Caçador → Gladiador → Campeão → Guardião → Paladino → Grão-Mestre → Lenda → Titã → Colosso. Paladino (60) uses dark green instead of orange so it doesn't clash with Grão-Mestre's bronze (70).

`Level 1 · Neófito` is ALSO the **autorole** (YAGPDB dashboard → Autorole): every new member gets it on join, so nobody is colorless before their first level-up. With `-rr set-type highest`, the colour then climbs the ladder on its own.

To (re)apply the full ladder:

```
-rr add 1 Level 1 · Neófito
-rr add 10 Level 10 · Errante
-rr add 20 Level 20 · Caçador
-rr add 30 Level 30 · Gladiador
-rr add 40 Level 40 · Campeão
-rr add 50 Level 50 · Guardião
-rr add 60 Level 60 · Paladino
-rr add 70 Level 70 · Grão-Mestre
-rr add 80 Level 80 · Lenda
-rr add 90 Level 90 · Titã
-rr add 100 Level 100 · Colosso
-rr set-type highest
-rr view
```

Notes:

- Create-first rule: the roles must already exist in Discord (section 1) before `-rr add`, using the exact names.
- If `-rr add` says "unable to find the role", check for typos/extra spaces — the match is by name (case-insensitive, exact-or-partial) or by mention/ID.
- Members who leveled up while rewards were empty/misconfigured don't gain roles retroactively: run `-setlevel <user> <current level>` on them (same level) to force the role assignment.

## 3. Role menu (reaction roles) — commands 8–10 (`-rolemenu`)

Take/release menu: react on the menu message → gain the role; remove the reaction → lose it.

| Command | What it does |
|---|---|
| `-rolemenu add <emoji> <cargo>` | Links an emoji to a role (staff) |
| `-rolemenu remove <emoji>` | Unlinks an emoji (staff) |
| `-rolemenu list` | Shows current pairs |
| `-rolemenu post [#channel]` | Publishes/updates the menu message (staff) |
| `-rolemenu` (no args) | Help embed |

Aliases: `rrm`. Unicode emojis (`🔴`) and custom server emojis (`<:name:id>` — paste the emoji directly) both work.

Workflow for a new menu:

1. Create the roles in Discord (section 1) — below the YAGPDB role.
2. Link each pair: `-rolemenu add 🔴 Vermelho`
3. Publish: `-rolemenu post #escolha-cargos`
4. Test with a second account or ask a member: react → role arrives; un-react → role goes away.

Notes:

- Only the **latest posted** menu grants roles; after a repost, old menu messages are inert (safe to just leave or delete manually).
- Changing a pair requires a repost for the menu message to show the updated list.
- Un-react removes the role (take/release) — intended for the game-channel roles.

Game-channel menu (seções por jogo, definido 2025-11-24). Custom emojis live in `emojis-roles/` (source links in handoff of the folder): poring (Ragnarok, sprite do divine-pride), poe (logo wiki), warframe, albion (favicon, JPG), adventurequest (favicon, 32px).

```
-rolemenu add :poring: Ragnarok
-rolemenu add :poe: Path of Exile
-rolemenu add :warframe: Warframe
-rolemenu add :albion: Albion
-rolemenu add :adventurequest: Adventure Quest
-rolemenu add 🎁 jogos-gratis
-rolemenu post
```

Each game role gets **View Channel** on its category (category-level overwrite); the game categories hide channels from `@everyone` and from the level-ladder roles. The `jogos-gratis` role keeps only its webhook/mention purpose.

## 4. Media stores — commands 11–14 (`-gif` / `-image`)

Named media lookup: staff registers name → direct link once; anyone can call it forever.

| Command | Who | What it does |
|---|---|---|
| `-gif set <nome> <link-direto>` | Staff | Registers a GIF under `<nome>` |
| `-gif <nome>` | Everyone | Posts the GIF |
| `-gif list` | Everyone | Lists registered names |
| `-gif del <nome>` | Staff | Removes the entry |
| `-image set/list/del ...` | idem | Same, separate storage, for static images |

Aliases: `-image` also answers to `img` and `imagem`.

Link rules (the only friction point):

1. Must start with `http`/`https` and point **directly at the file**, not a page.
2. **Tenor**: open the GIF → right-click it → *Copy image address* (a `media.tenor.com/....gif` link). The normal share link does not render.
3. **Imgur**: use the `i.imgur.com/....gif` link (the gallery page link does not).
4. **Any server**: attach the media to a message in a private channel, right-click the attachment → *Copy link* (`cdn.discordapp.com/attachments/...`) — the most reliable option, hosted on Discord's own CDN.
5. Name rules: letters/numbers/`-`/`_`, up to 32 chars; reserved names: `set`, `list`, `del`.

Workflow example (the old dedicated `-galuverior` command lives here now):

```
-gif set galuverior https://media.tenor.com/xxxxx/galuverior.gif
-gif galuverior
```

If the embed posts but the image doesn't render, the link isn't a direct file link — redo it via method 4 (Discord attachment).

## 5. Troubleshooting cheat sheet

| Symptom | Check |
|---|---|
| Role not granted on level up | YAGPDB role position vs. reward role; command 1's *Last error* in dashboard |
| `-rr add` can't find role | Exact name/typo; role must exist first |
| Reaction does nothing | Reacted on the *latest* posted menu? Emoji still linked (`-rolemenu list`)? Trigger of commands 9/10 = Reaction + correct "Added/Removed" option? |
| 400 "emoji_id is not snowflake" on `-rolemenu post` | Command 8's post branch must send custom emojis as `name:id` (no `<>`). Fixed in [yagpdb-commands-8-14.md](yagpdb-commands-8-14.md); re-paste the post branch if the dashboard copy is old |
| `-gif set` / `-image set` answers Usage with valid syntax | Old templates read `set` from CmdArgs[0], but the trigger already consumes `set|del`. Templates 11/13 were fixed (CmdArgs[0] = name); re-paste if the dashboard copy is old |
| `-gif <nome>` / `-image <nome>` answers help | Old public triggers consumed the argument (`gif(\s+[^\s]+)?`); fixed to `gif(\s+|\z)` so CmdArgs carries the name. Re-paste triggers of commands 12/14 if the dashboard copy is old |
| GIF/image doesn't render | Link must be direct file link (section 4, item 2–4) |
| Command "does nothing" for members | Role restrictions set to *Require* a role the user lacks (commands 3–5, 8, 11, 13) |
