#!/usr/bin/env python3
"""Generador del vídeo GTA 6 (HyperFrames).

Lee assets/transcript.json (tiempos de cada palabra) y escribe:
  index.html, compositions/world.html, compositions/captions.html

Uso:  python3 gen.py            -> con subtítulos
      python3 gen.py --no-subs  -> sin subtítulos
Todo va pegado a la voz con P("palabra", n): el inicio de la n-ésima vez que se dice.
"""
import json, math, os, random, re, subprocess, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
NO_SUBS = "--no-subs" in sys.argv
W, H = 1080, 1920
FOCUS_Y = 980  # punto de la pantalla donde la cámara centra cada escena

# ---------------------------------------------------------------- voz y tiempos
def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)

DUR = float(subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
    os.path.join(HERE, "assets/voz.wav")]).decode().strip())

raw = json.load(open(os.path.join(HERE, "assets/transcript.json")))
raw = raw if isinstance(raw, list) else raw["words"]
WORDS = []
for w in raw:
    t = w["text"].strip()
    # whisper a veces junta dos palabras ("superar.¿Lo"): se separan
    m = re.match(r"^(.+?[.,!?])\s*(¿.+)$", t)
    if m:
        WORDS.append({"text": m.group(1), "start": w["start"], "end": max(w["start"] + 0.3, w["end"] - 0.3)})
        WORDS.append({"text": m.group(2), "start": max(w["start"] + 0.3, w["end"] - 0.25), "end": w["end"]})
    else:
        WORDS.append({"text": t, "start": w["start"], "end": w["end"]})

# nombres que la voz lee "a la española": en pantalla se escriben bien
FIX = {"yeison": "Jason", "hasson": "Jason", "jeison": "Jason", "yason": "Jason",
       "boni": "Bonnie", "bonnier": "Bonnie", "bonny": "Bonnie",
       "claid": "Clyde", "selide": "Clyde", "clide": "Clyde", "claude": "Clyde"}
for w in WORDS:
    k = norm(w["text"])
    if k in FIX:
        w["text"] = re.sub(r"[\wÀ-ÿ]+", FIX[k], w["text"], count=1)
    w["n"] = norm(w["text"])

def P(word, n=1, after=0.0):
    """Inicio (s) de la n-ésima vez que se dice `word` (o una de sus variantes)."""
    opts = [norm(x) for x in (word if isinstance(word, (list, tuple)) else [word])]
    c = 0
    for w in WORDS:
        if w["start"] + 1e-6 < after:
            continue
        if w["n"] in opts:
            c += 1
            if c == n:
                return round(w["start"], 3)
    raise SystemExit(f"[gen] No encuentro la palabra {word!r} (vez {n}) en la transcripción")

def E(word, n=1, after=0.0):
    """Final (s) de esa misma palabra."""
    s = P(word, n, after)
    return round(next(w["end"] for w in WORDS if abs(w["start"] - s) < 1e-3), 3)

T = dict(
    gta=P("gta", 1), aqui=P("aqui"), numeros=P("numeros"), miedo=P("miedo"),
    d1=P("dato", 1), primer=P("primer", 1), trailer1=P("trailer", 1), n90=P(["90", "noventa"]),
    youtube=P("youtube"), dia=P("dia", 1),
    d2=P("dato", 2), segundo=P("segundo"), lejos=P("lejos"), rockstar=P("rockstar"),
    n475=P(["475", "cuatrocientos"]), horas=P("horas"), sumando=P("sumando"), redes=P("redes"),
    d3=P("dato", 3), retrasado=P("retrasado"), veces=P("veces"), primero=P("primero"),
    y2025=P(["2025", "dos"], after=P("primero")), luego=P("luego"), mayo=P("mayo"),
    final=P("final"), hoy=P("hoy"), noviembre=P("noviembre"), y2026=P(["2026"], after=P("noviembre")),
    d4=P("dato", 4), volvemos=P("volvemos"), vice=P("vice", 1), n24=P(["24", "veinticuatro"], after=P("vice", 1)),
    anos=P("anos"), primera=P("primera"), mujer=P("mujer"), lucia=P("lucia"),
    jason=P("jason"), historia=P("historia"), bonnie=P("bonnie"),
    pero=P("pero"), bestia=P("bestia"), gta5=P("gta", 2), y2013=P(["2013"]), vendido=P("vendido"),
    n230=P(["230", "doscientos"]), copias=P("copias"), liston=P("liston"), gta6b=P("gta", 3),
    superar=P("superar"), lo=P(["lo", "¿lo"], after=P("superar")), vas=P("vas"), primerdia=P("dia", 2),
    comenta=P("comenta"), vice2=P("vice", 2), leo=P("leo"),
)
T["dia_end"] = E("dia", 1)
T["redes_end"] = E("redes")
T["bonnie_end"] = E("clyde") if any(w["n"] == "clyde" for w in WORDS) else T["bonnie"] + 0.8
T["dur"] = round(DUR, 3)

# ---------------------------------------------------------------- mundo
S = {  # centro de cada escena en el lienzo gigante
    "s0": (600, 1000), "s1": (1800, 1000), "s2": (3000, 1000),
    "s3": (3000, 2600), "s4": (1800, 2600), "s5": (600, 2600), "s6": (600, 4200),
}
G1, G2, G3 = 1520, 3120, 4720  # suelo de cada fila (el camino)
WORLD_W, WORLD_H = 3700, 5000

ARC = math.pi * 100 / 2
SEGS = {
    "p0": ("M -200 1520 H 600", 800),
    "pA": ("M 600 1520 H 1800", 1200),
    "pB": ("M 1800 1520 H 3000", 1200),
    "pC": ("M 3000 1520 H 3400 A 100 100 0 0 1 3500 1620 V 3020 A 100 100 0 0 1 3400 3120 H 3000",
           400 + ARC + 1400 + ARC + 400),
    "pD": ("M 3000 3120 H 1800", 1200),
    "pE": ("M 1800 3120 H 600", 1200),
    "pF": ("M 600 3120 H 200 A 100 100 0 0 0 100 3220 V 4620 A 100 100 0 0 0 200 4720 H 600",
           400 + ARC + 1400 + ARC + 400),
}

def R(st, dx, dy):
    """Coordenadas del mundo a partir de la escena y un desplazamiento."""
    cx, cy = S[st]
    return cx + dx, cy + dy

# ---------------------------------------------------------------- iconos (Phosphor)
def icon(name, size, color, extra=""):
    svg = open(os.path.join(HERE, f"assets/icons/{name}-fill.svg")).read()
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    return (f'<svg viewBox="0 0 256 256" width="{size}" height="{size}" fill="{color}" '
            f'style="display:block" {extra}>{inner}</svg>')

# ---------------------------------------------------------------- personajes SVG
CHARS = {
    "dani":  dict(skin="#F2C29B", top="#FF8A1E", top2="#E06A00", pants="#24324D", shoe="#F4F4F5", hair="#1F2937", kind="cap"),
    "lucia": dict(skin="#C98B5E", top="#9B5CF6", top2="#7C3AED", pants="#1F2937", shoe="#F472B6", hair="#2B1A12", kind="long"),
    "jason": dict(skin="#E7B48C", top="#3B82F6", top2="#1D4ED8", pants="#3F3F46", shoe="#111827", hair="#6B4423", kind="short"),
}

def char_svg(cid):
    c = CHARS[cid]
    hair_back = hair_front = extra = ""
    if c["kind"] == "cap":
        hair_front = (f'<path d="M88,116 A62,62 0 0 1 212,116 Z" fill="{c["hair"]}"/>'
                      f'<rect x="186" y="104" width="58" height="16" rx="8" fill="{c["hair"]}"/>'
                      f'<rect x="96" y="100" width="108" height="10" rx="5" fill="#FF8A1E"/>')
    elif c["kind"] == "long":
        hair_back = f'<path d="M78,120 Q76,40 150,46 Q226,40 222,124 L230,236 Q150,262 70,236 Z" fill="{c["hair"]}"/>'
        hair_front = (f'<path d="M86,118 Q92,52 150,52 Q212,52 216,112 Q180,96 160,74 Q130,104 86,118 Z" fill="{c["hair"]}"/>'
                      f'<circle cx="94" cy="146" r="10" fill="none" stroke="#FBBF24" stroke-width="5"/>')
    else:
        hair_front = (f'<path d="M88,112 Q90,50 150,52 Q214,50 212,112 Q196,84 150,84 Q108,84 88,112 Z" fill="{c["hair"]}"/>')
        extra = f'<path d="M106,150 Q150,206 194,150 Q190,184 150,190 Q110,184 106,150 Z" fill="{c["hair"]}" opacity="0.35"/>'
    collar = (f'<path d="M126,182 L150,214 L174,182" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round"/>'
              if c["kind"] != "cap" else f'<rect x="118" y="262" width="64" height="26" rx="10" fill="{c["top2"]}"/>')
    return f'''
<div class="char" id="{cid}"><div class="flip" id="{cid}-flip">
<svg viewBox="0 0 300 470" width="300" height="470" overflow="visible">
  <ellipse cx="150" cy="452" rx="84" ry="12" fill="rgba(0,0,0,.45)"/>
  <g id="{cid}-body">
    <g id="{cid}-legL"><line x1="134" y1="300" x2="130" y2="428" stroke="{c["pants"]}" stroke-width="34" stroke-linecap="round"/><ellipse cx="138" cy="440" rx="30" ry="15" fill="{c["shoe"]}"/></g>
    <g id="{cid}-legR"><line x1="166" y1="300" x2="170" y2="428" stroke="{c["pants"]}" stroke-width="34" stroke-linecap="round"/><ellipse cx="178" cy="440" rx="30" ry="15" fill="{c["shoe"]}"/></g>
    <g id="{cid}-up">
      <g id="{cid}-armB"><line x1="196" y1="200" x2="208" y2="292" stroke="{c["top2"]}" stroke-width="28" stroke-linecap="round"/><circle cx="209" cy="302" r="17" fill="{c["skin"]}"/></g>
      <rect x="96" y="176" width="108" height="142" rx="44" fill="{c["top"]}"/>
      {collar}
      <g id="{cid}-head">
        {hair_back}
        <rect x="136" y="160" width="28" height="30" rx="10" fill="{c["skin"]}"/>
        <circle cx="150" cy="120" r="64" fill="{c["skin"]}"/>
        {extra}
        {hair_front}
        <g id="{cid}-eyes">
          <ellipse cx="132" cy="122" rx="12" ry="15" fill="#fff"/><ellipse cx="174" cy="122" rx="12" ry="15" fill="#fff"/>
          <circle cx="136" cy="124" r="7" fill="#0B0D12"/><circle cx="178" cy="124" r="7" fill="#0B0D12"/>
        </g>
        <g id="{cid}-brows"><line x1="120" y1="100" x2="142" y2="98" stroke="#0B0D12" stroke-width="5" stroke-linecap="round"/><line x1="164" y1="98" x2="186" y2="100" stroke="#0B0D12" stroke-width="5" stroke-linecap="round"/></g>
        <path id="{cid}-mouth" d="M138,152 Q156,166 172,152" fill="none" stroke="#0B0D12" stroke-width="5" stroke-linecap="round"/>
        <ellipse id="{cid}-mouthO" cx="156" cy="158" rx="11" ry="0.1" fill="#0B0D12"/>
      </g>
      <g id="{cid}-armF"><line x1="104" y1="200" x2="92" y2="292" stroke="{c["top2"]}" stroke-width="28" stroke-linecap="round"/><circle cx="91" cy="302" r="17" fill="{c["skin"]}"/></g>
    </g>
  </g>
</svg></div></div>'''

CHAR_PIVOTS = {"legL": "134 300", "legR": "166 300", "armF": "104 200", "armB": "196 200",
               "head": "150 184", "body": "150 450", "up": "150 300", "eyes": "154 122",
               "mouthO": "156 158"}

# parpadeos deterministas
random.seed(6)
BLINKS = {cid: [] for cid in CHARS}
for cid in CHARS:
    t = 0.6 + random.random()
    while t < DUR - 0.3:
        BLINKS[cid].append(round(t, 2))
        t += 2.2 + random.random() * 1.8

# ---------------------------------------------------------------- cámara
def cam_world(cx, cy, z):
    return dict(x=round(W / 2 - cx * z, 2), y=round(FOCUS_Y - cy * z, 2), scale=round(z, 4))

CAM = []  # (t, dur, cx, cy, z, ease, blur)
def cam(t, dur, cx, cy, z=1.0, ease="power2.inOut", blur=0):
    CAM.append((round(t, 3), round(dur, 3), cx, cy, z, ease, blur))

SFX = []  # (t, kind)
def sfx(t, kind):
    SFX.append((round(t, 3), kind))

def travel(t_arrive, frm, to, seg, dur=0.75, zo=True):
    """Fin de bloque: se aleja para enseñarlo entero y viaja al siguiente."""
    t0 = t_arrive - dur
    if zo:
        cam(t0 - 0.5, 0.45, *S[frm], 0.8, "power2.inOut")
    cam(t0, dur, *S[to], 1.0, "power3.inOut", blur=6)
    sfx(t0 - 0.05, "whoosh")
    return t0

# Gancho: arranca con un zoom grande ya en el primer fotograma
cam(0, 0.5, S["s0"][0], S["s0"][1] - 40, 1.0, "expo.out")
tA = travel(T["d1"], "s0", "s1", "pA", dur=0.6, zo=False)
# Dato 1: punch-in al contador
cam(T["n90"] - 0.05, 0.5, S["s1"][0], S["s1"][1] - 20, 1.04, "power3.out")
cam(T["dia"], 0.45, *S["s1"], 1.0, "power2.inOut")
tB = travel(T["d2"], "s1", "s2", "pB")
cam(T["n475"] - 0.05, 0.5, S["s2"][0], S["s2"][1] - 40, 1.04, "power3.out")
cam(T["sumando"], 0.45, *S["s2"], 1.0)
tC = travel(T["d3"], "s2", "s3", "pC", dur=0.85)
cam(T["hoy"] - 0.05, 0.5, S["s3"][0], S["s3"][1] + 20, 1.04, "power3.out")
tD = travel(T["d4"], "s3", "s4", "pD")
cam(T["mujer"] - 0.1, 0.6, S["s4"][0], S["s4"][1] + 40, 1.04, "power3.out")
cam(T["historia"] - 0.1, 0.5, *S["s4"], 1.0)
# Clímax: vista de todo el mundo y viaje al dato más fuerte
OV = (1800, 2620, 0.25)
cam(T["pero"], 0.85, *OV, "power3.inOut", blur=4)
sfx(T["pero"] - 0.05, "whoosh")
tE = T["gta5"] - 0.7
cam(tE, 0.7, *S["s5"], 1.0, "power3.inOut", blur=6)
sfx(tE - 0.05, "whoosh")
cam(T["n230"] - 0.05, 0.5, S["s5"][0], S["s5"][1] - 30, 1.04, "power3.out")
cam(T["liston"] - 0.05, 0.45, *S["s5"], 1.0)
tF = travel(T["lo"] - 0.05, "s5", "s6", "pF", dur=0.75)
cam(T["vice2"] - 0.1, 0.5, S["s6"][0], S["s6"][1] + 20, 1.03, "power3.out")

PATH_DRAW = [("p0", 0.0, 0.7), ("pA", tA, 0.6), ("pB", tB, 0.75), ("pC", tC, 0.85),
             ("pD", tD, 0.75), ("pE", T["pero"] + 0.2, 1.2), ("pF", tF, 0.75)]

# ---------------------------------------------------------------- sonidos de cada momento
for k in ("gta",):
    sfx(0.0, "impact")
for k in ("numeros",):
    sfx(T[k], "pop")
for k in ("d1", "d2", "d3", "d4"):
    sfx(T[k] + 0.02, "pop")
sfx(T["n90"], "tick")
sfx(T["dia"], "pop")
sfx(T["lejos"], "pop")
sfx(T["rockstar"], "pop")
sfx(T["n475"], "tick")
for i in range(5):
    sfx(T["sumando"] + 0.25 + i * 0.16, "pop")
sfx(T["veces"], "pop")
sfx(T["y2025"], "pop"); sfx(T["luego"], "click"); sfx(T["mayo"], "pop"); sfx(T["final"], "click")
sfx(T["hoy"], "pop")
sfx(T["n24"], "tick")
sfx(T["lucia"], "pop"); sfx(T["jason"], "pop"); sfx(T["bonnie"], "pop")
sfx(T["bestia"], "impact")
sfx(T["gta5"] + 0.05, "pop")
sfx(T["n230"], "tick")
sfx(T["liston"], "pop")
sfx(T["superar"], "pop")
sfx(T["vas"], "pop")
sfx(T["vice2"] - 0.02, "typing")
sfx(T["vice2"] + 0.45, "click")
sfx(T["leo"], "pop")

# ---------------------------------------------------------------- utilidades HTML
def odo(oid, value, size, color="#0B0D12", start=None):
    """Contador de rodillo: cada cifra es una tira 0-9 x2 que gira."""
    lh = round(size * 1.12)
    start = start or "".join("0" if ch.isdigit() else ch for ch in value)
    out, i = [], 0
    for ch, st in zip(value, start):
        if ch.isdigit():
            digits = "".join(f"<span>{d % 10}</span>" for d in range(20))
            out.append(f'<span class="col" style="height:{lh}px"><span class="strip" id="{oid}-c{i}" '
                       f'data-to="{ch}" data-from="{st}">{digits}</span></span>')
            i += 1
        else:
            out.append(f'<span class="sep">{ch}</span>')
    return (f'<div class="odo" data-layout-ignore id="{oid}" data-lh="{lh}" data-n="{i}" '
            f'style="font-size:{size}px;line-height:{lh}px;color:{color}">{"".join(out)}</div>')

def at(st, dx, dy, w=None, h=None):
    x, y = R(st, dx, dy)
    s = f"left:{x}px;top:{y}px;"
    if w: s += f"width:{w}px;"
    if h: s += f"height:{h}px;"
    return s

def badge(st, num, color="#22C55E", ico=None):
    inner = icon(ico, 76, "#fff") if ico else f'<span>{num}</span>'
    return (f'<div class="badge" id="{st}-badge" style="{at(st, -470, -560)}">'
            f'<div class="badge-dot" id="{st}-badge-dot" style="background:{color}">{inner}</div>'
            f'<div class="badge-txt" id="{st}-badge-txt">{"DATO " + str(num) if num else "EL MÁS BESTIA"}</div></div>')

# ---------------------------------------------------------------- escenas
scenes = []

# S0 · Gancho
scenes.append(f'''
<div class="hook-gta" id="h-gta" style="{at("s0", -480, -500, 960)}">GTA</div>
<div class="hook-vi" id="h-vi" style="{at("s0", -480, -400, 960)}">VI</div>
<div class="pill green" id="h-aqui" style="{at("s0", -230, 30, 460)}">YA ESTÁ AQUÍ</div>
<div class="chip" id="h-n1" style="{at("s0", -470, -230)}">90M</div>
<div class="chip" id="h-n2" style="{at("s0", 260, -330)}">475M</div>
<div class="chip red" id="h-n3" style="{at("s0", 250, -40)}">230M</div>
''')

# S1 · Tráiler 1 en YouTube
scenes.append(badge("s1", 1) + f'''
<div class="card" id="yt-card" style="{at("s1", -460, -420, 920, 560)}">
  <div class="yt-video" id="yt-video">
    <div class="yt-label">TRÁILER 1</div>
    <div class="yt-logo" id="yt-logo">{icon("youtube-logo", 180, "#FF0033")}</div>
    <div class="yt-bar"><div class="yt-prog" id="yt-prog"></div></div>
  </div>
  <div class="yt-stats">
    <div class="yt-eye">{icon("eye", 64, "#64748B")}</div>
    {odo("o90", "90.000.000", 88)}
  </div>
  <div class="yt-sub" id="yt-sub">visitas en YouTube</div>
</div>
<div class="stamp" id="yt-24" style="{at("s1", 180, -470)}">{icon("clock", 56, "#fff")}<span>24 H</span></div>
''')

# S2 · Tráiler 2: gráfica
BAR_MAX = 330
b1 = round(BAR_MAX * 90 / 475)
scenes.append(badge("s2", 2) + f'''
<div class="card" id="ch-card" style="{at("s2", -460, -420, 920, 560)}">
  <div class="ch-title">VISTAS EN 24 H</div>
  <div class="ch-base"></div>
  <div class="bar grey" id="bar1" style="left:110px;height:{b1}px"></div>
  <div class="bar-val" id="bar1-v" style="left:60px;bottom:{110 + b1}px">90 M</div>
  <div class="bar-lab" style="left:60px">Tráiler 1</div>
  <div class="bar ghost" id="bar2g" style="left:470px;height:{BAR_MAX}px"></div>
  <div class="bar green" id="bar2" style="left:470px;height:{BAR_MAX}px"></div>
  <div class="bar-val big" id="bar2-v" style="left:420px;bottom:{116 + BAR_MAX}px">{odo("o475", "475", 76, "#16A34A")}<span class="m">M</span></div>
  <div class="bar-lab" style="left:420px">Tráiler 2</div>
</div>
<div class="pill yellow" id="ch-rock" style="{at("s2", -40, -500)}">SEGÚN ROCKSTAR</div>
''')
SOCIAL = [("youtube-logo", "#FF0033"), ("tiktok-logo", "#0B0D12"), ("instagram-logo", "#E1306C"),
          ("x-logo", "#0B0D12"), ("facebook-logo", "#1877F2")]
for i, (n, col) in enumerate(SOCIAL):
    scenes.append(f'<div class="soc" id="soc{i}" style="{at("s2", -170 + i * 130, 170)}">{icon(n, 76, col)}</div>')

# S3 · Retrasos
DATES = [("2025", "y2025"), ("26 MAYO 2026", "mayo"), ("19 NOV 2026", "noviembre")]
s3 = badge("s3", 3, "#EF4444") + f'''
<div class="big-title red" id="ret-title" style="{at("s3", -480, -430, 960)}">RETRASADO <span id="ret-x2">×2</span></div>
'''
for i, (txt, _) in enumerate(DATES):
    ico = "calendar-check" if i == 2 else "calendar-blank"
    s3 += f'''
<div class="date" id="date{i}" style="{at("s3", -470, -280 + i * 150, 660, 124)}">
  <div class="date-fill" id="date{i}-fill"></div>
  <div class="date-ico" id="date{i}-ico">{icon(ico, 70, "#0B0D12")}</div>
  <div class="date-txt" id="date{i}-txt">{txt}</div>
  <div class="date-strike" id="date{i}-strike"></div>
</div>'''
s3 += f'''<div class="pill green" id="date-hoy" style="{at("s3", 220, -140)}">¡HOY!</div>
<div class="sofa" id="sofa" style="{at("s3", 190, 330, 300, 190)}"><div class="sofa-back"></div><div class="sofa-seat"></div><div class="sofa-arm l"></div><div class="sofa-arm r"></div></div>
'''
scenes.append(s3)

# S4 · Vice City
palms = ""
for i, (px, sc) in enumerate([(70, 1.0), (760, 0.85)]):
    palms += f'''<svg class="palm" id="palm{i}" viewBox="0 0 200 400" width="{int(200*sc)}" height="{int(400*sc)}" style="left:{px}px;bottom:70px">
  <path d="M96,400 Q86,260 112,120" stroke="#1B0B2E" stroke-width="18" fill="none" stroke-linecap="round"/>
  <g id="palm{i}-top"><path d="M112,120 Q60,70 4,96 Q60,92 112,120Z M112,120 Q150,60 196,84 Q148,86 112,120Z M112,120 Q90,40 40,30 Q100,60 112,120Z M112,120 Q140,30 180,24 Q130,60 112,120Z M112,120 Q70,130 30,180 Q80,140 112,120Z M112,120 Q160,130 190,170 Q150,138 112,120Z" fill="#1B0B2E"/></g>
</svg>'''
scenes.append(badge("s4", 4, "#A855F7") + f'''
<div class="card vc" id="vc-card" style="{at("s4", -460, -420, 920, 520)}">
  <div class="vc-sky"></div>
  <div class="vc-sun" id="vc-sun"></div>
  <div class="vc-sea"><div class="vc-wave" id="vc-w1"></div><div class="vc-wave" id="vc-w2" style="top:60px"></div></div>
  {palms}
  <div class="vc-title" id="vc-title">VICE CITY</div>
  <div class="vc-year" id="vc-year">{odo("oyr", "2026", 70, "#fff", start="2002")}</div>
  <div class="pill green vc-24" id="vc-24">+24 AÑOS</div>
</div>
<div class="name purple" id="nm-lucia" style="{at("s4", -460, 120)}">LUCÍA</div>
<div class="name blue" id="nm-jason" style="{at("s4", 230, 120)}">JASON</div>
<div class="pill pink" id="nm-bc" style="{at("s4", -300, -5, 600)}">ESTILO BONNIE Y CLYDE</div>
<svg class="heart" id="heart" viewBox="0 0 200 180" width="150" height="135" style="{at("s4", -75, 200)}">
  <path id="heart-p" d="M100,170 C40,120 6,92 6,52 C6,22 30,6 56,6 C76,6 92,18 100,34 C108,18 124,6 144,6 C170,6 194,22 194,52 C194,92 160,120 100,170 Z" fill="none" stroke="#F472B6" stroke-width="14" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>
</svg>
''')

# S5 · Clímax
boxes = ""
for i in range(7):
    boxes += f'<div class="gbox" id="gb{i}" style="{at("s5", -440, 520 - 80 * (i + 1), 230, 74)}">GTA V</div>'
scenes.append(badge("s5", 0, "#EF4444", ico="fire") + f'''
<div class="ring" id="s5-ring" style="{at("s5", -720, -720, 1440, 1440)}"></div>
<div class="pill white" id="gv-chip" style="{at("s5", -230, -420, 460)}">GTA V · <span id="gv-year">2013</span></div>
<div class="climax-num" id="cx-num" style="{at("s5", -480, -300, 960)}">{odo("o230", "230.000.000", 112, "#fff")}</div>
<div class="climax-lab" id="cx-lab" style="{at("s5", -480, -165, 960)}">COPIAS VENDIDAS</div>
{boxes}
<div class="liston" id="liston" style="{at("s5", -480, -52, 960)}"></div>
<div class="pill yellow" id="liston-lab" style="{at("s5", 60, -20)}">EL LISTÓN</div>
<div class="gbox vi" id="gb-vi" style="{at("s5", -80, 446, 230, 74)}">GTA VI</div>
<div class="arrow-up" id="vi-arrow" style="{at("s5", -10, 210)}">{icon("arrow-fat-up", 96, "#22C55E")}</div>
<div class="qmark" id="vi-q" style="{at("s5", 90, 170)}">?</div>
''')

# S6 · Llamada a la acción
words6 = ["¿LO", "VAS", "A", "JUGAR", "EL", "PRIMER", "DÍA?"]
keys6 = ["lo", "vas", None, None, None, None, "primerdia"]
title6 = "".join(f'<span class="w6" id="w6-{i}">{w}</span> ' for i, w in enumerate(words6))
typed = "".join(f'<span class="tl" id="tl{i}">{ch}</span>' for i, ch in enumerate("VICE"))
scenes.append(f'''
<div class="big-title" id="cta-title" style="{at("s6", -480, -560, 960)}">{title6}</div>
<div class="card chat" id="chat" style="{at("s6", -460, -365, 920, 500)}">
  <div class="chat-head">{icon("chat-circle-dots", 64, "#0B0D12")}<span>Comentarios</span></div>
  <div class="cmt" id="cmt1"><div class="av" style="background:#F59E0B"></div><div class="bub">Día 1 sin dormir</div></div>
  <div class="cmt mine" id="cmt-me"><div class="av" style="background:#FF8A1E"></div><div class="bub green">VICE</div>
     <div class="likes" id="likes">{icon("heart", 52, "#EF4444")}{odo("olk", "999", 48, "#0B0D12")}</div></div>
  <div class="chat-input" id="chat-input"><div class="typed" id="typed">{typed}<span class="caret" id="caret"></span></div>
     <div class="ph" id="ph">Escribe…</div>
     <div class="send" id="send">{icon("paper-plane-right", 56, "#fff")}</div></div>
</div>
<div class="cursor" id="cursor" style="{at("s6", 352, 30)}">{icon("cursor", 92, "#fff", 'stroke="#0B0D12" stroke-width="10"')}</div>
''')

paths_svg = "".join(
    f'<path id="{k}" d="{d}" class="road" stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}" data-len="{L:.1f}"/>'
    for k, (d, L) in SEGS.items())
paths_glow = "".join(f'<path d="{d}" class="road-glow" id="{k}-g" stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}"/>'
                     for k, (d, L) in SEGS.items())

# partículas del fondo (paralaje)
random.seed(19)
parts = ""
for i in range(46):
    x, y = random.randint(-600, 4200), random.randint(-600, 5400)
    r = random.choice([4, 5, 6, 8])
    col = random.choice(["#FF8A1E", "#F472B6", "#22C55E", "#60A5FA", "#ffffff"])
    parts += f'<div class="pt" id="pt{i}" style="left:{x}px;top:{y}px;width:{r*2}px;height:{r*2}px;background:{col}"></div>'

chars_html = "".join(char_svg(c) for c in CHARS)

# ---------------------------------------------------------------- JS (animación)
JS = r"""
const T = __T__, DUR = T.dur;
const CAM = __CAM__, PATHS = __PATHS__, BLINKS = __BLINKS__, PIV = __PIV__, ST = __ST__;
const tl = gsap.timeline({ paused: true });
const $ = (s) => document.querySelector(s);

// ---------- cámara: un solo mundo, una sola cámara
const camW = (cx, cy, z) => ({ x: 540 - cx * z, y: 980 - cy * z, scale: z });
gsap.set("#wd", Object.assign({ transformOrigin: "0 0" }, camW(ST.s0[0], ST.s0[1] - 40, 1.45)));
gsap.set("#grid", { x: -540 * 0.5, y: -500 * 0.5 });
for (const [t, d, cx, cy, z, ease, blur] of CAM) {
  tl.to("#wd", Object.assign({ duration: d, ease }, camW(cx, cy, z)), t);
  // paralaje: la rejilla se mueve a la mitad de velocidad
  tl.to("#grid", { x: -cx * 0.5, y: -cy * 0.5, duration: d, ease }, t);
  if (blur) {
    tl.to("#wd", { filter: `blur(${blur}px)`, duration: d * 0.45, ease: "power2.in" }, t);
    tl.to("#wd", { filter: "blur(0px)", duration: d * 0.55, ease: "power2.out" }, t + d * 0.45);
  }
}
function shake(t, amp = 22, n = 8) {
  for (let i = 0; i < n; i++) {
    const a = amp * (1 - i / n);
    tl.to("#shake", { x: (i % 2 ? -a : a) * 0.8, y: (i % 3 - 1) * a * 0.6, duration: 0.04, ease: "none" }, t + i * 0.04);
  }
  tl.to("#shake", { x: 0, y: 0, duration: 0.06 }, t + n * 0.04);
}

// ---------- el camino se dibuja mientras la cámara viaja
for (const [id, t, d] of PATHS) {
  tl.to(["#" + id, "#" + id + "-g"], { strokeDashoffset: 0, duration: d, ease: "power2.inOut" }, t);
}

// ---------- personajes
for (const c of ["dani", "lucia", "jason"])
  for (const [p, o] of Object.entries(PIV)) {
    const el = $(`#${c}-${p}`);
    if (el) gsap.set(el, { svgOrigin: o });
  }
function place(c, x, y, face = 1) {
  gsap.set("#" + c, { x: x - 150, y: y - 452 });
  gsap.set("#" + c + "-flip", { scaleX: face, transformOrigin: "150px 50%" });
}
function face(c, t, f) { tl.set("#" + c + "-flip", { scaleX: f }, t); }
function breathe(c) {
  const per = 1.6, n = Math.floor(DUR / per);
  tl.fromTo(`#${c}-up`, { scaleY: 1 }, { scaleY: 1.025, duration: per / 2, ease: "sine.inOut", yoyo: true, repeat: n * 2 - 1 }, 0);
  tl.fromTo(`#${c}-head`, { rotation: -2 }, { rotation: 2, duration: per * 1.3, ease: "sine.inOut", yoyo: true, repeat: Math.floor(DUR / (per * 1.3)) - 1 }, 0.3);
}
function blinks(c) {
  for (const t of BLINKS[c]) {
    tl.to(`#${c}-eyes`, { scaleY: 0.1, duration: 0.06, ease: "power1.in" }, t);
    tl.to(`#${c}-eyes`, { scaleY: 1, duration: 0.09, ease: "power1.out" }, t + 0.06);
  }
}
// andar o correr entre puntos (pasos con piernas y brazos opuestos)
function move(c, t, pts, dur, run = true) {
  const per = run ? 0.26 : 0.46, amp = run ? 34 : 22;
  let L = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(l); L += l; }
  let tt = t;
  for (let i = 1; i < pts.length; i++) {
    const d = dur * seg[i - 1] / L;
    tl.to("#" + c, { x: pts[i][0] - 150, y: pts[i][1] - 452, duration: d, ease: i === pts.length - 1 ? "power2.out" : "none" }, tt);
    tt += d;
  }
  const n = Math.max(1, Math.round(dur / per));
  const legs = { duration: per / 2, ease: "sine.inOut", yoyo: true, repeat: n * 2 - 1 };
  tl.fromTo(`#${c}-legL`, { rotation: amp }, Object.assign({ rotation: -amp }, legs), t);
  tl.fromTo(`#${c}-legR`, { rotation: -amp }, Object.assign({ rotation: amp }, legs), t);
  tl.fromTo(`#${c}-armF`, { rotation: -amp * 1.1 }, Object.assign({ rotation: amp * 1.1 }, legs), t);
  tl.fromTo(`#${c}-armB`, { rotation: amp * 1.1 }, Object.assign({ rotation: -amp * 1.1 }, legs), t);
  tl.fromTo(`#${c}-body`, { y: 0 }, { y: -14, duration: per / 4, ease: "sine.out", yoyo: true, repeat: n * 4 - 1 }, t);
  tl.to(`#${c}-up`, { rotation: run ? 8 : 3, duration: 0.15 }, t);
  const end = t + dur;
  tl.to([`#${c}-legL`, `#${c}-legR`, `#${c}-armF`, `#${c}-armB`], { rotation: 0, duration: 0.18, ease: "power2.out" }, end);
  tl.to(`#${c}-body`, { y: 0, duration: 0.1 }, end);
  tl.to(`#${c}-up`, { rotation: 0, duration: 0.25, ease: "back.out(2)" }, end);
  return end;
}
function arm(c, t, which, rot, d = 0.3, ease = "back.out(1.6)") { tl.to(`#${c}-arm${which}`, { rotation: rot, duration: d, ease }, t); }
function surprise(c, t, hold = 1.0) {
  tl.to(`#${c}-mouthO`, { attr: { ry: 16 }, duration: 0.15, ease: "back.out(3)" }, t);
  tl.to(`#${c}-mouth`, { opacity: 0, duration: 0.05 }, t);
  tl.to(`#${c}-eyes`, { scale: 1.25, duration: 0.15, ease: "back.out(3)" }, t);
  tl.to(`#${c}-brows`, { y: -10, duration: 0.15 }, t);
  tl.to(`#${c}-mouthO`, { attr: { ry: 0.1 }, duration: 0.2 }, t + hold);
  tl.to(`#${c}-mouth`, { opacity: 1, duration: 0.05 }, t + hold + 0.1);
  tl.to(`#${c}-eyes`, { scale: 1, duration: 0.25 }, t + hold);
  tl.to(`#${c}-brows`, { y: 0, duration: 0.25 }, t + hold);
}
function hop(c, t, h = 60) {
  tl.to(`#${c}-body`, { scaleY: 0.86, duration: 0.08, ease: "power2.in" }, t);
  tl.to(`#${c}-body`, { scaleY: 1.06, y: -h, duration: 0.2, ease: "power2.out" }, t + 0.08);
  tl.to(`#${c}-body`, { scaleY: 1, y: 0, duration: 0.2, ease: "power2.in" }, t + 0.28);
  tl.to(`#${c}-body`, { scaleY: 0.92, duration: 0.06 }, t + 0.48);
  tl.to(`#${c}-body`, { scaleY: 1, duration: 0.12 }, t + 0.54);
}
for (const c of ["dani", "lucia", "jason"]) { breathe(c); blinks(c); }

// ---------- pop genérico (aparece creciendo en su sitio)
function pop(sel, t, d = 0.45, from = 0.4) {
  tl.fromTo(sel, { opacity: 0, scale: from }, { opacity: 1, scale: 1, duration: d, ease: "back.out(1.8)" }, t);
}
function hidden(sel) { tl.set(sel, { opacity: 0 }, 0); }
function roll(id, t, dur = 1.1) {
  const el = $("#" + id), lh = +el.dataset.lh, n = +el.dataset.n;
  for (let i = 0; i < n; i++) {
    const s = $(`#${id}-c${i}`), to = +s.dataset.to, fr = +s.dataset.from;
    gsap.set(s, { y: -fr * lh });
    tl.to(s, { y: -(10 + to) * lh, duration: dur + 0.07 * i, ease: "power3.out" }, t);
  }
}

// ================= S0 · GANCHO =================
tl.fromTo("#h-vi", { scale: 1.6, opacity: 1 }, { scale: 1, duration: 0.45, ease: "expo.out" }, 0);
tl.fromTo("#h-gta", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }, T.gta + 0.05);
shake(0.38, 18, 6);
place("dani", ST.s0[0] - 760, 1520, 1);
move("dani", 0.05, [[ST.s0[0] - 760, 1520], [ST.s0[0] - 250, 1520]], 0.7);
tl.to("#dani-up", { rotation: -10, duration: 0.12 }, 0.75).to("#dani-up", { rotation: 0, duration: 0.3, ease: "back.out(3)" }, 0.87);
hidden("#h-aqui"); pop("#h-aqui", T.aqui);
hidden(["#h-n1", "#h-n2", "#h-n3"]);
["#h-n1", "#h-n2", "#h-n3"].forEach((s, i) => pop(s, T.numeros + i * 0.12, 0.4, 0.2));
tl.fromTo(["#h-n1", "#h-n2", "#h-n3"], { rotation: -6 }, { rotation: 6, duration: 0.18, ease: "sine.inOut", yoyo: true, repeat: 3 }, T.miedo);
tl.to("#h-vi", { color: "#EF4444", duration: 0.2 }, T.miedo);
shake(T.miedo, 14, 6);
surprise("dani", T.miedo, 0.5);
tl.fromTo("#dani-flip", { x: -4 }, { x: 4, duration: 0.05, yoyo: true, repeat: 7, ease: "none" }, T.miedo);
// sale corriendo a la siguiente escena
move("dani", T.d1 - 0.62, [[ST.s0[0] - 250, 1520], [ST.s1[0] + 360, 1520]], 0.8);
face("dani", T.d1 + 0.2, -1);

// ================= S1 · TRÁILER 1 =================
const badgeIn = (s, t) => {
  hidden([`#${s}-badge-dot`, `#${s}-badge-txt`]);
  tl.fromTo(`#${s}-badge-dot`, { opacity: 0, scale: 0, rotation: -90 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.5, ease: "back.out(2)" }, t);
  tl.fromTo(`#${s}-badge-txt`, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.35, ease: "power3.out" }, t + 0.1);
};
badgeIn("s1", T.d1);
hidden("#yt-card"); pop("#yt-card", T.primer - 0.1, 0.5, 0.6);
tl.fromTo("#yt-logo", { scale: 0.6 }, { scale: 1, duration: 0.5, ease: "back.out(2.5)" }, T.trailer1);
tl.fromTo("#yt-prog", { scaleX: 0 }, { scaleX: 1, duration: T.d2 - T.trailer1, ease: "none" }, T.trailer1);
roll("o90", T.n90, 1.0);
tl.fromTo("#yt-sub", { opacity: 0 }, { opacity: 1, duration: 0.3 }, T.youtube - 0.25);
hidden("#yt-24");
tl.fromTo("#yt-24", { opacity: 0, scale: 2.2, rotation: -30 }, { opacity: 1, scale: 1, rotation: -8, duration: 0.4, ease: "back.out(1.6)" }, T.dia);
arm("dani", T.n90 - 0.1, "F", -115);
arm("dani", T.dia + 0.25, "F", 0, 0.3, "power2.inOut");
move("dani", T.d2 - 0.75, [[ST.s1[0] + 360, 1520], [ST.s2[0] - 360, 1520]], 0.85);
face("dani", T.d2 - 0.75, 1);

// ================= S2 · TRÁILER 2 =================
badgeIn("s2", T.d2);
hidden("#ch-card");
tl.fromTo("#ch-card", { opacity: 0, scale: 0.5, x: -200 }, { opacity: 1, scale: 1, x: 0, duration: 0.6, ease: "back.out(1.4)" }, T.segundo);
tl.fromTo("#bar1", { scaleY: 0 }, { scaleY: 1, duration: 0.5, ease: "power3.out" }, T.segundo + 0.2);
hidden("#bar1-v"); pop("#bar1-v", T.segundo + 0.5);
tl.fromTo("#bar2g", { scaleY: 0, opacity: 0 }, { scaleY: 1, opacity: 1, duration: 0.5, ease: "power3.out" }, T.lejos);
hidden("#ch-rock");
tl.fromTo("#ch-rock", { opacity: 0, y: -40, rotation: 8 }, { opacity: 1, y: 0, rotation: -3, duration: 0.4, ease: "back.out(2)" }, T.rockstar);
tl.fromTo("#bar2", { scaleY: 0 }, { scaleY: 1, duration: 1.1, ease: "power3.out" }, T.n475);
hidden("#bar2-v"); tl.to("#bar2-v", { opacity: 1, duration: 0.15 }, T.n475);
roll("o475", T.n475, 1.0);
for (let i = 0; i < 5; i++) {
  hidden("#soc" + i);
  tl.fromTo("#soc" + i, { opacity: 0, y: -900, rotation: (i - 2) * 25 }, { opacity: 1, y: 0, rotation: 0, duration: 0.55, ease: "bounce.out" }, T.sumando + 0.1 + i * 0.16);
}
surprise("dani", T.redes, 1.4);
arm("dani", T.redes, "F", -165, 0.3); arm("dani", T.redes, "B", 165, 0.3);
arm("dani", T.redes + 1.0, "F", 0, 0.3, "power2.inOut"); arm("dani", T.redes + 1.0, "B", 0, 0.3, "power2.inOut");
hop("dani", T.redes);
// corre por el camino hasta el sofá
const sofaX = ST.s3[0] + 340;
move("dani", T.d3 - 0.55, [[ST.s2[0] - 360, 1520], [3500, 1520], [3500, 3120], [sofaX, 3120]], 1.35);
face("dani", T.d3 + 0.85, -1);

// ================= S3 · RETRASOS =================
badgeIn("s3", T.d3);
hidden("#ret-title");
tl.fromTo("#ret-title", { opacity: 0, scale: 1.4 }, { opacity: 1, scale: 1, duration: 0.35, ease: "power4.out" }, T.retrasado);
hidden("#ret-x2"); pop("#ret-x2", T.veces, 0.4, 2.2);
// Dani se sienta en el sofá y espera impaciente
const sitT = T.d3 + 0.9;
tl.to("#dani-body", { y: 70, duration: 0.25, ease: "power2.in" }, sitT);
tl.to("#dani-legL", { rotation: -80, duration: 0.25 }, sitT);
tl.to("#dani-legR", { rotation: -70, duration: 0.25 }, sitT);
tl.fromTo("#dani-legR", { rotation: -70 }, { rotation: -50, duration: 0.14, yoyo: true, repeat: Math.max(1, Math.floor((T.hoy - sitT - 0.6) / 0.14)), ease: "sine.inOut" }, sitT + 0.3);
const dts = [T.primero, T.luego, T.final + 0.1];
hidden(["#date0-fill", "#date1-fill", "#date2-strike"]);
for (let i = 0; i < 3; i++) { hidden("#date" + i); tl.fromTo("#date" + i, { opacity: 0, x: -120 }, { opacity: 1, x: 0, duration: 0.4, ease: "power3.out" }, dts[i]); }
const strike = (i, t) => {
  tl.fromTo(`#date${i}-strike`, { scaleX: 0, rotation: -3 }, { scaleX: 1, rotation: -3, duration: 0.3, ease: "power3.inOut" }, t);
  tl.to(`#date${i}`, { backgroundColor: "#FEE2E2", duration: 0.25 }, t);
  tl.to(`#date${i}-txt`, { color: "#B91C1C", duration: 0.25 }, t);
};
strike(0, T.luego); strike(1, T.final);
tl.fromTo("#date2-fill", { scaleX: 0 }, { scaleX: 1, duration: 0.45, ease: "power3.inOut" }, T.hoy);
tl.to(["#date2-txt"], { color: "#fff", duration: 0.2 }, T.hoy + 0.1);
tl.to("#date2-ico svg", { fill: "#fff", duration: 0.2 }, T.hoy + 0.1);
hidden("#date-hoy"); pop("#date-hoy", T.hoy + 0.1, 0.45, 0.2);
// ¡hoy! se levanta de un salto
tl.to("#dani-body", { y: 0, duration: 0.2, ease: "power2.out" }, T.hoy);
tl.to(["#dani-legL", "#dani-legR"], { rotation: 0, duration: 0.2 }, T.hoy);
hop("dani", T.hoy + 0.2, 80);
arm("dani", T.hoy + 0.2, "F", -170); arm("dani", T.hoy + 0.2, "B", 170);
arm("dani", T.y2026 + 0.6, "F", 0, 0.3, "power2.inOut"); arm("dani", T.y2026 + 0.6, "B", 0, 0.3, "power2.inOut");

// ================= S4 · VICE CITY =================
badgeIn("s4", T.d4);
hidden("#vc-card"); pop("#vc-card", T.volvemos - 0.1, 0.5, 0.7);
tl.fromTo("#vc-sun", { y: 40 }, { y: 120, duration: T.pero - T.volvemos, ease: "none" }, T.volvemos);
tl.fromTo("#vc-w1", { x: 0 }, { x: -120, duration: T.pero - T.volvemos, ease: "none" }, T.volvemos);
tl.fromTo("#vc-w2", { x: -120 }, { x: 0, duration: T.pero - T.volvemos, ease: "none" }, T.volvemos);
for (let i = 0; i < 2; i++)
  tl.fromTo(`#palm${i}-top`, { rotation: -3 }, { rotation: 3, svgOrigin: "112 120", duration: 1.4 + i * 0.3, ease: "sine.inOut", yoyo: true, repeat: 7 }, T.volvemos);
hidden("#vc-title");
tl.fromTo("#vc-title", { opacity: 0, scaleX: 1.5, filter: "blur(8px)" }, { opacity: 1, scaleX: 1, filter: "blur(0px)", duration: 0.5, ease: "power3.out" }, T.vice);
hidden("#vc-year"); tl.to("#vc-year", { opacity: 1, duration: 0.2 }, T.n24 - 0.2);
roll("oyr", T.n24, 0.9);
hidden("#vc-24"); pop("#vc-24", T.anos);
place("lucia", ST.s4[0] - 700, 3120, 1);
place("jason", ST.s4[0] + 700, 3120, -1);
hidden("#jason"); tl.to("#jason", { opacity: 1, duration: 0.01 }, T.d4);
move("lucia", T.primera, [[ST.s4[0] - 700, 3120], [ST.s4[0] - 170, 3120]], 1.5, false);
hidden("#nm-lucia");
tl.fromTo("#nm-lucia", { opacity: 0, scale: 0.3 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }, T.lucia);
tl.to("#nm-lucia", { backgroundColor: "#22C55E", duration: 0.25 }, T.lucia + 0.1);
arm("lucia", T.lucia, "B", 160); arm("lucia", T.lucia + 0.6, "B", 0, 0.3, "power2.inOut");
hop("lucia", T.lucia, 30);
move("jason", T.jason - 0.5, [[ST.s4[0] + 700, 3120], [ST.s4[0] + 170, 3120]], 1.2, false);
hidden("#nm-jason");
tl.fromTo("#nm-jason", { opacity: 0, scale: 0.3 }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(2)" }, T.jason);
// choque de puños
arm("lucia", T.historia - 0.1, "F", -84, 0.25); arm("jason", T.historia - 0.1, "F", -84, 0.25);
tl.to(["#lucia", "#jason"], { x: (i) => (i ? ST.s4[0] + 150 : ST.s4[0] - 150) - 150, duration: 0.2, ease: "power2.out" }, T.historia - 0.1);
arm("lucia", T.bonnie + 0.3, "F", 0, 0.35, "power2.inOut"); arm("jason", T.bonnie + 0.3, "F", 0, 0.35, "power2.inOut");
tl.to("#heart-p", { strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }, T.bonnie);
tl.fromTo("#heart", { scale: 0.8 }, { scale: 1.08, duration: 0.3, yoyo: true, repeat: 3, ease: "sine.inOut" }, T.bonnie + 0.7);
hidden("#nm-bc"); pop("#nm-bc", T.bonnie);

// ================= CLÍMAX =================
hidden("#s5-ring");
tl.fromTo("#s5-ring", { opacity: 0, scale: 0.2 }, { opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" }, T.bestia);
tl.to("#s5-ring", { opacity: 0, duration: 0.4 }, T.bestia + 0.5);
badgeIn("s5", T.bestia);
shake(T.bestia, 26, 9);
// Dani cruza el mapa corriendo hasta el clímax
face("dani", T.pero, -1);
move("dani", T.pero + 0.15, [[sofaX, 3120], [ST.s5[0] + 360, 3120]], 1.4);
hidden("#gv-chip"); pop("#gv-chip", T.gta5 + 0.05);
tl.fromTo("#gv-year", { color: "#0B0D12" }, { color: "#16A34A", duration: 0.2 }, T.y2013);
hidden(["#cx-num", "#cx-lab"]);
tl.fromTo("#cx-num", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }, T.vendido - 0.1);
roll("o230", T.n230, 1.1);
tl.fromTo("#cx-lab", { opacity: 0 }, { opacity: 1, duration: 0.3 }, T.copias);
const boxT0 = T.vendido, boxStep = (T.copias + 0.4 - T.vendido) / 7;
for (let i = 0; i < 7; i++) {
  hidden("#gb" + i);
  tl.fromTo("#gb" + i, { opacity: 0, y: -500 }, { opacity: 1, y: 0, duration: 0.35, ease: "bounce.out" }, boxT0 + i * boxStep);
}
tl.fromTo("#liston", { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: "power3.inOut" }, T.liston);
hidden("#liston-lab"); pop("#liston-lab", T.liston + 0.1);
hidden("#gb-vi"); pop("#gb-vi", T.gta6b, 0.45, 0.2);
hidden(["#vi-arrow", "#vi-q"]);
tl.fromTo("#vi-arrow", { opacity: 0, y: 120 }, { opacity: 1, y: -60, duration: 0.6, ease: "power3.out" }, T.superar);
pop("#vi-q", T.superar + 0.2, 0.4, 0.2);
arm("dani", T.superar - 0.1, "F", -175);
face("dani", T.superar - 0.1, -1);
move("dani", T.lo - 0.85, [[ST.s5[0] + 360, 3120], [200, 3120], [100, 3220], [100, 4620], [200, 4720], [ST.s6[0] - 390, 4720]], 1.3);
arm("dani", T.lo - 0.85, "F", 0, 0.1);
face("dani", T.lo - 0.85, -1);
face("dani", T.lo - 0.6, 1);

// ================= S6 · LLAMADA A LA ACCIÓN =================
const w6 = __W6__;
w6.forEach((t, i) => { hidden("#w6-" + i); tl.fromTo("#w6-" + i, { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.15 }, t); });
hidden("#chat"); pop("#chat", T.vas, 0.5, 0.7);
hidden("#cmt1"); tl.fromTo("#cmt1", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.35, ease: "power3.out" }, T.primerdia);
hidden("#cmt-me");
hidden(["#tl0", "#tl1", "#tl2", "#tl3", "#typed"]);
tl.to("#typed", { opacity: 1, duration: 0.01 }, T.comenta);
tl.to("#ph", { opacity: 0, duration: 0.15 }, T.comenta);
tl.fromTo("#caret", { opacity: 1 }, { opacity: 0, duration: 0.25, yoyo: true, repeat: 7, ease: "steps(1)" }, T.comenta);
for (let i = 0; i < 4; i++) tl.to("#tl" + i, { opacity: 1, duration: 0.01 }, T.vice2 + i * 0.07);
hidden("#cursor");
tl.fromTo("#cursor", { opacity: 0, x: 120, y: 160 }, { opacity: 1, x: 0, y: 0, duration: 0.4, ease: "power3.out" }, T.vice2 + 0.05);
tl.to("#cursor", { scale: 0.8, duration: 0.07 }, T.vice2 + 0.45).to("#cursor", { scale: 1, duration: 0.12 }, T.vice2 + 0.52);
tl.to("#send", { scale: 0.85, duration: 0.07 }, T.vice2 + 0.45).to("#send", { scale: 1, duration: 0.2, ease: "back.out(3)" }, T.vice2 + 0.52);
tl.to("#typed", { opacity: 0, duration: 0.1 }, T.vice2 + 0.5);
tl.fromTo("#cmt-me", { opacity: 0, y: 80, scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.8)" }, T.vice2 + 0.5);
roll("olk", T.vice2 + 0.55, 0.3);
arm("dani", T.comenta, "B", 125, 0.3);
tl.fromTo("#dani-armB", { rotation: 125 }, { rotation: 95, duration: 0.18, yoyo: true, repeat: 5, ease: "sine.inOut" }, T.comenta + 0.3);
arm("dani", T.leo, "F", -110);

// ---------- vida en el fondo
document.querySelectorAll(".pt").forEach((p, i) => {
  const per = 2.4 + (i % 5) * 0.5;
  tl.fromTo(p, { y: 0, opacity: 0.25 }, { y: -40 - (i % 4) * 15, opacity: 0.7, duration: per, ease: "sine.inOut", yoyo: true, repeat: Math.floor(DUR / per) - 1 }, (i % 7) * 0.2);
});
tl.fromTo("#glow", { opacity: 0.75, scale: 1 }, { opacity: 1, scale: 1.08, duration: 2.5, ease: "sine.inOut", yoyo: true, repeat: Math.floor(DUR / 2.5) - 1 }, 0);

window.__timelines["world"] = tl;
"""

w6_times = [T["lo"], T["vas"], T["vas"] + 0.08, P("jugar"), P("el", after=P("jugar")), P("primer", 2), T["primerdia"]]
js = (JS.replace("__T__", json.dumps(T)).replace("__CAM__", json.dumps(CAM))
      .replace("__PATHS__", json.dumps([[k, round(t, 3), d] for k, t, d in PATH_DRAW]))
      .replace("__BLINKS__", json.dumps(BLINKS)).replace("__PIV__", json.dumps(CHAR_PIVOTS))
      .replace("__ST__", json.dumps(S)).replace("__W6__", json.dumps(w6_times)))

CSS = open(os.path.join(HERE, "world.css")).read()

world_html = f'''<template>
<style>
{CSS}
</style>
<div id="root" data-composition-id="world" data-width="{W}" data-height="{H}" data-layout-allow-overflow>
  <div id="bg"></div>
  <div id="gridwrap" data-layout-ignore><div id="grid">{parts}</div></div>
  <div id="glow"></div>
  <div id="shake">
   <div id="wd" style="width:{WORLD_W}px;height:{WORLD_H}px" data-layout-allow-overflow data-layout-allow-overlap>
    <svg id="roads" width="{WORLD_W}" height="{WORLD_H}" viewBox="0 0 {WORLD_W} {WORLD_H}" overflow="visible">{paths_glow}{paths_svg}</svg>
    {"".join(scenes)}
    {chars_html}
   </div>
  </div>
  <div id="vignette"></div>
</div>
<script>
{js}
</script>
</template>
'''

# ---------------------------------------------------------------- subtítulos
KEY_GOOD = {"gta", "6", "90", "youtube", "475", "rockstar", "redes", "hoy", "19", "noviembre", "vice", "city",
            "24", "lucia", "jason", "mujer", "bonnie", "clyde", "230", "copias", "liston", "superar", "comenta",
            "2013", "5", "millones", "aqui", "dia", "1", "2", "3", "4", "primer", "segundo", "historia", "primera"}
KEY_BAD = {"miedo", "retrasado", "veces", "2025", "mayo", "bestia", "26"}
PRIO = ["vice", "comenta", "bestia", "miedo", "retrasado", "lucia", "jason", "bonnie", "clyde", "youtube", "rockstar",
        "liston", "superar", "hoy", "redes", "copias", "mujer", "city", "aqui", "historia"]

def cap_text(t):
    t = re.sub(r"[.,;:]+$", "", t)
    return t.upper()

groups, cur = [], []
for i, w in enumerate(WORDS):
    cur.append(w)
    nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
    end_sent = bool(re.search(r"[.,!?;:]$", w["text"]))
    gap = (nxt["start"] - w["end"]) if nxt else 1
    if not nxt or len(cur) >= 4 or (end_sent and len(cur) >= 2) or (gap >= 0.15 and len(cur) >= 2) or \
       (end_sent and len(cur) == 1 and nxt and re.search(r"[.?!]$", w["text"])):
        groups.append(cur); cur = []
if cur:
    groups.append(cur)
# no dejar grupos de una sola palabra si se pueden unir
merged = []
for g in groups:
    if merged and len(g) == 1 and len(merged[-1]) < 4 and not re.search(r"[.?!]$", merged[-1][-1]["text"]):
        merged[-1] += g
    else:
        merged.append(g)
groups = merged

cap_html, cap_js = [], []
for gi, g in enumerate(groups):
    # palabra clave del grupo
    best, bscore = None, 99
    for wi, w in enumerate(g):
        k = w["n"]
        if k in KEY_GOOD or k in KEY_BAD:
            sc = PRIO.index(k) if k in PRIO else (20 if k.isdigit() else 30)
            if sc < bscore:
                best, bscore = wi, sc
    txt = " ".join(cap_text(w["text"]) for w in g)
    fs = 74
    est = len(txt) * 0.66 * fs
    if est > 940:
        fs = max(54, int(940 / (len(txt) * 0.66)))
    spans = []
    for wi, w in enumerate(g):
        cls = "cw"
        if wi == best:
            cls += " key bad" if w["n"] in KEY_BAD else " key"
        spans.append(f'<span class="{cls}" id="cw{gi}_{wi}">{cap_text(w["text"])}</span>')
    t0 = max(0.1, g[0]["start"] - 0.05)
    t1 = groups[gi + 1][0]["start"] - 0.05 if gi + 1 < len(groups) else DUR - 0.05
    t1 = max(t1, g[-1]["end"])
    t1 = min(t1, DUR - 0.02)
    cap_html.append(f'<div class="cg" id="cg{gi}" style="font-size:{fs}px">{" ".join(spans)}</div>')
    cap_js.append([gi, round(t0, 3), round(t1, 3), [round(w["start"], 3) for w in g], best])

captions_html = f'''<template>
<style>
#root {{ position:absolute; inset:0; pointer-events:none; }}
.cg {{ position:absolute; left:0; right:0; top:250px; text-align:center; font-family:Inter, sans-serif;
       font-weight:900; color:#fff; letter-spacing:-1px; line-height:1.15; padding:0 70px; opacity:0;
       text-shadow:0 6px 0 rgba(0,0,0,.55), 0 0 24px rgba(0,0,0,.6); }}
.cw {{ display:inline-block; padding:2px 6px; opacity:0; }}
.cw.key {{ background:#22C55E; color:#06210f; border-radius:14px; padding:2px 18px; text-shadow:none;
           box-shadow:0 8px 0 rgba(0,0,0,.35); }}
.cw.key.bad {{ background:#EF4444; color:#fff; }}
</style>
<div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">
{"".join(cap_html)}
</div>
<script>
const G = {json.dumps(cap_js)};
const tl = gsap.timeline({{ paused: true }});
for (const [gi, t0, t1, ws, key] of G) {{
  const g = "#cg" + gi;
  tl.set(g, {{ opacity: 1, visibility: "visible" }}, t0);
  ws.forEach((t, wi) => {{
    const w = `#cw${{gi}}_${{wi}}`;
    if (wi === key) tl.fromTo(w, {{ opacity: 0, scale: 0.6, rotation: -4 }}, {{ opacity: 1, scale: 1, rotation: -2, duration: 0.22, ease: "back.out(2.5)" }}, Math.max(t0, t - 0.03));
    else tl.fromTo(w, {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.12, ease: "power2.out" }}, Math.max(t0, t - 0.03));
  }});
  tl.to(g, {{ opacity: 0, duration: 0.08, ease: "power2.in" }}, t1 - 0.08);
  tl.set(g, {{ opacity: 0, visibility: "hidden" }}, t1);
}}
window.__timelines["captions"] = tl;
</script>
</template>
'''

# ---------------------------------------------------------------- índice + audio
SFX_FILES = {
    "whoosh": [("assets/sfx/mk_1489.mp3", 0.55), ("assets/sfx/mk_1492.mp3", 0.55), ("assets/sfx/mk_1491.mp3", 0.55)],
    "pop": [("assets/sfx/mk_2354.mp3", 0.45), ("assets/sfx/mk_2358.mp3", 0.45), ("assets/sfx/mk_2364.mp3", 0.45)],
    "click": [("assets/sfx/mk_1133.mp3", 0.7)],
    "tick": [("assets/sfx/mk_1109.mp3", 0.4)],
    "typing": [("assets/sfx/mk_1386.mp3", 0.5)],
    "impact": [("assets/sfx/mk_1143.mp3", 0.8)],
}
SFX_DUR = {"whoosh": 1.1, "pop": 0.47, "click": 0.39, "tick": 0.8, "typing": 0.55, "impact": 2.2}
SFX.sort()
rot = {k: 0 for k in SFX_FILES}
audio_tags, lanes_end = [], []
for i, (t, k) in enumerate(SFX):
    files = SFX_FILES[k]
    f, vol = files[rot[k] % len(files)]
    rot[k] += 1
    t = max(0.0, t)
    d = min(SFX_DUR[k], DUR - t - 0.01)
    if d <= 0.05:
        continue
    lane = next((li for li, e in enumerate(lanes_end) if e <= t), None)
    if lane is None:
        lanes_end.append(0); lane = len(lanes_end) - 1
    lanes_end[lane] = t + d
    extra = ' data-media-start="2.0"' if k == "typing" else ""
    audio_tags.append(f'<audio id="sfx{i}" class="clip" src="{f}" data-start="{t:.3f}" data-duration="{d:.3f}" '
                      f'data-track-index="{10 + lane}" data-volume="{vol}"{extra}></audio>')

index_html = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={H}" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#07090D; }}
#root {{ width:100%; height:100%; position:relative; font-family:Inter, sans-serif; background:#07090D; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="{W}" data-height="{H}">
  <div id="world" data-composition-id="world" data-composition-src="compositions/world.html" data-start="0"
       data-duration="{DUR:.3f}" data-track-index="1" data-track-kind="graphics" data-width="{W}" data-height="{H}"></div>
  {"" if NO_SUBS else f'<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{DUR:.3f}" data-track-index="2" data-track-kind="captions" data-width="{W}" data-height="{H}"></div>'}
  <audio id="voz" class="clip" src="assets/voz.wav" data-start="0" data-duration="{DUR:.3f}" data-track-index="3" data-volume="1"></audio>
  <audio id="musica" class="clip" src="assets/music/musica.mp3" data-start="0" data-duration="{DUR:.3f}" data-track-index="4"
         data-volume="0.11" data-fade-in="0.4" data-fade-out="1.5"></audio>
  {chr(10).join(audio_tags)}
</div>
<script>
window.__timelines["main"] = gsap.timeline({{ paused: true }});
</script>
</body>
</html>
'''

os.makedirs(os.path.join(HERE, "compositions"), exist_ok=True)
open(os.path.join(HERE, "compositions/world.html"), "w").write(world_html)
open(os.path.join(HERE, "compositions/captions.html"), "w").write(captions_html)
open(os.path.join(HERE, "index.html"), "w").write(index_html)
json.dump({"T": T, "groups": [[w["text"] for w in g] for g in groups]}, open(os.path.join(HERE, "cues.json"), "w"),
          ensure_ascii=False, indent=1)
print(f"[gen] OK · duración {DUR:.3f}s · {len(WORDS)} palabras · {len(groups)} grupos de subtítulos · "
      f"{len(audio_tags)} efectos · subtítulos={'no' if NO_SUBS else 'sí'}")
