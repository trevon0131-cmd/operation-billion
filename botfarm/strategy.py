"""Bounded, explainable learning: new compliant proposals, not self-editing Python.

Rejection never grants permission to repeat a forbidden activity. The new plan is
tried from scratch before any files are generated. Public buzz is not demand.
"""
from dataclasses import dataclass, replace
from .court import Proposal

THEMES = (
    'Daily Momentum', 'Simple Wins', 'Fresh Start', 'Little Victories',
    'Better Every Day', 'Make It Happen', 'Small Steps', 'Bright Ideas',
    'Keep Going', 'Focused Future', 'Start Somewhere', 'Own Your Journey',
    'Grow With Purpose', 'Think Clearly', 'More Possibilities', 'Build Slowly',
)
# No more than 16 intentionally different treatments per specialist, because
# generating infinite near-duplicate listings without evidence is not useful.
MAX_VARIANTS = 16

@dataclass(frozen=True)
class Candidate:
    bot: object
    proposal: Proposal
    hypothesis: str
    change: str


def propose(bot, variant, evidence_links=(), metrics=()):
    """Improve creative theme from prior attempts; use measured outcomes only if present."""
    theme = THEMES[(variant - 1) % len(THEMES)] if variant else None
    subject = bot.subject if not variant else f'{theme} — {bot.subject}'
    # Preserve short labels for SVG/PDF friendliness and truthful template contents.
    if bot.artifact == 'svg' and variant:
        subject = theme
    adjusted = replace(bot, subject=subject)
    hypothesis = ('New themed variation for testing. Demand unverified.' if variant
                  else 'Original product idea. Demand unverified.')
    observed = [x for x in metrics if x.get('views', 0) >= 50]
    if observed:
        hypothesis += ' At least one user-reported comparison has 50+ impressions; results are not independently verified.'
    if bot.key == 'ebay_sticker_scout' and variant == 0:
        # A legitimate initial proposal that fails without production/stock.
        p = Proposal(bot.key, 'Sell physical stickers without stock',
                     action='publish_to_marketplace', requires_inventory=True,
                     evidence_links=tuple(evidence_links[:3]))
        return Candidate(adjusted, p, hypothesis, 'Physical fulfillment concept (must be rejected)')
    if bot.key == 'affiliate_review' and variant == 0:
        p = Proposal(bot.key, 'Publish affiliate sales pages without enrollment',
                     action='publish_to_marketplace',
                     evidence_links=tuple(evidence_links[:3]))
        return Candidate(adjusted, p, hypothesis, 'Affiliate enrollment and verification not established')
    p = Proposal(bot.key, adjusted.subject, evidence_links=tuple(evidence_links[:3]))
    return Candidate(adjusted, p, hypothesis, 'Original free digital draft')


def repair(candidate, judgment):
    """Try ONE distinct zero-cost alternative; do not silence original charges."""
    if judgment.verdict != 'GUILTY':
        return None
    charges = ' '.join(judgment.judge).lower()
    bot = candidate.bot
    if 'inventory' in charges or 'fulfillment' in charges or bot.key == 'ebay_sticker_scout':
        new_title = 'Zero-inventory digital sticker product alternative'
        change = 'Reject stockless physical sale; research an original downloadable sticker product instead.'
    elif 'action' in charges or 'outside' in charges:
        new_title = f'{bot.subject} — original local draft, no marketplace posting'
        change = 'Replace external publishing with an original file and publication checklist.'
    elif 'cost' in charges or 'budget' in charges:
        new_title = f'{bot.subject} — free software alternative'
        change = 'Drop every paid tool and upfront expense; use local-only generation.'
    elif 'intellectual property' in charges or 'licens' in charges:
        new_title = 'Original geometry and public-domain-free workflow'
        change = 'Use original material only; do not reuse the disputed content.'
    elif 'third parties' in charges or 'outreach' in charges:
        new_title = 'Opt-in product concept; no messages sent'
        change = 'Replace unsolicited outreach with an offline opt-in landing-page draft.'
    elif 'misleading' in charges or 'earnings' in charges:
        new_title = 'Evidence-first product draft with no earnings claims'
        change = 'Remove unverified claims and replace them with measurement plans.'
    else:
        return None  # Unrecognized hard stop: pause, do not invent a workaround.
    # Preserves bot key; the existing generator can recover after interruption.
    revised = replace(bot, subject=new_title)
    if bot.key == 'ebay_sticker_scout':
        revised = replace(revised, artifact='svg', suggested_price=3.0,
                          channel='Ko-fi / Gumroad',
                          pitch='Original, downloadable digital sticker vector; NOT a physical sticker',
                          notes='No physical stock, shipping or print-on-demand service')
    p = Proposal(bot.key, new_title, action='generate_local_draft',
                 evidence_links=candidate.proposal.evidence_links)
    return Candidate(revised, p, 'Alternative unvalidated zero-cost idea', change)
