#!/usr/bin/env python3
"""Generate a 10-slide investor pitch template from the SEE Pakistan bootcamp rules.

Edit COMPANY below, then run:

    python3 talks/2026-see-pakistan-pitch-deck/generate_pitch_deck.py

Writes YOUR-PITCH-DECK.pptx and pitch-preview.html in this folder.
Cursor cannot preview .pptx; open pitch-preview.html in a browser instead.
"""

from html import escape
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt


# --- Fill this in with the real company. Bracketed lines are prompts. -----
COMPANY = {
    "name": "[Company name]",
    "one_breath": (
        "[Customer] uses [product] to [job], so they get [outcome]. "
        "Example of strong: Clinic software that brings appointments, EMR, billing and pharmacy into one system."
    ),
    "problem_person": "[Who feels the pain — a specific person, not an industry]",
    "problem": (
        "[Person] + [painful situation] + [consequence]. "
        "Example: Independent clinics manage patient records, billing and inventory across paper registers and disconnected software."
    ),
    "before": "Fragmented: paper, email, spreadsheets, disconnected tools.",
    "product": "[What the product actually is in one line]",
    "after": "Integrated: one workflow, one source of truth, a measurable outcome.",
    "why_now": (
        "[What changed: regulation, behavior, infrastructure, AI, costs, or distribution — and why that makes this timely.]"
    ),
    "bad_tam_label": '"[Huge market slogan]"',
    "bad_tam": "$X T",
    "units": "[40,000 target customers]",
    "price": "[PKR 15K monthly ACV]",
    "opportunity": "[PKR 7.2B annual opportunity]",
    "beachhead": "[The first segment you can actually acquire this year.]",
    "who_pays": "[The buyer who writes the cheque]",
    "how_much": "[Price / unit]",
    "how_often": "[Recurring subscription / usage / contract]",
    "gtm_steps": ["Awareness", "Demo", "Pilot", "Contract", "Referral / expansion"],
    "gtm_engine": "[How customer #1 becomes customer #1,000 — a repeatable motion, not a hope.]",
    "rivals": [
        ("Do nothing", "Zero switching cost"),
        ("[Excel / WhatsApp / status quo]", "Cheap, familiar, already adopted"),
        ("[Legacy tool]", "Embedded in the current workflow"),
        ("[Named competitor]", "What they actually own"),
    ],
    "advantage": (
        "[Why the advantage compounds: distribution, data, workflow lock-in, network effects, brand, or cost.]"
    ),
    "team_evidence": [
        "Built [X]",
        "Scaled [Y]",
        "Sold to [Z] / industry access: [who]",
        "Proprietary insight: [what you know from the market]",
    ],
    "raise_amount": "[Amount being raised]",
    "runway": "[Runway this creates]",
    "milestones": "[Milestones the round unlocks]",
    "capital_changes": "[What is different after the money lands]",
    "want_next": "[The specific next step you want from this investor]",
    "traction": [
        "[Paying customers / pilots / revenue / waitlist — one real number]",
        "[Retention, usage, or a customer quote]",
        "[Time to value or a before/after metric]",
        "[If early: evidence of demand, not logos for decoration]",
    ],
}


INK = RGBColor(0x14, 0x14, 0x14)
MUTED = RGBColor(0x5C, 0x5C, 0x5C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PAPER = RGBColor(0xF7, 0xF5, 0xF1)
WEAK = RGBColor(0xF8, 0xE8, 0xEA)
STRONG = RGBColor(0xE4, 0xF1, 0xF4)
TEAL = RGBColor(0x0F, 0x6E, 0x62)
ORANGE = RGBColor(0xC4, 0x5A, 0x12)
RED = RGBColor(0xC4, 0x34, 0x2A)
LINE = RGBColor(0xE6, 0xE6, 0xE6)
BLACK = RGBColor(0x11, 0x11, 0x11)
LIGHT = RGBColor(0xFA, 0xFA, 0xFA)

W = Inches(13.333)
H = Inches(7.5)
FONT = "Calibri"


def _set_shape_fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def _disable_shadow(shape):
    sp_pr = shape._element.spPr
    effect = sp_pr.find(qn("a:effectLst"))
    if effect is not None:
        sp_pr.remove(effect)


def _set_run(paragraph, text, *, size, color, bold=False):
    paragraph.clear()
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = FONT
    run.font.bold = bold
    rpr = run._r.get_or_add_rPr()
    latin = rpr.find(qn("a:latin"))
    if latin is None:
        latin = etree.SubElement(rpr, qn("a:latin"))
    latin.set("typeface", FONT)
    return run


def add_textbox(slide, left, top, width, height, text, *, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t", MSO_ANCHOR.MIDDLE: "ctr", MSO_ANCHOR.BOTTOM: "b"}[anchor])
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    _set_run(p, text, size=size, color=color, bold=bold)
    return box


def add_rect(slide, left, top, width, height, color, *, radius=None):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(left), Inches(top), Inches(width), Inches(height))
    _set_shape_fill(shape, color)
    _disable_shadow(shape)
    if radius is not None:
        try:
            shape.adjustments[0] = radius
        except Exception:
            pass
    return shape


def paint(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = PAPER
    add_rect(slide, 0, 0, 0.09, 7.5, TEAL)


def add_kicker(slide, text):
    add_textbox(slide, 0.48, 0.28, 12.2, 0.28, text.upper(), size=11, color=MUTED, bold=True)


def add_title(slide, text, *, top=0.52, size=28):
    add_textbox(slide, 0.48, top, 12.3, 0.7, text, size=size, color=INK, bold=True)


def add_footer(slide, index, total):
    add_textbox(slide, 0.48, 7.14, 8.5, 0.24, "REWRITE USING THE BOOTCAMP CHAIN OF CONVICTION", size=9, color=MUTED)
    add_textbox(slide, 10.4, 7.14, 2.4, 0.24, f"{index:02d}  /  {total:02d}", size=9, color=MUTED, align=PP_ALIGN.RIGHT)


def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    paint(slide)
    return slide


def card(slide, left, top, width, height, color, title, body, *, title_color=INK):
    add_rect(slide, left, top, width, height, color, radius=0.08)
    add_textbox(slide, left + 0.22, top + 0.16, width - 0.44, 0.32, title, size=12, color=title_color, bold=True)
    add_textbox(slide, left + 0.22, top + 0.48, width - 0.44, height - 0.68, body, size=15, color=INK)


def build_pptx(out_path: Path):
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    c = COMPANY
    slides = []

    # 1 Cover / one breath
    s = new_slide(prs)
    add_kicker(s, "Understand · Slide 1")
    add_title(s, "Make me understand the company in one breath", size=30)
    add_textbox(s, 0.48, 1.35, 12.3, 0.36, c["name"], size=16, color=TEAL, bold=True)
    add_rect(s, 0.48, 1.85, 12.36, 2.35, STRONG, radius=0.08)
    add_textbox(s, 0.74, 2.05, 11.86, 1.95, c["one_breath"], size=22, color=INK, bold=True)
    add_textbox(
        s, 0.48, 4.45, 12.3, 1.4,
        "Rule: describe the business before describing the ambition. Customer + job + outcome. No ecosystem, no AI-powered, no next-generation until the buyer is obvious.",
        size=16, color=MUTED,
    )
    slides.append(s)

    # 2 Problem
    s = new_slide(prs)
    add_kicker(s, "Understand · Problem")
    add_title(s, "Pain beats breadth")
    card(s, 0.48, 1.45, 6.0, 4.4, WEAK, "WEAK — industry language", "A list of everything wrong with a sector. Fragmented. Inefficient. Outdated. The investor still cannot see one person stuck.", title_color=RED)
    card(s, 6.84, 1.45, 6.0, 4.4, STRONG, "STRONG — customer language", f"{c['problem_person']}\n\n{c['problem']}", title_color=TEAL)
    add_textbox(s, 0.48, 6.05, 12.3, 0.7, "Person + painful situation + consequence.", size=16, color=MUTED)
    slides.append(s)

    # 3 Solution + why now
    s = new_slide(prs)
    add_kicker(s, "Understand + why now")
    add_title(s, "Show the transformation, then explain why now")
    card(s, 0.48, 1.45, 3.5, 3.2, LIGHT, "BEFORE", c["before"])
    add_rect(s, 4.18, 1.85, 4.96, 2.4, BLACK, radius=0.08)
    add_textbox(s, 4.38, 2.15, 4.56, 0.4, "YOUR PRODUCT", size=12, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_textbox(s, 4.38, 2.55, 4.56, 1.4, c["product"], size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    card(s, 9.34, 1.45, 3.5, 3.2, STRONG, "AFTER", c["after"], title_color=TEAL)
    add_rect(s, 0.48, 4.9, 12.36, 1.7, WHITE, radius=0.08)
    add_textbox(s, 0.7, 5.05, 11.9, 0.3, "WHY NOW?", size=12, color=ORANGE, bold=True)
    add_textbox(s, 0.7, 5.38, 11.9, 1.0, c["why_now"], size=16, color=INK)
    slides.append(s)

    # 4 Market
    s = new_slide(prs)
    add_kicker(s, "Believe · Market")
    add_title(s, "Replace giant TAM with believable math")
    card(s, 0.48, 1.45, 4.2, 4.5, WEAK, "TOP-DOWN — low information", f"{c['bad_tam']}\n\n{c['bad_tam_label']}\n\nBig number. Low information.", title_color=RED)
    add_rect(s, 4.92, 1.45, 7.92, 4.5, STRONG, radius=0.08)
    add_textbox(s, 5.2, 1.7, 7.4, 0.32, "BOTTOM-UP", size=12, color=TEAL, bold=True)
    add_textbox(s, 5.2, 2.15, 7.4, 1.4, f"{c['units']}  ×  {c['price']}  =  {c['opportunity']}", size=22, color=INK, bold=True)
    add_textbox(s, 5.2, 3.7, 7.4, 1.8, f"Beachhead:\n{c['beachhead']}", size=16, color=INK)
    slides.append(s)

    # 5 Traction
    s = new_slide(prs)
    add_kicker(s, "Believe · Proof")
    add_title(s, "Traction is evidence, not decoration")
    for i, line in enumerate(c["traction"]):
        y = 1.5 + i * 1.2
        add_rect(s, 0.48, y, 12.36, 1.05, WHITE, radius=0.08)
        add_rect(s, 0.48, y, 0.12, 1.05, TEAL)
        add_textbox(s, 0.84, y + 0.28, 11.7, 0.55, line, size=18, color=INK)
    slides.append(s)

    # 6 Model + GTM
    s = new_slide(prs)
    add_kicker(s, "Engine")
    add_title(s, "Who pays, how much, how often — then #1 to #1,000")
    card(s, 0.48, 1.4, 4.0, 2.35, WHITE, "WHO PAYS?", c["who_pays"], title_color=TEAL)
    card(s, 4.66, 1.4, 4.0, 2.35, WHITE, "HOW MUCH?", c["how_much"], title_color=ORANGE)
    card(s, 8.84, 1.4, 4.0, 2.35, WHITE, "HOW OFTEN?", c["how_often"], title_color=RED)
    add_textbox(s, 0.48, 3.95, 12.3, 0.36, "How does customer #1 become customer #1,000?", size=18, color=INK, bold=True)
    step_w = 2.28
    for i, step in enumerate(c["gtm_steps"]):
        x = 0.48 + i * 2.56
        add_rect(s, x, 4.45, step_w, 0.9, WHITE, radius=0.08)
        add_textbox(s, x, 4.68, step_w, 0.45, step, size=13, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_textbox(s, 0.48, 5.55, 12.3, 1.1, c["gtm_engine"], size=16, color=MUTED)
    slides.append(s)

    # 7 Competition
    s = new_slide(prs)
    add_kicker(s, "Why you")
    add_title(s, "Your biggest rival may be “do nothing”")
    add_textbox(s, 0.48, 1.28, 12.3, 0.36, "Do not manufacture a feature table where you win every column.", size=14, color=MUTED)
    for i, (name, note) in enumerate(c["rivals"][:4]):
        x = 0.48 + i * 3.2
        add_rect(s, x, 1.8, 3.02, 2.6, WHITE, radius=0.08)
        add_textbox(s, x + 0.18, 2.0, 2.66, 0.9, name, size=18, color=INK, bold=True)
        add_textbox(s, x + 0.18, 2.95, 2.66, 1.2, note, size=14, color=MUTED)
    add_rect(s, 0.48, 4.65, 12.36, 1.9, BLACK, radius=0.08)
    add_textbox(s, 0.74, 4.85, 11.86, 0.7, "Your job is not to prove competitors are bad. It is to prove your advantage compounds.", size=16, color=WHITE, bold=True)
    add_textbox(s, 0.74, 5.55, 11.86, 0.75, c["advantage"], size=16, color=WHITE)
    slides.append(s)

    # 8 Team
    s = new_slide(prs)
    add_kicker(s, "Want more · Team")
    add_title(s, "Team ≠ biographies. Show evidence.")
    for i, line in enumerate(c["team_evidence"]):
        col = i % 2
        row = i // 2
        x = 0.48 + col * 6.4
        y = 1.5 + row * 2.35
        add_rect(s, x, y, 6.16, 2.15, WHITE, radius=0.08)
        add_rect(s, x, y, 0.12, 2.15, TEAL)
        add_textbox(s, x + 0.4, y + 0.7, 5.5, 0.8, line, size=18, color=INK, bold=True)
    slides.append(s)

    # 9 Ask
    s = new_slide(prs)
    add_kicker(s, "Want more · Ask")
    add_title(s, "Ask ≠ “strategic investors”. Be specific.")
    items = [
        ("AMOUNT", c["raise_amount"]),
        ("RUNWAY", c["runway"]),
        ("MILESTONES", c["milestones"]),
        ("WHAT CAPITAL CHANGES", c["capital_changes"]),
        ("WHAT YOU WANT NEXT", c["want_next"]),
    ]
    for i, (label, body) in enumerate(items):
        y = 1.4 + i * 0.95
        add_rect(s, 0.48, y, 12.36, 0.85, WHITE, radius=0.08)
        add_rect(s, 0.48, y, 0.12, 0.85, RED)
        add_textbox(s, 0.84, y + 0.08, 12.0, 0.28, label, size=11, color=RED, bold=True)
        add_textbox(s, 0.84, y + 0.36, 12.0, 0.4, body, size=16, color=INK)
    slides.append(s)

    # 10 Scorecard
    s = new_slide(prs)
    add_kicker(s, "Before redesign")
    add_title(s, "Score the story. Then subtract.")
    left_items = [
        "1. Business understood quickly",
        "2. Problem specific + painful",
        "3. Solution immediately clear",
        "4. Traction is credible evidence",
        "5. Market math is believable",
    ]
    right_items = [
        "6. Business model is clear",
        "7. GTM is repeatable",
        "8. Advantage is defensible",
        "9. Team has founder-market fit",
        "10. Ask is explicit",
    ]
    for i, line in enumerate(left_items):
        add_textbox(s, 0.48, 1.4 + i * 0.55, 6.0, 0.45, line, size=16, color=INK)
    for i, line in enumerate(right_items):
        add_textbox(s, 6.84, 1.4 + i * 0.55, 6.0, 0.45, line, size=16, color=INK)
    add_rect(s, 0.48, 4.3, 3.9, 0.7, WEAK, radius=0.08)
    add_textbox(s, 0.48, 4.45, 3.9, 0.4, "0–19  RETHINK THE STORY", size=13, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_rect(s, 4.62, 4.3, 3.9, 0.7, RGBColor(0xF6, 0xEA, 0xD3), radius=0.08)
    add_textbox(s, 4.62, 4.45, 3.9, 0.4, "20–39  REFINE IT", size=13, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_rect(s, 8.76, 4.3, 4.08, 0.7, RGBColor(0xDC, 0xEF, 0xE8), radius=0.08)
    add_textbox(s, 8.76, 4.45, 4.08, 0.4, "40–50  POLISH IT", size=13, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_textbox(
        s, 0.48, 5.25, 12.3, 1.4,
        "Each item 0–5. Maximum 50. Perfecting the deck is mostly subtraction: remove anything that stops the investor from seeing the opportunity.",
        size=16, color=MUTED,
    )
    slides.append(s)

    total = len(slides)
    for i, slide in enumerate(slides, start=1):
        add_footer(slide, i, total)

    prs.save(out_path)
    return out_path


def build_html(out_path: Path):
    c = COMPANY
    rivals = "".join(
        f'<div class="card"><strong>{escape(name)}</strong><p>{escape(note)}</p></div>'
        for name, note in c["rivals"]
    )
    traction = "".join(f"<li>{escape(line)}</li>" for line in c["traction"])
    team = "".join(f"<li>{escape(line)}</li>" for line in c["team_evidence"])
    gtm = " → ".join(escape(step) for step in c["gtm_steps"])
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(c["name"])} · pitch preview</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,600&display=swap" rel="stylesheet" />
  <style>
    :root {{ --ink:#141414; --muted:#5c5c5c; --teal:#0f6e62; --paper:#f7f5f1; --weak:#f8e8ea; --strong:#e4f1f4; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family:"Instrument Sans",system-ui,sans-serif; background:var(--paper); color:var(--ink); }}
    .wrap {{ max-width:980px; margin:0 auto; padding:40px 24px 80px; }}
    h1,h2 {{ font-family:Newsreader,Georgia,serif; }}
    .slide {{ background:#fff; border:1px solid #e6e6e6; border-radius:18px; padding:28px; margin:18px 0; }}
    .kicker {{ font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); font-weight:600; }}
    .grid {{ display:grid; gap:12px; }}
    .two {{ grid-template-columns:1fr 1fr; }}
    .three {{ grid-template-columns:1fr 1fr 1fr; }}
    .four {{ grid-template-columns:repeat(4,1fr); }}
    .card {{ background:#fafafa; border-radius:12px; padding:16px; }}
    .weak {{ background:var(--weak); }}
    .strong {{ background:var(--strong); }}
    .black {{ background:#111; color:#fff; border-radius:12px; padding:20px; }}
    @media (max-width:800px) {{ .two,.three,.four {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <p class="kicker">Browser preview of YOUR-PITCH-DECK.pptx · PPTX cannot render in this chat</p>
    <h1>{escape(c["name"])}</h1>
    <p>Edit <code>COMPANY</code> in <code>generate_pitch_deck.py</code> and regenerate. Bracketed text is a prompt, not a claim.</p>

    <article class="slide">
      <div class="kicker">01 Understand</div>
      <h2>One breath</h2>
      <div class="card strong"><p>{escape(c["one_breath"])}</p></div>
    </article>

    <article class="slide">
      <div class="kicker">02 Problem</div>
      <h2>Pain beats breadth</h2>
      <p><strong>{escape(c["problem_person"])}</strong></p>
      <p>{escape(c["problem"])}</p>
    </article>

    <article class="slide">
      <div class="kicker">03 Solution + why now</div>
      <h2>Transformation</h2>
      <div class="grid three">
        <div class="card"><strong>Before</strong><p>{escape(c["before"])}</p></div>
        <div class="black"><strong>Product</strong><p>{escape(c["product"])}</p></div>
        <div class="card strong"><strong>After</strong><p>{escape(c["after"])}</p></div>
      </div>
      <p><strong>Why now:</strong> {escape(c["why_now"])}</p>
    </article>

    <article class="slide">
      <div class="kicker">04 Market</div>
      <h2>Believable math</h2>
      <div class="grid two">
        <div class="card weak"><strong>Not this</strong><p>{escape(c["bad_tam"])} {escape(c["bad_tam_label"])}</p></div>
        <div class="card strong"><strong>This</strong><p>{escape(c["units"])} × {escape(c["price"])} = {escape(c["opportunity"])}</p><p>{escape(c["beachhead"])}</p></div>
      </div>
    </article>

    <article class="slide">
      <div class="kicker">05 Traction</div>
      <h2>Evidence</h2>
      <ul>{traction}</ul>
    </article>

    <article class="slide">
      <div class="kicker">06 Engine</div>
      <h2>Who pays · how much · how often</h2>
      <div class="grid three">
        <div class="card"><strong>Who pays</strong><p>{escape(c["who_pays"])}</p></div>
        <div class="card"><strong>How much</strong><p>{escape(c["how_much"])}</p></div>
        <div class="card"><strong>How often</strong><p>{escape(c["how_often"])}</p></div>
      </div>
      <p>{gtm}</p>
      <p>{escape(c["gtm_engine"])}</p>
    </article>

    <article class="slide">
      <div class="kicker">07 Competition</div>
      <h2>Do nothing is a rival</h2>
      <div class="grid four">{rivals}</div>
      <p>{escape(c["advantage"])}</p>
    </article>

    <article class="slide">
      <div class="kicker">08 Team</div>
      <h2>Evidence, not job titles</h2>
      <ul>{team}</ul>
    </article>

    <article class="slide">
      <div class="kicker">09 Ask</div>
      <h2>Make the next step explicit</h2>
      <ul>
        <li>Amount: {escape(c["raise_amount"])}</li>
        <li>Runway: {escape(c["runway"])}</li>
        <li>Milestones: {escape(c["milestones"])}</li>
        <li>What capital changes: {escape(c["capital_changes"])}</li>
        <li>What you want next: {escape(c["want_next"])}</li>
      </ul>
    </article>

    <article class="slide">
      <div class="kicker">10 Scorecard</div>
      <h2>Score 0–5 on each, then subtract</h2>
      <p>Understood quickly · painful problem · clear solution · credible traction · believable market math · clear model · repeatable GTM · defensible advantage · founder-market fit · explicit ask.</p>
      <p>0–19 rethink · 20–39 refine · 40–50 polish.</p>
    </article>
  </div>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main():
    folder = Path(__file__).resolve().parent
    pptx_path = build_pptx(folder / "YOUR-PITCH-DECK.pptx")
    html_path = build_html(folder / "pitch-preview.html")
    print(f"Wrote {pptx_path}")
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
