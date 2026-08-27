import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("PlayerStats")

MC_HOST = "192.168.178.128"
MC_USER = "admin"
STATS_DIR = "/home/admin/minecraft/world/players/stats"
USERCACHE_PATH = "/home/admin/minecraft/usercache.json"

async def run_remote_cmd(cmd: str) -> str:
    """Executes a command on the Minecraft server host and returns output."""
    full_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {MC_USER}@{MC_HOST} '{cmd}'"
    proc = await asyncio.create_subprocess_shell(
        full_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode("utf-8", errors="ignore").strip()

async def get_all_player_stats() -> dict[str, dict]:
    """Fetches all player stats mapped to player names."""
    try:
        cache_raw = await run_remote_cmd(f"cat {USERCACHE_PATH} 2>/dev/null || true")
        usercache = json.loads(cache_raw) if cache_raw else []
    except Exception:
        usercache = []

    uuid_to_name = {u["uuid"]: u["name"] for u in usercache if "uuid" in u and "name" in u}

    # Fetch stats files
    files_list = await run_remote_cmd(f"ls {STATS_DIR}/*.json 2>/dev/null || true")
    if not files_list:
        return {}

    all_stats = {}
    for fpath in files_list.splitlines():
        uuid = fpath.split("/")[-1].replace(".json", "")
        player_name = uuid_to_name.get(uuid, uuid[:8])
        raw_json = await run_remote_cmd(f"cat {fpath} 2>/dev/null || true")
        if raw_json:
            try:
                data = json.loads(raw_json)
                all_stats[player_name] = data.get("stats", {})
            except Exception:
                continue

    return all_stats


def parse_player_data(stats: dict) -> dict:
    custom = stats.get("minecraft:custom", {})
    mined = stats.get("minecraft:mined", {})

    # Playtime in ticks (20 ticks = 1 sec)
    ticks = custom.get("minecraft:play_time", 0)
    seconds = ticks // 20
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # Diamonds mined
    diamonds = (
        mined.get("minecraft:diamond_ore", 0) +
        mined.get("minecraft:deepslate_diamond_ore", 0)
    )

    # Ancient debris / Netherite
    debris = mined.get("minecraft:ancient_debris", 0)

    # Distance in km
    cm = (
        custom.get("minecraft:walk_one_cm", 0) +
        custom.get("minecraft:sprint_one_cm", 0) +
        custom.get("minecraft:fly_one_cm", 0) +
        custom.get("minecraft:swim_one_cm", 0) +
        custom.get("minecraft:boat_one_cm", 0) +
        custom.get("minecraft:aviate_one_cm", 0)
    )
    km = round(cm / 100000, 2)

    return {
        "hours": hours,
        "minutes": minutes,
        "total_seconds": seconds,
        "diamonds": diamonds,
        "debris": debris,
        "mob_kills": custom.get("minecraft:mob_kills", 0),
        "player_kills": custom.get("minecraft:player_kills", 0),
        "deaths": custom.get("minecraft:deaths", 0),
        "distance_km": km,
        "damage_dealt": custom.get("minecraft:damage_dealt", 0),
        "damage_taken": custom.get("minecraft:damage_taken", 0),
        "jumps": custom.get("minecraft:jump", 0)
    }


class PlayerStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Zeigt die detaillierten Ingame-Statistiken eines Minecraft-Spielers.")
    @app_commands.describe(player_name="Minecraft-Name (oder leer lassen für deinen eigenen)")
    async def stats(self, interaction: discord.Interaction, player_name: str = None):
        await interaction.response.defer(thinking=True)

        all_stats = await get_all_player_stats()
        if not all_stats:
            await interaction.followup.send("❌ Es wurden noch keine Spieler-Statistiken auf dem Server gefunden.")
            return

        target_name = player_name
        if not target_name:
            # Try to find first player or match username
            for name in all_stats.keys():
                if interaction.user.name.lower() in name.lower() or interaction.user.display_name.lower() in name.lower():
                    target_name = name
                    break
            if not target_name:
                target_name = list(all_stats.keys())[0]

        # Search matching player in all_stats (case insensitive)
        matched_key = None
        for key in all_stats.keys():
            if key.lower() == target_name.lower() or key.lower() == f".{target_name.lower()}":
                matched_key = key
                break

        if not matched_key:
            available = ", ".join([f"`{k}`" for k in all_stats.keys()[:10]])
            await interaction.followup.send(f"❌ Spieler **`{target_name}`** nicht gefunden.\nVerfügbare Spieler: {available}")
            return

        pdata = parse_player_data(all_stats[matched_key])
        clean_name = matched_key.lstrip(".")

        embed = discord.Embed(
            title=f"📊 Spieler-Statistiken: {matched_key}",
            description=f"Echte Ingame-Daten vom Minecraft SMP Server",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=f"https://visage.surgeplay.com/bust/128/{clean_name}.png")

        embed.add_field(name="⏱️ Spielzeit", value=f"**{pdata['hours']} Std. {pdata['minutes']} Min.**", inline=True)
        embed.add_field(name="💎 Diamanten", value=f"**{pdata['diamonds']}** Erze", inline=True)
        embed.add_field(name="🔥 Ancient Debris", value=f"**{pdata['debris']}** Erze", inline=True)

        embed.add_field(name="⚔️ Mob-Kills", value=f"**{pdata['mob_kills']}** Monster", inline=True)
        embed.add_field(name="☠️ Tode", value=f"**{pdata['deaths']}** Tode", inline=True)
        embed.add_field(name="🏃 Distanz", value=f"**{pdata['distance_km']} km**", inline=True)

        embed.add_field(name="🗡️ Schaden ausgeteilt", value=f"**{pdata['damage_dealt']:,} HP**", inline=True)
        embed.add_field(name="🛡️ Schaden erlitten", value=f"**{pdata['damage_taken']:,} HP**", inline=True)
        embed.add_field(name="🦘 Sprünge", value=f"**{pdata['jumps']:,}**", inline=True)

        embed.set_footer(text="Minecraft SMP Statistik-Dashboard")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="leaderboard", description="Zeigt die Bestenliste des SMPs (Spielzeit, Diamanten, Kills, etc.).")
    @app_commands.describe(kategorie="Wähle die Wertungskategorie")
    @app_commands.choices(kategorie=[
        app_commands.Choice(name="⏱️ Spielzeit", value="playtime"),
        app_commands.Choice(name="💎 Abgebaute Diamanten", value="diamonds"),
        app_commands.Choice(name="⚔️ Getötete Mobs", value="kills"),
        app_commands.Choice(name="☠️ Tode", value="deaths"),
        app_commands.Choice(name="🏃 Zurückgelegte Distanz (km)", value="distance"),
    ])
    async def leaderboard(self, interaction: discord.Interaction, kategorie: app_commands.Choice[str]):
        await interaction.response.defer(thinking=True)

        all_stats = await get_all_player_stats()
        if not all_stats:
            await interaction.followup.send("❌ Es wurden noch keine Statistiken gefunden.")
            return

        parsed_list = []
        for name, stats in all_stats.items():
            pdata = parse_player_data(stats)
            parsed_list.append((name, pdata))

        # Sort according to choice
        if kategorie.value == "playtime":
            parsed_list.sort(key=lambda x: x[1]["total_seconds"], reverse=True)
            format_fn = lambda x: f"{x['hours']} Std. {x['minutes']} Min."
        elif kategorie.value == "diamonds":
            parsed_list.sort(key=lambda x: x[1]["diamonds"], reverse=True)
            format_fn = lambda x: f"{x['diamonds']} Diamanten"
        elif kategorie.value == "kills":
            parsed_list.sort(key=lambda x: x[1]["mob_kills"], reverse=True)
            format_fn = lambda x: f"{x['mob_kills']} Kills"
        elif kategorie.value == "deaths":
            parsed_list.sort(key=lambda x: x[1]["deaths"], reverse=True)
            format_fn = lambda x: f"{x['deaths']} Tode"
        elif kategorie.value == "distance":
            parsed_list.sort(key=lambda x: x[1]["distance_km"], reverse=True)
            format_fn = lambda x: f"{x['distance_km']} km"

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = []
        for idx, (pname, pdata) in enumerate(parsed_list[:10]):
            medal = medals[idx] if idx < len(medals) else f"`#{idx+1}`"
            val_str = format_fn(pdata)
            lines.append(f"{medal} **{pname}** — `{val_str}`")

        embed = discord.Embed(
            title=f"🏆 SMP Rangliste – {kategorie.name}",
            description="\n".join(lines) if lines else "Keine Einträge vorhanden.",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Live aus den Weltstatistiken berechnet")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PlayerStatsCog(bot))
