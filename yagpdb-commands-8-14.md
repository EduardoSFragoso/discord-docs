# YAGPDB — Commands 8–14 (Role Menu + Media Stores)

Companion to [yagpdb-leveling-setup.md](yagpdb-leveling-setup.md), which covers commands 1–7 (leveling).
Day-to-day operations guide (roles, menus, media): [yagpdb-roles-and-media-guide.md](yagpdb-roles-and-media-guide.md).
Numbering follows the full dashboard: commands 1–7 leveling, 8–10 role menu, 11–14 media stores (the old dedicated command 11 was dropped and the list renumbered).

## Role Menu (take/release) — commands 8–10

Reaction roles, take/release: reacting to the menu message grants the linked role, removing the reaction drops it. Not in the yagpdb-cc collection — custom-built.

| # | Command name | Trigger type | Trigger | Role restrictions |
|---|---|---|---|---|
| 8 | Role menu manager | Regex | `\A(-\|<@!?204255221017214977>\s*)(rolemenu\|rrm)(\s+\|\z)` | Staff only |
| 9 | Role menu give | Reaction | Added reactions only | Open |
| 10 | Role menu take | Reaction | Removed reactions only | Open |

Usage (Discord):

```
rolemenu add <emoji> <cargo>
rolemenu remove <emoji>
rolemenu list
rolemenu post [#channel]     ← publishes/updates; the newest message is the only active one
```

Notes: menu roles must sit below the YAGPDB role; reposting makes older menu messages inert (no need to delete them).

### Command 8 of 14 — Role menu manager (restrict to staff)

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(rolemenu|rrm)(\s+|\z)`

```gotmpl
{{/*
    Command name: Role menu manager
    Trigger type: Regex
    Trigger: \A(-|<@!?204255221017214977>\s*)(rolemenu|rrm)(\s+|\z)
    Role restrictions: Require at least one of the roles -> Owner/staff
    Case sensitive: off
    Self-assignable role menu (take/release). Pairs with the reaction give/take commands.
*/}}

{{ $help := cembed
    "title" "🎭 Role Menu"
    "description" (joinStr "\n\n"
        "`rolemenu add <emoji> <cargo>`: links an emoji to a role"
        "`rolemenu remove <emoji>`: unlinks an emoji"
        "`rolemenu list`: shows current pairs"
        "`rolemenu post [#channel]`: posts/updates the menu message"
    )
    "color" 14232643
}}

{{ $mapping := sdict }}
{{ with dbGet 0 "rrMapping" }} {{ $mapping = sdict .Value }} {{ end }}

{{ if not .CmdArgs }}
    {{ sendMessage nil $help }}
{{ else }}
    {{ $sub := index .CmdArgs 0 }}

    {{ if and (eq $sub "add") (ge (len .CmdArgs) 3) }}
        {{ $trimmed := trimSpace (index .CmdArgs 1) }}
        {{ $key := "" }} {{ $display := "" }}
        {{ if reFind `\A<a?:[^:]+:\d{17,19}>\z` $trimmed }}
            {{ $m := reFindAllSubmatches `<a?:[^:]+:(\d{17,19})>` $trimmed }}
            {{ $key = index (index $m 0) 1 }}
            {{ $display = $trimmed }}
        {{ else }}
            {{ $key = $trimmed }}
            {{ $display = $trimmed }}
        {{ end }}

        {{ $input := joinStr " " (slice .CmdArgs 2) | lower }}
        {{ $exactRole := 0 }} {{ $maybeRole := 0 }}
        {{ range .Guild.Roles }}
            {{- if eq (lower .Name) (lower $input) }} {{ $exactRole = . }}
            {{- else if inFold (lower .Name) (lower $input) }} {{ $maybeRole = . }}
            {{- end -}}
        {{ end }}
        {{ $role := or $exactRole $maybeRole }}

        {{ if $role }}
            {{ $mapping.Set $key (sdict "role" $role.ID "display" $display) }}
            {{ dbSet 0 "rrMapping" $mapping }}
            Successfully linked {{ $display }} → **{{ $role.Name }}**. Add all pairs, then publish with `rolemenu post`.
        {{ else }}
            Sorry, I could not find the role you provided.
        {{ end }}

    {{ else if and (eq $sub "remove") (ge (len .CmdArgs) 2) }}
        {{ $trimmed := trimSpace (index .CmdArgs 1) }}
        {{ $key := $trimmed }}
        {{ if reFind `\A<a?:[^:]+:\d{17,19}>\z` $trimmed }}
            {{ $m := reFindAllSubmatches `<a?:[^:]+:(\d{17,19})>` $trimmed }}
            {{ $key = index (index $m 0) 1 }}
        {{ end }}
        {{ if $mapping.Get $key }}
            {{ $mapping.Del $key }}
            {{ dbSet 0 "rrMapping" $mapping }}
            Successfully removed that pair. Repost the menu with `rolemenu post` to update it.
        {{ else }}
            There is no pair for that emoji.
        {{ end }}

    {{ else if eq $sub "list" }}
        {{ if eq (len $mapping) 0 }}
            No pairs configured yet. Add some with `rolemenu add <emoji> <role>`.
        {{ else }}
            {{ $out := "" }}
            {{ range $k, $v := $mapping }}
                {{- $out = printf "%s\n%s → <@&%v>" $out ($v.Get "display") ($v.Get "role") -}}
            {{ end }}
            {{ sendMessage nil (cembed "title" "🎭 Role Menu — Pairs" "description" $out "color" 14232643) }}
        {{ end }}

    {{ else if eq $sub "post" }}
        {{ if eq (len $mapping) 0 }}
            Nothing to post yet — configure pairs first with `rolemenu add <emoji> <role>`.
        {{ else }}
            {{ $desc := "" }}
            {{ range $k, $v := $mapping }}
                {{- $desc = printf "%s\n%s → <@&%v>" $desc ($v.Get "display") ($v.Get "role") -}}
            {{ end }}
            {{ $channel := .Channel.ID }}
            {{ if and (ge (len .CmdArgs) 2) (reFindAllSubmatches `<#(\d+)>` (index .CmdArgs 1)) }}
                {{ $m := reFindAllSubmatches `<#(\d+)>` (index .CmdArgs 1) }}
                {{ $channel = toInt64 (index (index $m 0) 1) }}
            {{ end }}
            {{ $id := sendMessageRetID $channel (cembed
                "title" "🎭 Pick your roles"
                "description" (printf "%s\n\nReact below to get a role — remove your reaction to drop it." $desc)
                "color" 14232643
            ) }}
            {{ range $k, $v := $mapping }}
                {{/* Custom emojis go as "name:id" (no angle brackets); unicode passes through as-is. */}}
                {{ $em := $v.Get "display" }}
                {{ if reFind `<a?:[^:]+:\d+>` $em }} {{ $em = reReplace `<a?:([^:]+):(\d+)>` $em "$1:$2" }} {{ end }}
                {{ addMessageReactions $channel $id $em }}
            {{ end }}
            {{ dbSet 0 "rrMenuMsg" (sdict "id" $id "channel" $channel) }}
            Menu posted! Only THIS message grants roles — older menu messages become inert after a repost.
        {{ end }}

    {{ else }}
        {{ sendMessage nil $help }}
    {{ end }}
{{ end }}
```

### Command 9 of 14 — Role menu give

Trigger type: `Reaction` — check **"Added reactions only"**. No role restrictions.

```gotmpl
{{/*
    Command name: Role menu give
    Trigger type: Reaction (Added reactions only)
    Role restrictions: none
    Gives the role linked to the emoji when a user reacts to the active menu message.
*/}}

{{ $menu := 0 }}
{{ with dbGet 0 "rrMenuMsg" }} {{ $menu = sdict .Value }} {{ end }}

{{ if and $menu (eq .ReactionMessage.ID $menu.id) }}
    {{ $key := .Reaction.Emoji.Name }}
    {{ if .Reaction.Emoji.ID }} {{ $key = str .Reaction.Emoji.ID }} {{ end }}
    {{ with dbGet 0 "rrMapping" }}
        {{ $mapping := sdict .Value }}
        {{ with $mapping.Get $key }}
            {{ $cfg := sdict . }}
            {{ addRoleID ($cfg.Get "role") }}
        {{ end }}
    {{ end }}
{{ end }}
```

### Command 10 of 14 — Role menu take

Trigger type: `Reaction` — check **"Removed reactions only"**. No role restrictions.

```gotmpl
{{/*
    Command name: Role menu take
    Trigger type: Reaction (Removed reactions only)
    Role restrictions: none
    Removes the role linked to the emoji when a user un-reacts from the active menu message.
*/}}

{{ $menu := 0 }}
{{ with dbGet 0 "rrMenuMsg" }} {{ $menu = sdict .Value }} {{ end }}

{{ if and $menu (eq .ReactionMessage.ID $menu.id) }}
    {{ $key := .Reaction.Emoji.Name }}
    {{ if .Reaction.Emoji.ID }} {{ $key = str .Reaction.Emoji.ID }} {{ end }}
    {{ with dbGet 0 "rrMapping" }}
        {{ $mapping := sdict .Value }}
        {{ with $mapping.Get $key }}
            {{ $cfg := sdict . }}
            {{ removeRoleID ($cfg.Get "role") }}
        {{ end }}
    {{ end }}
{{ end }}
```

## Media stores (GIF / image) — commands 11–14

Per-name media lookup. set/del are staff-only (enforced by dashboard Role restrictions on the admin commands); lookups are open to everyone. Trigger patterns are split by argument count so admin and public commands never overlap — a non-staff member typing `gif set ...` triggers nothing.

Usage (Discord):

```
gif set <nome> <link-direto>   (staff)      image set <nome> <link-direto>   (staff)
gif <nome> / gif list / gif del <nome>      image <nome> / image list / image del <nome>
```

Notes: links must be direct file links (tenor: right-click → copy image address; imgur: i.imgur.com). Name rules: letters/numbers/`-`/`_`, up to 32 chars.

| # | Command name | Trigger type | Trigger | Role restrictions |
|---|---|---|---|---|
| 11 | GIF admin | Regex | `\A(-\|<@!?204255221017214977>\s*)gif\s+(set\|del)(\s+\|\z)` | Staff only |
| 12 | GIF public | Regex | `\A(-\|<@!?204255221017214977>\s*)gif(\s+|\z)` | Open |
| 13 | Image admin | Regex | `\A(-\|<@!?204255221017214977>\s*)(image\|img\|imagem)\s+(set\|del)(\s+\|\z)` | Staff only |
| 14 | Image public | Regex | `\A(-\|<@!?204255221017214977>\s*)(image\|img\|imagem)(\s+|\z)` | Open |

### Command 11 of 14 — GIF admin (restrict to staff)

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)gif\s+(set|del)(\s+|\z)`

```gotmpl
{{/*
    Command name: GIF admin
    Trigger type: Regex
    Trigger: \A(-|<@!?204255221017214977>\s*)gif\s+(set|del)(\s+|\z)
    Role restrictions: Require at least one of the roles -> Owner/staff
    Case sensitive: off
    Usage: gif set <name> <direct-link> | gif del <name>
*/}}

{{ $store := sdict }}
{{ with dbGet 0 "gifStore" }} {{ $store = sdict .Value }} {{ end }}

{{/* The trigger already consumes "gif set|del", so CmdArgs[0] is the name
    and CmdArgs[1]+ the URL (set). len == 1 means "del". */}}
{{ $name := "" }}
{{ if ge (len .CmdArgs) 1 }} {{ $name = lower (index .CmdArgs 0) }} {{ end }}

{{ if ge (len .CmdArgs) 2 }}
    {{ $url := joinStr " " (slice .CmdArgs 1) }}
    {{ if not (reFind `\A[\w-]{1,32}\z` $name) }}
        Invalid name — letters, numbers, `-` and `_` only, up to 32 characters.
    {{ else if not (reFind `\Ahttps?://\S+\z` $url) }}
        That does not look like a valid link (must start with http/https). Use the DIRECT link to the file — tenor: right-click the GIF → copy image address; imgur: the i.imgur.com link.
    {{ else }}
        {{ $store.Set $name (sdict "url" $url) }}
        {{ dbSet 0 "gifStore" $store }}
        Saved! Anyone can now use it with `-gif {{ $name }}`.
    {{ end }}
{{ else if eq (len .CmdArgs) 1 }}
    {{ if $store.Get $name }}
        {{ $store.Del $name }}
        {{ dbSet 0 "gifStore" $store }}
        Deleted.
    {{ else }}
        There is no GIF registered under that name.
    {{ end }}
{{ else }}
    Usage: `gif set <nome> <link-direto>` or `gif del <nome>`.
{{ end }}
```

### Command 12 of 14 — GIF public

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)gif(\s+|\z)`

```gotmpl
{{/*
    Command name: GIF public
    Trigger type: Regex
    Trigger: \A(-|<@!?204255221017214977>\s*)gif(\s+|\z)
    Role restrictions: Ignore the roles in the following list
    Case sensitive: off
    Usage: gif | gif <name> | gif list
*/}}

{{ $store := sdict }}
{{ with dbGet 0 "gifStore" }} {{ $store = sdict .Value }} {{ end }}

{{ if not .CmdArgs }}
    {{ sendMessage nil (cembed
        "title" "🎞️ GIFs"
        "description" (joinStr "\n\n"
            "`gif <nome>`: posts the GIF *(everyone)*"
            "`gif list`: lists registered GIFs *(everyone)*"
            "Staff: `gif set <nome> <link-direto>` and `gif del <nome>`"
        )
        "color" 14232643
    ) }}
{{ else if eq (lower (index .CmdArgs 0)) "list" }}
    {{ if not (len $store) }}
        No GIFs registered yet.
    {{ else }}
        {{ $names := cslice }}
        {{ range $k, $v := $store }} {{ $names = $names.Append $k }} {{ end }}
        {{ sendMessage nil (cembed "title" "🎞️ Registered GIFs" "description" (printf "%d GIF(s): %s" (len $names) (joinStr ", " $names)) "color" 14232643) }}
    {{ end }}
{{ else }}
    {{ $name := lower (index .CmdArgs 0) }}
    {{ with $store.Get $name }}
        {{ $entry := sdict . }}
        {{ sendMessage nil (cembed "image" (sdict "url" ($entry.Get "url")) "color" 14232643) }}
    {{ else }}
        No GIF found under `{{ $name }}`. Run `-gif` for help.
    {{ end }}
{{ end }}
```

### Command 13 of 14 — Image admin (restrict to staff)

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(image|img|imagem)\s+(set|del)(\s+|\z)`

```gotmpl
{{/*
    Command name: Image admin
    Trigger type: Regex
    Trigger: \A(-|<@!?204255221017214977>\s*)(image|img|imagem)\s+(set|del)(\s+|\z)
    Role restrictions: Require at least one of the roles -> Owner/staff
    Case sensitive: off
    Usage: image set <name> <direct-link> | image del <name>
*/}}

{{ $store := sdict }}
{{ with dbGet 0 "imgStore" }} {{ $store = sdict .Value }} {{ end }}

{{/* The trigger already consumes "image set|del", so CmdArgs[0] is the name
    and CmdArgs[1]+ the URL (set). len == 1 means "del". */}}
{{ $name := "" }}
{{ if ge (len .CmdArgs) 1 }} {{ $name = lower (index .CmdArgs 0) }} {{ end }}

{{ if ge (len .CmdArgs) 2 }}
    {{ $url := joinStr " " (slice .CmdArgs 1) }}
    {{ if not (reFind `\A[\w-]{1,32}\z` $name) }}
        Invalid name — letters, numbers, `-` and `_` only, up to 32 characters.
    {{ else if not (reFind `\Ahttps?://\S+\z` $url) }}
        That does not look like a valid link (must start with http/https). Use the DIRECT link to the file.
    {{ else }}
        {{ $store.Set $name (sdict "url" $url) }}
        {{ dbSet 0 "imgStore" $store }}
        Saved! Anyone can now use it with `-image {{ $name }}`.
    {{ end }}
{{ else if eq (len .CmdArgs) 1 }}
    {{ if $store.Get $name }}
        {{ $store.Del $name }}
        {{ dbSet 0 "imgStore" $store }}
        Deleted.
    {{ else }}
        There is no image registered under that name.
    {{ end }}
{{ else }}
    Usage: `image set <nome> <link-direto>` or `image del <nome>`.
{{ end }}
```

### Command 14 of 14 — Image public

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(image|img|imagem)(\s+|\z)`

```gotmpl
{{/*
    Command name: Image public
    Trigger type: Regex
    Trigger: \A(-|<@!?204255221017214977>\s*)(image|img|imagem)(\s+|\z)
    Role restrictions: Ignore the roles in the following list
    Case sensitive: off
    Usage: image | image <name> | image list
*/}}

{{ $store := sdict }}
{{ with dbGet 0 "imgStore" }} {{ $store = sdict .Value }} {{ end }}

{{ if not .CmdArgs }}
    {{ sendMessage nil (cembed
        "title" "🖼️ Images"
        "description" (joinStr "\n\n"
            "`image <nome>`: posts the image *(everyone)*"
            "`image list`: lists registered images *(everyone)*"
            "Staff: `image set <nome> <link-direto>` and `image del <nome>`"
        )
        "color" 14232643
    ) }}
{{ else if eq (lower (index .CmdArgs 0)) "list" }}
    {{ if not (len $store) }}
        No images registered yet.
    {{ else }}
        {{ $names := cslice }}
        {{ range $k, $v := $store }} {{ $names = $names.Append $k }} {{ end }}
        {{ sendMessage nil (cembed "title" "🖼️ Registered images" "description" (printf "%d image(s): %s" (len $names) (joinStr ", " $names)) "color" 14232643) }}
    {{ end }}
{{ else }}
    {{ $name := lower (index .CmdArgs 0) }}
    {{ with $store.Get $name }}
        {{ $entry := sdict . }}
        {{ sendMessage nil (cembed "image" (sdict "url" ($entry.Get "url")) "color" 14232643) }}
    {{ else }}
        No image found under `{{ $name }}`. Run `-image` for help.
    {{ end }}
{{ end }}
```
