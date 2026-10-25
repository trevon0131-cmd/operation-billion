"""Original digital-product generator. No outside art, fonts, or paid API needed."""
import csv
import html
import json
import math
import os
import struct
import tempfile
import zlib
from pathlib import Path
from .catalog import Bot

PALETTES = [('#172554','#c7d2fe','#fcd34d'),('#064e3b','#d1fae5','#fbbf24'),
            ('#4c1d95','#f3e8ff','#fda4af'),('#7c2d12','#ffedd5','#7dd3fc')]

# Basic pixel font lets us produce a *real transparent PNG* without Pillow or ImageMagick.
FONT = {
'A':'01110 10001 10001 11111 10001 10001 10001','B':'11110 10001 11110 10001 10001 10001 11110',
'C':'01111 10000 10000 10000 10000 10000 01111','D':'11110 10001 10001 10001 10001 10001 11110',
'E':'11111 10000 11110 10000 10000 10000 11111','F':'11111 10000 11110 10000 10000 10000 10000',
'G':'01111 10000 10000 10111 10001 10001 01111','H':'10001 10001 10001 11111 10001 10001 10001',
'I':'11111 00100 00100 00100 00100 00100 11111','J':'00111 00010 00010 00010 10010 10010 01100',
'K':'10001 10010 10100 11000 10100 10010 10001','L':'10000 10000 10000 10000 10000 10000 11111',
'M':'10001 11011 10101 10101 10001 10001 10001','N':'10001 11001 10101 10011 10001 10001 10001',
'O':'01110 10001 10001 10001 10001 10001 01110','P':'11110 10001 10001 11110 10000 10000 10000',
'Q':'01110 10001 10001 10001 10101 10010 01101','R':'11110 10001 10001 11110 10100 10010 10001',
'S':'01111 10000 10000 01110 00001 00001 11110','T':'11111 00100 00100 00100 00100 00100 00100',
'U':'10001 10001 10001 10001 10001 10001 01110','V':'10001 10001 10001 10001 10001 01010 00100',
'W':'10001 10001 10001 10101 10101 10101 01010','X':'10001 10001 01010 00100 01010 10001 10001',
'Y':'10001 10001 01010 00100 00100 00100 00100','Z':'11111 00001 00010 00100 01000 10000 11111',
' ':'00000 00000 00000 00000 00000 00000 00000',
}

def atomic_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.writing-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

def svg_art(bot: Bot, variant: int) -> str:
    ink, paper, accent = PALETTES[variant % len(PALETTES)]
    t=html.escape(bot.subject)
    rings=[]
    for j in range(14):
        a=2*math.pi*j/14+variant*0.21
        x=400+230*math.cos(a); y=390+230*math.sin(a)
        rings.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{17+j%3*8}" fill="{accent}" opacity=".78"/>')
    body=''.join(rings)
    if bot.key=='coloring_pages':
        body=''.join(f'<circle cx="400" cy="400" r="{30+i*26}" fill="none" stroke="{ink}" stroke-width="3"/>' for i in range(12))
        paper='#ffffff'; accent='#ffffff'
    elif bot.key=='icon_pack' or bot.key=='pattern_designer':
        body=''.join(f'<rect x="{64+i*90}" y="{160+j*92}" width="48" height="48" rx="{(i+j+variant)%4*12}" fill="{accent if (i+j)%2 else ink}" opacity=".8"/>' for i in range(8) for j in range(5))
    elif bot.key=='sticker_studio':
        body+=''.join(f'<path d="M 400 390 Q {200+i*50} {100+i*10} {320+i*25} {200+i*18}" fill="none" stroke="{ink}" stroke-width="5" stroke-linecap="round"/>' for i in range(4))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" role="img" aria-label="Original {t} design">
<rect width="800" height="800" rx="{0 if bot.key=='coloring_pages' else 150}" fill="{paper}"/>
<circle cx="400" cy="370" r="250" fill="none" stroke="{ink}" stroke-width="12"/>
{body}
<rect x="70" y="327" width="660" height="145" rx="30" fill="{paper}" stroke="{ink}" stroke-width="6"/>
<text x="400" y="393" text-anchor="middle" fill="{ink}" font-family="sans-serif" font-size="{max(20, min(39, 620/max(1, len(bot.subject))*1.3)):.0f}" font-weight="bold">{t}</text>
<text x="400" y="428" text-anchor="middle" fill="{ink}" font-family="sans-serif" font-size="16">ORIGINAL DESIGN · EDITABLE VECTOR</text>
</svg>'''

def png_chunk(name, payload):
    return struct.pack('!I',len(payload))+name+payload+struct.pack('!I',zlib.crc32(name+payload)&0xffffffff)

def make_sticker_png(path: Path, variant: int, words='KEEP GROWING'):
    """Transparent raster asset, originally drawn with simple geometric layers."""
    size=640
    buf=bytearray(size*size*4)
    palette=[(42,72,139),(20,117,98),(112,59,155),(155,71,40)]
    r,g,b=palette[variant % 4]
    def pixel(x,y,color):
        if 0<=x<size and 0<=y<size:
            p=(y*size+x)*4; buf[p:p+4]=bytes(color)
    # Ring + solid oval from entirely original geometry.
    for y in range(50,590):
        yy=y-320
        for x in range(50,590):
            xx=x-320; d=xx*xx+yy*yy
            if d < 263**2:
                color=(254,248,232,255) if d<252**2 else (r,g,b,255)
                pixel(x,y,color)
    for i in range(12):
        a=2*math.pi*i/12
        cx=320+205*math.cos(a);cy=320+205*math.sin(a)
        for y in range(int(cy-17),int(cy+18)):
            for x in range(int(cx-17),int(cx+18)):
                if (x-cx)**2+(y-cy)**2 < (8+i%3*3)**2:
                    pixel(x,y,(241,163,71,255))
    # Draw legible block-letter text over the original sticker.
    def label(txt, y, scale=5):
        txt=txt[:18].upper()
        x0=(size-(len(txt)*6-1)*scale)//2
        for n,ch in enumerate(txt):
            glyph=FONT.get(ch,FONT[' ']).split()
            for gy,row in enumerate(glyph):
                for gx,val in enumerate(row):
                    if val=='1':
                        for dy in range(scale):
                            for dx in range(scale):
                                pixel(x0+(n*6+gx)*scale+dx,y+gy*scale+dy,(r,g,b,255))
    label('KEEP',265,10)
    label('GROWING',365,7)
    raw=b''.join(b'\x00'+buf[y*size*4:(y+1)*size*4] for y in range(size))
    out=b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('!2I5B',size,size,8,6,0,0,0))
    out+=png_chunk(b'IDAT',zlib.compress(raw,6))+png_chunk(b'IEND',b'')
    path.write_bytes(out)

def document_html(bot: Bot, variant: int) -> str:
    ink,paper,accent=PALETTES[variant%4]
    title=html.escape(bot.subject)
    content = {
      'price_calculator':'''<p>Enter a selling price, platform fee %, fixed fee, and your real cost.</p><label>Price $ <input id="price" type="number" value="10" min="0" step=".01"></label><label>Platform fee % <input id="percent" type="number" value="5" min="0" max="100" step=".1"></label><label>Flat fee $ <input id="fixed" type="number" value=".30" min="0" step=".01"></label><label>Production cost $ <input id="cost" type="number" value="0" min="0" step=".01"></label><p id="answer">Change a value to calculate.</p><script>function calc(){const n=id=>Math.max(0,Number(document.getElementById(id).value)||0);const net=n('price')*(1-n('percent')/100)-n('fixed')-n('cost');document.getElementById('answer').textContent='Estimated profit before tax: $'+net.toFixed(2)+' (not actual earnings)';}document.querySelectorAll('input').forEach(x=>x.addEventListener('input',calc));calc();</script>''',
      'study_planner':'''<p>Use for courses, work blocks, and rest. Modify in your browser before printing.</p><table><tr><th>Day</th><th>Class / priority</th><th>Study block</th><th>Done?</th></tr>'''+''.join(f'<tr><td>{d}</td><td contenteditable="true">Type here</td><td contenteditable="true">Time here</td><td>☐</td></tr>' for d in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])+'</table>',
      'habit_tracker':'''<p>Write your habit: __________________</p><div class="days">'''+''.join(f'<span>{n}<input type="checkbox" aria-label="Day {n}"></span>' for n in range(1,31))+'</div><p>Reflection: What helped you be consistent? _________________________</p>',
      'meal_planner':'''<table><tr><th>Day</th><th>Breakfast</th><th>Lunch</th><th>Dinner</th></tr>'''+''.join(f'<tr><td>{d}</td>'+''.join('<td contenteditable="true">Plan meal</td>' for _ in range(3))+'</tr>' for d in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])+'''</table><h2>Groceries</h2><p contenteditable="true">Write your list here...</p>''',
      'cleaning_checklist':'''<h2>Weekly Reset</h2>'''+''.join(f'<p><input type="checkbox"> {item}</p>' for item in ['Clear counters and surfaces','Wipe kitchen sink','Tidy living area','Take out trash','Sweep / vacuum','Refresh bedding','Set next week priorities']),
      'resume_template':'''<h2 contenteditable="true">Your Name</h2><p contenteditable="true">City • email@example.com • Phone</p><h2>Profile</h2><p contenteditable="true">Two sentences about skills and work interests.</p><h2>Experience</h2><p contenteditable="true">Position | Organization | Dates<br>• Action + specific result you can verify</p><h2>Education</h2><p contenteditable="true">Your school, major and graduation date</p><h2>Skills</h2><p contenteditable="true">List only true skills.</p>''',
      'learning_worksheets':'''<p contenteditable="true">Topic: _____________ | Learner: ____________ | Date: ____________</p>'''+''.join(f'<p>{i}. <span contenteditable="true">Add an original practice question here ___________________________</span></p>' for i in range(1,11))+'''<h2>Answer key</h2><p contenteditable="true">Create your answer key here.</p>''',
      'landing_page_kit':'''<section class="hero"><h2 contenteditable="true">Your business. Your promise.</h2><p contenteditable="true">Write a specific, accurate benefit here.</p><a class="cta" href="mailto:you@example.com">Contact us</a></section><h2>Why choose us</h2><p contenteditable="true">Replace this placeholder with true details about your business and services.</p><h2>Contact</h2><p contenteditable="true">Email: you@example.com</p>''',
    }.get(bot.key,'<p>Editable template</p>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
body{{max-width:880px;margin:36px auto;padding:25px;font:17px/1.6 system-ui,Arial;color:{ink};background:#fff}}h1{{border-bottom:5px solid {accent};padding-bottom:18px}}h2{{margin-top:28px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #999;padding:10px;text-align:left}}td[contenteditable],p[contenteditable]{{background:{paper};min-width:40px}}.days{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}}.days span{{padding:14px;background:{paper};border-radius:8px}}label{{display:block;margin:12px 0}}input{{padding:6px}}.hero{{padding:35px;background:{paper};border-radius:16px}}.cta{{display:inline-block;background:{ink};color:white;padding:12px 20px;border-radius:8px}}@media print{{body{{margin:0;padding:8mm}}input{{border:0}}}}
</style></head><body><h1>{title}</h1><p>Editable original template • Variation {variant+1}</p>{content}<footer><small>Use and customize this template; review your facts before distributing.</small></footer></body></html>'''

def md_product(bot: Bot, variant: int) -> str:
    patterns = {
       'social_caption_pack':['Behind the scenes: Today I worked on [true activity].','Quick tip: One practical thing that helps with [topic].','Before and after: What changed in [your real project]?','Question for our community: What would you try?','Myth vs reality: Correct a common misconception, with sources.'],
       'blog_outline':['What problem does your reader really face?','What would a credible, sourced answer look like?','List the first three realistic steps.','Compare trade-offs without invented claims.','Close with an actionable checklist.'],
       'newsletter_kit':['Issue theme: one specific reader problem','Opening: 2 honest sentences summarizing this week','Main section: 3 researched points with citations','Useful links: only pages you reviewed','Call-to-action: reply with a question'],
       'interview_prep':['Describe a task you completed and what changed.','What did you learn from a difficult project?','How do you prioritize competing deadlines?','Tell me about teamwork with concrete evidence.','What is one thoughtful question for the interviewer?'],
       'cover_letter':['Dear [Hiring Manager],','I am applying for [role] because [true reason].','At [organization], I [specific verifiable achievement].','My experience with [skill] matches [job requirement].','Thank you for your consideration. Sincerely, [name]'],
       'website_pitch':['Project outcome: [specific client goal]','Scope: [pages and functionality agreed]','Client assets needed: [logos, words, photos with rights]','Timeline: [realistic agreed dates]','Price and revisions: [approved quote and limits]'],
       'micro_saas':['User problem hypothesis: repetitive task taking >10 minutes','Minimal demo: offline HTML + local storage only','Validation: interview 5 consenting potential users','Measure: real opt-ins, not views alone','Success gate: demonstrated demand before hosting expense'],
       'affiliate_review':['Disclosure: This page may contain affiliate links if enrolled.','Only describe a product after hands-on evaluation.','Track real price, shipping and returns before comparing.','Report downsides and conflicts of interest.','Do not insert affiliate links without approved program access.'],
       'ebay_sticker_scout':['Find out whether the proposed item is physical or a digital file.','Confirm design rights, printer/material cost and stock.','Calculate shipping, packaging, taxes and eBay fees.','Research category restrictions and listing limits.','Draft only; never promise physical stock you do not have.'],
    }
    steps=patterns.get(bot.key,['Define a real customer problem','Create an original solution','Ask for user feedback','Measure real orders and costs'])
    return '# '+bot.subject+'\n\n**Original editable starter • Version '+str(variant+1)+'**\n\n'+''.join(f'{i}. {s}\n' for i,s in enumerate(steps,1))+'\n## Notes\n\nReplace placeholders, verify all claims, and confirm the platform rules before publishing.\n'

def csv_product(bot: Bot) -> str:
    import io
    output=io.StringIO()
    writer=csv.writer(output)
    if bot.key=='budget_planner':
        writer.writerow(['Category','Planned_USD','Actual_USD','Notes'])
        for cat in ['Income','Housing','Utilities','Food','Transportation','Education','Savings','Other']:
            writer.writerow([cat,'0.00','0.00','Replace with actual data'])
    else:
        writer.writerow(['SKU','Item','Quantity','Cost_Each_USD','List_Price_USD','Platform_Fee_USD','Notes'])
        for num in range(1,6): writer.writerow([f'SKU{num:03d}','Your item',0,'0.00','0.00','0.00','Replace placeholders'])
    return output.getvalue()

def make_artifact(home:Path, bot:Bot, variant:int, fingerprint:str, evidence:list) -> Path:
    folder=home/'output'/bot.key/f'v{variant+1}_{fingerprint[:12]}'
    folder.mkdir(parents=True,exist_ok=True)
    if bot.artifact=='svg':
        atomic_text(folder/'product.svg',svg_art(bot,variant))
        if bot.key=='sticker_studio':
            make_sticker_png(folder/'sticker_transparent.png',variant)
    elif bot.artifact=='html':
        atomic_text(folder/'product.html',document_html(bot,variant))
    elif bot.artifact=='csv':
        atomic_text(folder/'product.csv',csv_product(bot))
    else:
        atomic_text(folder/'product.md',md_product(bot,variant))
    metadata={
        'bot':bot.name,'subject':bot.subject,'suggested_price_usd':bot.suggested_price,
        'suggested_channel':bot.channel,'audience_hypothesis':bot.audience,
        'revenue_usd':None,'revenue_status':'UNKNOWN / NOT YET MEASURED',
        'signal_sources':evidence,'variant':variant+1,'provenance':'Original local generated starter',
        'publication_status':'DRAFT_ONLY','notes':bot.notes}
    atomic_text(folder/'metadata.json',json.dumps(metadata,indent=2,ensure_ascii=False))
    atomic_text(folder/'listing_DRAFT.md',f'''# {bot.subject} — DRAFT ONLY

**Description:** {bot.pitch}.

**Who it may serve:** {bot.audience}. This is a hypothesis, not proven demand.

**Suggested initial asking price (not validated):** ${bot.suggested_price:.2f}

**Possible channel (not connected):** {bot.channel}

**What's included:** The original local product files in this folder.

**Important:** This is a digital design/template or research document, not a shipped physical item. Do not claim commercial results, product stock, licenses, or reviews you cannot prove. Check marketplace listing restrictions, rights, applicable tax rules, accessibility and quality before publishing.

**Not published. No account connected. No sale occurred.**
''')
    return folder
