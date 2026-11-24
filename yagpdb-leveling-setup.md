# YAGPDB Leveling System — Setup Guide

Companion docs: [yagpdb-commands-8-14.md](yagpdb-commands-8-14.md) — role menu + media stores (commands 8–14); [yagpdb-roles-and-media-guide.md](yagpdb-roles-and-media-guide.md) — day-to-day operations (roles, menus, media).
Dashboard numbering: 1–7 leveling (this doc), 8–10 role menu, 11–14 media stores.

Reference for configuring the leveling system from <https://yagpdb-cc.github.io/leveling/overview> (commands by jo3-l).

Codes below are copied from the official docs with one fix applied: the header comment of every command now closes with `*/}}` (the docs' rendering dropped the `}}` when copied).

## Prerequisites

1. Invite the bot: <https://yagpdb.xyz> → log in with Discord → select the server.
2. **Move the YAGPDB role above every role used as a level reward** (roles are granted bottom-up in Discord).
3. Bot permissions needed: Manage Roles, Send Messages, Embed Links, Add Reactions, Read Message History.

## Commands

Dashboard → **Custom Commands** → **New Custom Command**, one per section below. Paste the code into the **Code** tab, set the **Trigger type / Trigger** exactly as noted, save.

> ⚠️ Commands 3, 4 and 5 must be restricted to a staff role under **Roles/Categories restrictions** — otherwise any member can configure the system and set their own XP.

Summary:

| # | Command | Trigger type | Trigger |
|---|---|---|---|
| 1 | Message handler | Regex | `\A` |
| 2 | Reaction handler | Reaction | Added reactions only |
| 3 | Configure settings (staff only) | Regex | `\A(-\|<@!?204255221017214977>\s*)(leveling\|(level\|lvl)-?conf\|(level\|lvl)-?settings)(\s+\|\z)` |
| 4 | Configure role rewards (staff only) | Regex | `\A(-\|<@!?204255221017214977>\s*)(role-?rewards\|rr)(\s+\|\z)` |
| 5 | Set XP/Level (staff only) | Regex | `\A(-\|<@!?204255221017214977>\s*)(set-?(xp\|level))(\s+\|\z)` |
| 6 | View leaderboard | Regex | `\A(-\|<@!?204255221017214977>\s*)(leaderboard\|lb\|top)(\s+\|\z)` |
| 7 | View rank | Regex | `\A(-\|<@!?204255221017214977>\s*)(rank\|lvl\|xp)(\s+\|\z)` |

Notes:

- **Channel restrictions** on command 1 double as an XP whitelist/blacklist: channels in the "Ignore the channels in the following list" earn no XP. No code change needed.
- All 7 commands must exist for the system to work as expected.

## Activation

```
-leveling use-default
```

Expected: `Done! You are now using the default settings for the leveling system`.
Defaults: min 15 / max 25 XP per message, 1 minute cooldown, announcements on.

## Customization (Discord commands)

```
-leveling set cooldown 1 minute
-leveling set min 20
-leveling set max 25
-leveling set-announcements true
-leveling set-channel #general    (or "none" = announce in the channel where the user leveled up)
-rr add 5 Regular                 (role reward, levels 1-100, 1 role per level)
-rr set-type highest              (or "stack")
-leveling view / -rr view         (inspect current settings)
```

- `-leveling` / `-rr` with no args show a help embed.
- Rank card: in command 7's code set `{{ $rankcard := true }}`; `$background` below it sets the image.
- Level formula: `f(x) = 100x²` (XP required for level x). Changing it requires editing ~5 commands; not recommended.
- Level-up message text lives in command 1: search for `You've leveled up to level`.

## Command 1 of 14 — Message handler

Trigger type: `Regex` — Trigger: `\A`

```gotmpl
{{/*
	Command name: Message handler
	Trigger type: Regex
	Trigger: \A
	Role restrictions: none — must run for everyone
	Case sensitive: off

	Handles messages for the leveling system.
	See <https://yagpdb-cc.github.io/leveling/message-handler> for more information.

	Author: jo3-l <https://github.com/jo3-l>
*/}}

{{ $settings := 0 }} {{/* Instantiate settings at nil value */}}
{{ $roleRewards := sdict "type" "stack" }} {{/* Default role reward settings */}}
{{ with (dbGet 0 "xpSettings") }} {{ $settings = sdict .Value }} {{ end }} {{/* If in db, then we update value */}}
{{ with (dbGet 0 "roleRewards") }} {{ $roleRewards = sdict .Value }} {{ end }} {{/* See above */}}

{{ $cooldown := false }} {{/* We presume that user is not on cooldown */}}
{{ if (dbGet .User.ID "xpCooldown") }} {{ $cooldown = true }} {{ end }} {{/* Make user on cooldown if there is cooldown DB entry */}}

{{ if and (not $cooldown) $settings }} {{/* Make sure that both the user is not on cooldown and settings exist */}}
	{{ $amtToGive := randInt $settings.min $settings.max }} {{/* Amount of XP to give */}}
	{{ $currentXp := 0 }} {{/* User current XP */}}
	{{ with (dbGet .User.ID "xp") }}
		{{ $currentXp = .Value }}
	{{ end }} {{/* Update XP amount if present */}}

	{{ $currentLvl := roundFloor (mult 0.1 (sqrt $currentXp)) }} {{/* Calculate level */}}
	{{ $newXp := dbIncr .User.ID "xp" $amtToGive }} {{/* Increment the xp */}}
	{{ $newLvl := roundFloor (mult 0.1 (sqrt $newXp)) }} {{/* Calculate new level */}}
	{{ $channel := or $settings.channel .Channel.ID }}
	{{ if not (.Guild.GetChannel $channel) }} {{ $channel = .Channel.ID }} {{ end }}

	{{ if ne $newLvl $currentLvl }} {{/* If the level changed / user ranked up */}}
		{{ $type := $roleRewards.type }} {{/* Type of role giving (highest / stack) */}}
		{{ $toAdd := or ($roleRewards.Get (json $newLvl)) 0 }} {{/* Try to get the role reward for this level */}}
		{{ range $level, $reward := $roleRewards }} {{/* Loop over role rewards */}}
			{{- if and (ge (toInt $newLvl) (toInt $level)) (not (hasRoleID $reward)) (eq $type "stack") (ne $level "type") }} {{- addRoleID $reward }}
			{{- else if and (hasRoleID $reward) (eq $type "highest") $toAdd }} {{- removeRoleID $reward }} {{- end -}}
		{{ end }}
		{{ if $toAdd }} {{ addRoleID $toAdd }} {{ end }}
		{{ $embed := cembed
			"title" "❯ Level up!"
			"thumbnail" (sdict "url" "https://webstockreview.net/images/emoji-clipart-celebration-4.png")
			"description" (printf "Congratulations **%s**! You've leveled up to level %d - keep it up!" .User.String (toInt $newLvl))
			"color" 14232643
		}}
			{{ if $settings.announcements }}
			{{ sendMessage $channel (complexMessage "content" .User.Mention "embed" $embed) }} {{/* Send levelup notification */}}
			{{ end }}
	{{ end }}

	{{ $cooldownSeconds := div $settings.cooldown 1000000000 }} {{/* Convert cooldown to seconds */}}
	{{ dbSetExpire .User.ID "xpCooldown" true $cooldownSeconds }} {{/* Set cooldown entry */}}
{{ end }}
```

## Command 2 of 14 — Reaction handler

Trigger type: `Reaction` — check **"Added reactions only"**

```gotmpl
{{/*
	Command name: Reaction handler
	Trigger type: Reaction
	Trigger option: Added reactions only
	Role restrictions: none
	Case sensitive: n/a

	Handles reactions for the leveling system.
	See <https://yagpdb-cc.github.io/leveling/reaction-handler> for more information.

	Author: jo3-l <https://github.com/jo3-l>
*/}}

{{ $action := .Reaction.Emoji.Name }} {{/* The action being ran */}}
{{ $validEmojis := cslice "▶️" "◀️" }} {{/* Valid emojis */}}
{{ $isValid := false }} {{/* Whether this is actually a valid embed / leaderboard embed */}}
{{ $page := 0 }} {{/* The current page */}}
{{ with and (eq .ReactionMessage.Author.ID .BotUser.ID) .ReactionMessage.Embeds }} {{/* Checks for validity */}}
	{{ $embed := index . 0 }} {{/* The first embed */}}
	{{ if and (eq $embed.Title "❯ Leaderboard") $embed.Footer }} {{/* More checks */}}
		{{ $page = reFind `\d+` $embed.Footer.Text }} {{/* We presume that this is valid, and get the page num */}}
		{{ $isValid = true }} {{/* Yay, it is valid */}}
	{{ end }}
{{ end }}
{{ if and (in $validEmojis $action) $isValid $page }} {{/* Even more checks for validity... */}}
	{{ deleteMessageReaction nil .ReactionMessage.ID .User.ID $action }}
	{{ if eq $action "▶️" }} {{ $page = add $page 1 }} {{/* Update page according to emoji */}}
	{{ else }} {{ $page = sub $page 1 }} {{ end }}
	{{ if ge $page 1 }} {{/* Otherwise, dbTopEntries throws error due to negative skip */}}
		{{ $skip := mult (sub $page 1) 10 }} {{/* Get skip */}}
		{{ $users := dbTopEntries "xp" 10 $skip }} {{/* Fetch entries */}}
		{{ if (len $users) }} {{/* If there are users on this page, proceed */}}
			{{ $rank := $skip }}
			{{ $display := "" }} {{/* Display for leaderboard embed */}}
			{{ range $users }} {{- /* Loop over users and format */}}
				{{- $xp := toInt .Value }} {{- /* The user XP */}}
				{{- $rank = add $rank 1 }} {{- /* The user rank */}}
				{{- $display = printf "%s\n• **%d.** [%s](https://yagpdb.xyz) :: Level %d (%d XP)"
					$display $rank .User.String (toInt (roundFloor (mult 0.1 (sqrt $xp)))) $xp
				}} {{- /* Format display */ -}}
			{{ end }}
			{{ editMessage nil .ReactionMessage.ID (cembed
				"title" "❯ Leaderboard"
				"thumbnail" (sdict "url" "https://i.imgur.com/mJ7zu6k.png")
				"color" 14232643
				"description" $display
				"footer" (sdict "text" (joinStr "" "Page " $page))
			) }} {{/* Edit embed */}}
		{{ end }}
	{{ end }}
{{ end }}
```

## Command 3 of 14 — Configure settings (restrict to staff)

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(leveling|(level|lvl)-?conf|(level|lvl)-?settings)(\s+|\z)`

```gotmpl
{{/*
	Command name: Configure settings
	Trigger type: Regex
	Trigger: \A(-|<@!?204255221017214977>\s*)(leveling|(level|lvl)-?conf|(level|lvl)-?settings)(\s+|\z)
	Role restrictions: Require at least one of the roles -> Owner/staff
	Case sensitive: off

	Manages the general leveling settings for the server.
	See <https://yagpdb-cc.github.io/leveling/configure-settings> for more information.

	Author: jo3-l <https://github.com/jo3-l>
*/}}

{{/* Help message for convenience in sending */}}
{{ $helpMsg := cembed
	"title" "🏆 Leveling"
	"description" (joinStr "\n\n"
		"`leveling use-default`: Use the default settings"
		"`leveling set <key> <value>`: Sets the given settings to the value provided. Valid keys are \"min\", \"max\", and \"cooldown\" (duration)."
		"`leveling set-channel <channel|none>`: Sets the channel where level up messages will be sent (defaults to current channel). If you want to make it the current channel, use `leveling set-channel none`."
			"`leveling set-announcements`: Sets if you want to display the level up messages."
		"`leveling view`: Views the current settings."
	)
	"color" 14232643
}}
{{ if .CmdArgs }}
	{{ $isSaved := false }} {{/* Whether the settings are saved */}}
	{{ $currentSettings := sdict
		"min" 15
		"max" 25
		"cooldown" .TimeMinute
			"announcements" true
	}} {{/* Defaults for level settings */}}
	{{ with (dbGet 0 "xpSettings") }}
		{{ $isSaved = true }} {{/* Settings are in DB */}}
		{{ $currentSettings = sdict .Value }} {{/* Convert value to sdict */}}
	{{ end }}

	{{ if eq (index .CmdArgs 0) "use-default" }}
		{{ $s := dbSet 0 "xpSettings" $currentSettings }} {{/* Set defaults */}}
		Done! You are now using the default settings for the leveling system.

	{{ else if and (eq (index .CmdArgs 0) "set") (ge (len .CmdArgs) 3) }}
		{{ $key := index .CmdArgs 1 }} {{/* The key of the setting being set */}}
		{{ $value := slice .CmdArgs 2 | joinStr " " }} {{/* The value of the new setting */}}
		{{ if in (cslice "min" "max" "cooldown") $key }} {{/* Check that key is valid */}}
			{{ $parsed := or (and (eq $key "cooldown") (toDuration $value)) (toInt $value) }} {{/* Find the proper type of conversion needed */}}
			{{ if not $parsed }} {{/* Check whether it was parsed correctly / whether it was valid value */}}
				Please provide a valid value for the key `{{ $key }}`.
			{{ else }}
				{{ $currentSettings.Set $key $parsed }} {{/* Set key to value */}}
				{{ if ge $currentSettings.min $currentSettings.max }} {{/* Preemptively prevent user from setting larger min value than max which would cause error later */}}
					The minimum xp cannot be larger than or equal to the max xp.
				{{ else }}
					{{ $s := dbSet 0 "xpSettings" $currentSettings }} {{/* Save it */}}
					Successfully set the key `{{ $key }}` to `{{ $value }}`!
				{{ end }}
			{{ end }}
		{{ else }}
			That was not a valid key. The only valid settings are "min", "max", and "cooldown".
		{{ end }}

	{{ else if and (eq (index .CmdArgs 0) "set-channel") (ge (len .CmdArgs) 2) }}
		{{ $input := index .CmdArgs 1 }}
		{{ with reFindAllSubmatches `<#(\d+)>` $input }} {{ $input = toInt64 (index . 0 1) }} {{ end }}
		{{ $channel := .Guild.GetChannel $input }}
		{{ if $channel }}
			{{ $currentSettings.Set "channel" $channel.ID }}
			{{ $s := dbSet 0 "xpSettings" $currentSettings }}
			Successfully set channel to <#{{ $channel.ID }}>!
		{{ else if eq $input "none" }}
			{{ $currentSettings.Del "channel" }}
			{{ $s := dbSet 0 "xpSettings" $currentSettings }}
			Successfully set the channel for level up notifications to none.
		{{ else }}
			That was not a valid channel. Try again.
		{{ end }}

	{{ else if eq (index .CmdArgs 0) "set-announcements" }}
		{{ $input := index .CmdArgs 1 | lower }}
		{{ if eq $input "true" "y" }}
			{{ $currentSettings.Set "announcements" true }}
			Successfully set the value for announcements to `true`
			{{ dbSet 0 "xpSettings" $currentSettings }}
		{{ else if eq $input "false" "n" }}
			{{ $currentSettings.Set "announcements" false }}
			Successfully set the value for announcements to `false`
			{{ dbSet 0 "xpSettings" $currentSettings }}
		{{ else }}
			That was not a valid option. The only valid options are "true" and "false".
		{{ end }}

	{{ else if eq (index .CmdArgs 0) "view" }}
		{{ $channel := "*None set*" }}
		{{ with $currentSettings.channel }} {{ $channel = printf "<#%d>" . }} {{ end }}
		{{ $formatted := printf "**❯ Minimum XP:** %d\n**❯ Maximum XP:** %d\n**❯ Cooldown:** %s\n**❯ Level-up Channel:** %s\n**❯ Announcements:** %v\n"
			$currentSettings.min
			$currentSettings.max
			(humanizeDurationSeconds ($currentSettings.cooldown | toDuration))
			$channel
			$currentSettings.announcements
		}} {{/* Construct the embed description */}}
		{{ if $isSaved }} {{/* If the settings are in DB */}}
			{{ sendMessage nil (cembed "title" "Level Settings" "description" $formatted "thumbnail" (sdict "url" "https://i.imgur.com/mJ7zu6k.png")) }}
		{{ else }}
			This server has not set up the leveling system. Run `-leveling use-default` to use the default settings or customize it using `-leveling set <key> <value>`.
		{{ end }}
	{{ else }} {{/* Send help messages */}}
		{{ sendMessage nil $helpMsg }}
	{{ end }}
{{ else }}
	{{ sendMessage nil $helpMsg }}
{{ end }}
```

## Command 4 of 14 — Configure role rewards (restrict to staff)

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(role-?rewards|rr)(\s+|\z)`

```gotmpl
{{/*
	Command name: Configure role rewards
	Trigger type: Regex
	Trigger: \A(-|<@!?204255221017214977>\s*)(role-?rewards|rr)(\s+|\z)
	Role restrictions: Require at least one of the roles -> Owner/staff
	Case sensitive: off

	Manages the role rewards of the server.
	See <https://yagpdb-cc.github.io/leveling/configure-role-rewards> for more information.

	Author: jo3-l <https://github.com/jo3-l>
*/}}

{{/* Help message */}}
{{ $helpMsg := cembed
	"title" "🏆 Role Rewards"
	"description" (joinStr "\n\n"
		"`rolerewards add <level> <role>`: Adds a role reward at the given level"
		"`rolerewards remove <level>`: Removes the role reward from the given level"
		"`rolerewards set-type <highest|stack>`: Sets the role reward type. Highest means only the highest role reward less than or equal to the current level, stack is all role rewards up to that level."
		"`rolerewards reset`: Resets role reward settings."
		"`rolerewards view`: Views current settings for role rewards."
	)
	"color" 14232643
}}
{{ if .CmdArgs }}
	{{ $roleRewards := sdict "type" "stack" }} {{/* The default setup */}}
	{{ with (dbGet 0 "roleRewards") }}
		{{ $roleRewards = sdict .Value }} {{/* Update with DB entry if present */}}
	{{ end }}
	{{ $cmd := index .CmdArgs 0 }} {{/* The subcommand used for convenience */}}

	{{ if and (eq $cmd "add") (ge (len .CmdArgs) 3) }}
		{{ $level := index .CmdArgs 1 | toInt }} {{/* The level for this role reward */}}
		{{ $input := slice .CmdArgs 2 | joinStr " " | lower }} {{/* The role name in lowercase */}}

		{{/* Exact match (irregardless of case) */}}
		{{ $exactRole := 0 }}
		{{/* Match from inFold */}}
		{{ $maybeRole := 0 }}

		{{ with reFindAllSubmatches `^<@&(\d{17,19})>|(\d{17,19})$` $input }}
			{{ $id := toInt (or (index . 0 1) (index . 0 2)) }}
			{{ range $.Guild.Roles }}
				{{- if eq .ID $id }} {{ $exactRole = . }} {{ end -}}
			{{ end }}
		{{ else }}
			{{ range .Guild.Roles }}
				{{- if eq (lower .Name) (lower $input) }} {{ $exactRole = . }}
				{{- else if inFold (lower .Name) (lower $input) }} {{ $maybeRole = . }}
				{{- end -}}
			{{ end }}
		{{ end }}

		{{ $role := or $exactRole $maybeRole }}
		{{/* If there is both level and role */}}
		{{ if and $level $role }}
			{{ if and (ge $level 1) (le $level 200) }} {{/* If level is in correct range */}}
				{{ $roleRewards.Set (str $level) $role.ID }}
				{{ $s := dbSet 0 "roleRewards" $roleRewards }} {{/* Save settings */}}
				Successfully set the role `{{ $role.Name }}` to be given at the level `{{ $level }}`.
			{{ else }}
				Sorry, the level provided was not in the range 1-200.
			{{ end }}
		{{ else }}
			Sorry, I was unable to find the role you provided / the level provided was invalid.
		{{ end }}

	{{ else if and (eq $cmd "set-type") (ge (len .CmdArgs) 2) }}
		{{ $type := index .CmdArgs 1 }}
		{{ if not (in (cslice "stack" "highest") $type) }} {{/* Check whether type is valid */}}
			Sorry, that was not a valid type. The type must be either "stack" or "highest".
		{{ else }}
			{{ $roleRewards.Set "type" $type }}
			{{ $s := dbSet 0 "roleRewards" $roleRewards }} {{/* Save settings */}}
			Successfully set the role-giving type of this server to `{{ $type }}`.
		{{ end }}

	{{ else if eq $cmd "reset" }}
		{{ $s := dbSet 0 "roleRewards" (sdict "type" "stack") }} {{/* We set the settings to default */}}
		Alright, I cleared the role rewards for this server!

	{{ else if and (eq $cmd "remove") (ge (len .CmdArgs) 2) }}
		{{ with (reFind `\d+` (index .CmdArgs 1)) }} {{/* Find level to remove */}}
			{{ if $roleRewards.Get . }}
				{{ $roleRewards.Del . }}
				{{ $s := dbSet 0 "roleRewards" $roleRewards }}
				Successfully removed the role reward from the level `{{ . }}`.
			{{ else }}
				Sorry, there is not a role reward set for that level!
			{{ end }}
		{{ else }}
			Please provide a valid level to remove the role reward from.
		{{ end }}

	{{ else if eq $cmd "view" }}
		{{ if eq (len $roleRewards) 1 }} {{/* If it is still the default settings */}}
			{{ sendMessage nil (cembed "title" "Role Rewards" "thumbnail" (sdict "url" "https://i.imgur.com/mJ7zu6k.png") "description" (joinStr "" "**❯ Role Rewards:** n/a\n**❯ Type:** " $roleRewards.type)) }}
		{{ else }}
			{{ $out := "" }} {{/* The embed description */}}
			{{ range $level := seq 1 201 }} {{- /* We can do this as we know level roles are in range 1-100 */}}
				{{- with ($roleRewards.Get (str $level)) }}
					{{- $out = printf "%s\n❯ **Level %d:** <@&%d>" $out $level . }}
				{{- end -}}
			{{ end }}
			{{/* Format and send embed */}}
			{{ sendMessage nil (cembed "title" "Role Rewards" "thumbnail" (sdict "url" "https://i.imgur.com/mJ7zu6k.png") "description" (joinStr "" $out "\n\n" "**❯ Type:** " $roleRewards.type)) }}
		{{ end }}

	{{ else }}
		{{ sendMessage nil $helpMsg }}
	{{ end }}
{{ else }}
	{{ sendMessage nil $helpMsg }}
{{ end }}
```

## Command 5 of 14 — Set XP/Level (restrict to staff)

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(set-?(xp|level))(\s+|\z)`

```gotmpl
{{/*
	Command name: Set XP/Level
	Trigger type: Regex
	Trigger: \A(-|<@!?204255221017214977>\s*)(set-?(xp|level))(\s+|\z)
	Role restrictions: Require at least one of the roles -> Owner/staff
	Case sensitive: off

	Sets the XP or level of user.
	See <https://yagpdb-cc.github.io/leveling/set-xp> for more information.

	Author: jo3-l <https://github.com/jo3-l>
*/}}

{{ $cmd := reFind `(?i)xp|level` .Cmd }} {{/* The type of command used */}}
{{ $user := 0 }} {{/* Target user */}}
{{ $newLvl := 0 }} {{/* Whether user leveled up with these changes */}}
{{ with .CmdArgs }} {{ $user = index . 0 | userArg }} {{ end }} {{/* We try to resolve user from arguments given */}}
{{ if and (eq $cmd "level") (eq (len .CmdArgs) 2) }}
	{{ $level := $.nil }}
	{{ $valid := false }}
	{{ with reFind `\A\d+\z` (index .CmdArgs 1) }} {{ $valid = true }} {{ $level = toInt . }} {{ end }}
	{{ if and $valid $user }}
		{{ $calculated := mult 100 (mult $level $level) }} {{/* Calculate XP for this level */}}
		{{ $s := dbSet $user.ID "xp" $calculated }} {{/* Update db */}}
		{{ $newLvl = $level }} {{/* As user leveled up, we change newLvl */}}
		{{ printf "Successfully set **%s**'s level to %d!" $user.String $level }}
	{{ else }}
		The syntax for this command is `-setlevel <user> <level>`.
	{{ end }}
{{ else if eq (len .CmdArgs) 2 }}
	{{ $xp := $.nil }}
	{{ $valid := false }}
	{{ with reFind `\A\d+\z` (index .CmdArgs 1) }} {{ $valid = true }} {{ $xp = toInt . }} {{ end }}
	{{ if and $valid $user }}
		{{ $oldXp := 0 }} {{/* Old XP */}}
		{{ with (dbGet $user.ID "xp") }} {{ $oldXp = .Value }} {{ end }} {{/* Update old xp with db entry */}}
		{{ $oldLvl := roundFloor (mult 0.1 (sqrt $oldXp)) }} {{/* Calculate old level */}}
		{{ $s := dbSet $user.ID "xp" $xp }} {{/* Silence the dbSet */}}
		{{ $updatedLvl := roundFloor (mult 0.1 (sqrt $xp)) }} {{/* Calculate updated level */}}
		{{ if ne $oldLvl $updatedLvl }} {{ $newLvl = $updatedLvl }} {{ end }} {{/* If level was updated, update newLvl */}}
		{{ printf "Successfully set **%s**'s XP to %d!" $user.String $xp }}
	{{ else }}
		The syntax for this command is `-setxp <user> <xp>`.
	{{ end }}
{{ else }}
	The syntax for this command is `-setxp/setlevel <user> <level|xp>`.
{{ end }}
{{/* Handle leveling up | Basically the same as whats in the message listener, so if you are curious look at that */}}
{{ if $newLvl }}
	{{ $roleRewards := sdict "type" "stack" }}
	{{ with dbGet 0 "roleRewards" }} {{ $roleRewards = sdict .Value }} {{ end }}
	{{ $type := $roleRewards.type }}
	{{ $toAdd := 0 }}
	{{ $dist := -1 }}
	{{ range $level, $reward := $roleRewards }}
		{{- if eq $level "type" }} {{- continue }} {{- end }}
		{{- if and (le (toInt $level) (toInt $newLvl)) (or (gt $dist (sub (toInt $newLvl) (toInt $level))) (eq $dist -1)) (eq $type "highest") }}
			{{- $dist = sub (toInt $newLvl) (toInt $level) }} {{- $toAdd = $reward }}
		{{- end }}
		{{- if and (ge (toInt $newLvl) (toInt $level)) (not (targetHasRoleID $user $reward)) (eq $type "stack") (ne $level "type") }} {{- giveRoleID $user $reward }}
		{{- else if and (targetHasRoleID $user $reward) (eq $type "highest") }} {{- takeRoleID $user $reward }} {{- end -}}
	{{ end }}
	{{/* TODO: Find a better solution than removing and adding this role */}}
	{{ if $toAdd }} {{ giveRoleID $user $toAdd }} {{ end }}
{{ end }}
```

## Command 6 of 14 — View leaderboard

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(leaderboard|lb|top)(\s+|\z)`

```gotmpl
{{/*
	Command name: View leaderboard
	Trigger type: Regex
	Trigger: \A(-|<@!?204255221017214977>\s*)(leaderboard|lb|top)(\s+|\z)
	Role restrictions: none
	Case sensitive: off

	Views the leaderboard of the server for the leveling system.
	See <https://yagpdb-cc.github.io/leveling/view-leaderboard> for more information.

	Author: jo3-l <https://github.com/jo3-l>
*/}}

{{ $page := 1 }}
{{ with reFind `\d+` (joinStr " " .CmdArgs) }} {{ $page = . | toInt }} {{ end }}
{{ $skip := mult (sub $page 1) 10 }}
{{ $users := dbTopEntries "xp" 10 $skip }}
{{ if not (len $users) }}
	There were no users on that page!
{{ else }}
	{{ $rank := $skip }}
	{{ $display := "" }}
	{{ range $users }}
		{{- $usr := .User.String }}
		{{- if eq $usr "#" }}
			{{- $usr = .UserID }}
		{{- end }}
		{{- $xp := toInt .Value }}
		{{- $rank = add $rank 1 }}
		{{- $display = printf "%s\n• **%d.** [%s](https://yagpdb.xyz) :: Level %d (%d XP)"
			$display $rank $usr (toInt (roundFloor (mult 0.1 (sqrt $xp)))) $xp -}}
	{{ end }}
	{{ $id := sendMessageRetID nil (cembed
		"title" "❯ Leaderboard"
		"thumbnail" (sdict "url" "https://i.imgur.com/mJ7zu6k.png")
		"color" 14232643
		"description" $display
		"footer" (sdict "text" (joinStr "" "Page " $page))
	) }}
	{{ addMessageReactions nil $id "◀️" "▶️" }}
{{ end }}
```

## Command 7 of 14 — View rank

Trigger type: `Regex` — Trigger: `\A(-|<@!?204255221017214977>\s*)(rank|lvl|xp)(\s+|\z)`

```gotmpl
{{/*
	Command name: View rank
	Trigger type: Regex
	Trigger: \A(-|<@!?204255221017214977>\s*)(rank|lvl|xp)(\s+|\z)
	Role restrictions: none
	Case sensitive: off

	Views the rank of a given member, or the triggering user.
	See <https://yagpdb-cc.github.io/leveling/view-rank> for more information.

	Author: jo3-l <https://github.com/jo3-l>
*/}}

{{/* Configurable values */}}
{{ $rankcard := false }}
{{ $background := "https://xbox-store-checker.com/assets/upload/game/2020/06/optimize/9n5qmw0x81jm-background.jpg" }}
{{/* End of configurable values */}}

{{/* Instantiate constants */}}
{{ $barEmpty := "□" }}
{{ $barFull := "■" }}
{{ $xp := 0 }} {{/* Xp of user */}}
{{ $color := 14232643 }} {{/* Embed color */}}
{{ $user := .User }} {{/* Target user */}}
{{ $colorSet := false }}

{{ with .CmdArgs }}
	{{ $temp := userArg (index . 0) }}
	{{ if $temp }}
		{{ $user = $temp }}
		{{ with dbGet $user.ID "xpColor" }} {{ $color = .Value }} {{ end }}
	{{ else if and (eq (index . 0) "set-color") (ge (len .) 2) }}
		{{ $colorSet = true }}
		{{ $multipliers := cslice 1048576 65536 4096 256 16 1 }}
		{{ $hex2dec := sdict "A" 10 "B" 11 "C" 12 "D" 13 "E" 14 "F" 15 }}
		{{ with reFindAllSubmatches `\A(?:#?default|([a-fA-F\d]{1,6}))\z` (joinStr " " (slice . 1)) }}
			{{ $hex := "D92C43" }}
			{{ with index . 0 1 }}
				{{ $hex = (printf "%06s" .) | upper }}
			{{ end }}
			{{ $dec := 0 }}
			{{ range $k, $v := split $hex "" -}}
				{{- $multiplier := index $multipliers $k }}
				{{- $num := or ($hex2dec.Get $v) $v}}
				{{- $dec = add $dec (mult $num $multiplier) -}}
			{{ end }}
			{{ dbSet $user.ID "xpColor" $dec }}
			{{ dbSet $user.ID "hex" $hex }}
			{{ $user.Mention }}, I set your rank card color to `#{{ $hex }}`.
		{{ else }}
			Please provide a valid hex to set your rank card color to.
		{{ end }}
	{{ end }}
{{ end }}
{{ if not $colorSet }}
	{{/* Get the color for this user */}}
	{{ with dbGet $user.ID "xpColor" }} {{ $color = .Value }} {{ end }}
	{{ with dbGet $user.ID "xp" }}
		{{ $xp = .Value }}
	{{ end }} {{/* If XP is there, use that */}}

	{{ $level := roundFloor (mult 0.1 (sqrt $xp)) }} {{/* Calculate level */}}
	{{ $current := sub $xp (mult 100 $level $level) }} {{/* current XP for this level */}}
	{{ if lt (toInt $xp) 100 }}
		{{ $current = $xp }}
	{{ end }} {{/* If this level < level 1, use total XP as current */}}

	{{ $nextLvl := add $level 1 }} {{/* Next level */}}
	{{ $total := sub (mult 100 $nextLvl $nextLvl) (mult 100 $level $level) }} {{/* The total until next level */}}
	{{ $percentage := (mult (fdiv $current $total) 100) | roundFloor }} {{/* Start with percentage calculations */}}
	{{ $percentage = div $percentage 10 | toInt }} {{/* Percentage out of 10 */}}

	{{ $bar := "" }} {{/* The progress bar */}}
	{{ range seq 1 11 }}
		{{- if ge $percentage . }} {{- $bar = joinStr "" $bar $barFull }} {{/* We join with full bar unicode if percentage > current iteration */}}
		{{- else }} {{- $bar = joinStr "" $bar $barEmpty }} {{- end -}} {{/* Otherwise, join with empty bar */}}
	{{ end }}

	{{ $embed := sdict
		"title" (printf "❯ %s's Rank" $user.String)
		"color" $color
		"description" (printf
			"❯ **%d / %d** XP\n❯ **Total:** %d\n❯ **Level:** %d\n❯ **Progress bar:**\n[**%s**](https://yagpdb.xyz)"
			(toInt $current) (toInt $total) (toInt $xp) (toInt $level) $bar)
	}} {{/* Format embed */}}

	{{ $rank := 0 }} {{/* Current rank of user */}}
	{{ range $index, $entry := dbTopEntries "xp" 100 0 }} {{- /* Loop over top 100 entries - see if user is in top 100 */}}
		{{- if eq .UserID $user.ID }} {{- $rank = add $index 1 }} {{- end -}}
	{{ end }}

	{{ if $rank }}
		{{ $embed.Set "description" (printf
			"🏆 *Member of Top 100*\n\n❯ **Rank:** %d\n%s"
			$rank
			$embed.description
		) }} {{/* If user in top 100, update the description */}}
	{{ end }}
{{ $bg := true }}
{{ with .CmdArgs }}
{{ $bg = false }}
{{ if and (eq (index . 0) "set-background") (ge (len .) 2) }}
			  {{ if eq (index . 1) "del" }} {{ dbDel $.User.ID "background" }} deleted
			{{ else if (reFindAllSubmatches `https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,63}\b(?:(?:(?:,?[-a-zA-Z0-9@:%_\+.~#?!&/=*]*)|(?:,?\([-a-zA-Z0-9@:%_\+.~#?!&/=*]*\))*|\[\])*)` (index . 1)) }}
			{{ dbSet $.User.ID "background" (index . 1) }} doneso
	{{ else }} thats not a valid link!
{{ end }}
{{ end }}
{{ end }}
{{ if ($rankcard) }}
{{ $rank = or $rank "100" }}
{{ $username := urlescape ($user.Username) }}
{{ with dbGet $user.ID "background" }}
{{ $background = .Value }} {{end}}
{{$pfp := "https://discord.com/assets/322c936a8c8be1b803cd94861bdfa868.png"}}
{{if $user.Avatar}} {{$pfp = ($user.AvatarURL "256")}} {{end}}

{{ sendMessage nil (cembed "color" 4645612 "image" (sdict "url" (print "https://vacefron.nl/api/rankcard?username=" $username "&avatar=" $pfp "&level=" $level "&rank=" $rank "&currentxp=" $current "&nextlevelxp=" $total "&previouslevelxp=0&custombg=" $background "&xpcolor=" ((dbGet $user.ID "hex").Value)))) }}
	 {{ else }}
	{{ sendMessage nil (cembed $embed) }}
{{ end }}
{{ end }}
```
