"""Deterministic trial. AI suggestions can never bypass judge hard-stop rules."""
from dataclasses import dataclass, asdict
import math
from typing import Any

ALLOWED_ACTIONS = frozenset({'generate_local_draft', 'analyze_public_signal'})

@dataclass(frozen=True)
class Proposal:
    bot_key: str
    title: str
    action: str = 'generate_local_draft'
    expenditure_usd: float = 0.0
    expected_revenue_claim: str = 'unknown'
    third_party_ip: bool = False
    has_rights: bool = True
    requires_inventory: bool = False
    inventory_confirmed: bool = False
    requires_outreach: bool = False
    rights_released: bool = False
    license_issue: bool = False
    deceptive_claim: bool = False
    evidence_links: tuple = ()

@dataclass
class Judgment:
    verdict: str
    decision: str
    prosecution: list
    defense: list
    witnesses: dict
    jury: list
    judge: list
    evidence: list
    human_release_required: bool = True

    def data(self):
        return asdict(self)

def adjudicate(p: Proposal, budget=0.0) -> Judgment:
    charges = []
    defense = []
    judge = []
    evidence = [{'source': 'proposal', 'detail':f'{p.bot_key}: {p.title}', 'type':'claim'}]
    evidence.extend({'source':'public signal (not sales)', 'detail':v, 'type':'url'}
                    for v in p.evidence_links[:5] if isinstance(v, str) and v.startswith('https://'))
    if p.action not in ALLOWED_ACTIONS:
        judge.append('HARD STOP: action is outside the allowed local/research actions')
    if not math.isfinite(p.expenditure_usd) or p.expenditure_usd > budget or p.expenditure_usd < 0:
        judge.append('HARD STOP: projected cost exceeds the zero-dollar budget or is invalid')
    if p.third_party_ip and not p.has_rights:
        judge.append('HARD STOP: third-party intellectual property rights not proven')
    if p.license_issue:
        judge.append('HARD STOP: unresolved licensing or terms concern')
    if p.requires_inventory and not p.inventory_confirmed:
        judge.append('HARD STOP: physical fulfillment or inventory unverified')
    if p.requires_outreach:
        judge.append('HARD STOP: contacting third parties is not authorized')
    if p.deceptive_claim:
        judge.append('HARD STOP: misleading or fabricated claims')
    if p.expected_revenue_claim != 'unknown':
        judge.append('HARD STOP: non-verified earnings promises are not admitted')
    if p.rights_released:
        judge.append('HARD STOP: local generation cannot grant publication/sale rights')
    if not judge:
        defense.extend(['Original locally produced draft is possible with free local software',
                        'No spending, outreach, uploads, or commerce actions will be executed'])
    else:
        charges.extend(judge)
        defense.append('A local-only redesign may remove blocked actions after a new trial')
    witnesses = {
        'Financial expert': f'Planned up-front expenditure: ${p.expenditure_usd:.2f}; permitted: ${budget:.2f}. Sales unproven.',
        'Rights expert': 'Third-party material requires documented rights' if p.third_party_ip else 'No third-party content asserted by proposer',
        'Evidence expert': f'{len(p.evidence_links)} external leads. Public interest is not proof of buyers.',
        'Operations expert': f'Action proposed: {p.action}; outside-platform activity not automated',
    }
    # Jury considers independent dimensions; the judge's hard stops always take precedence.
    jury = [
        {'juror':'Economics', 'vote':'GUILTY' if (not math.isfinite(p.expenditure_usd) or p.expenditure_usd > budget or p.expenditure_usd < 0) else 'NOT GUILTY'},
        {'juror':'Originality & rights', 'vote':'GUILTY' if (p.third_party_ip and not p.has_rights) or p.license_issue else 'NOT GUILTY'},
        {'juror':'Consumer trust', 'vote':'GUILTY' if p.deceptive_claim or p.expected_revenue_claim != 'unknown' else 'NOT GUILTY'},
        {'juror':'Execution safety', 'vote':'GUILTY' if p.action not in ALLOWED_ACTIONS or p.requires_outreach else 'NOT GUILTY'},
        {'juror':'Fulfillment', 'vote':'GUILTY' if p.requires_inventory and not p.inventory_confirmed else 'NOT GUILTY'},
    ]
    guilty = bool(judge) or sum(j['vote']=='GUILTY' for j in jury) >= 3
    if not guilty:
        judge.append('Allowed: prepare LOCAL DRAFT ONLY. Publication, payment, and contact require human action.')
    verdict = 'GUILTY' if guilty else 'NOT GUILTY'
    return Judgment(verdict, 'REJECT' if guilty else 'ALLOW LOCAL DRAFT', charges,
                    defense, witnesses, jury, judge, evidence)
