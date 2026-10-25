"""Time-boxed business experiments and conservative pivots.

Drafts and live offers have separate clocks. Missing marketplace metrics do not
prove buyers rejected a product. No marketplace login or publication occurs here.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from .catalog import BOTS

DRAFT_TIMEOUT_DAYS = 14
LIVE_TIMEOUT_DAYS = 14
EARLY_REVIEW_DAYS = 7
MIN_EARLY_IMPRESSIONS = 100


@dataclass(frozen=True)
class Decision:
    action: str       # keep, retire, or none
    classification: str
    explanation: str
    days: float


def as_utc(raw):
    if isinstance(raw, datetime):
        return raw.replace(tzinfo=timezone.utc) if raw.tzinfo is None else raw.astimezone(timezone.utc)
    if not isinstance(raw,str):
        raise ValueError('Expected an ISO timestamp or UTC datetime')
    return as_utc(datetime.fromisoformat(raw.replace('Z', '+00:00')))


def assess(trial, now=None):
    """Assess a single allowed, generated case from truthful observed history.

    * Never assert the absence of demand from absent analytics.
    * Only manually reported data is currently available.
    * A sale reported by a user is useful but not verified commerce proof.
    """
    now=as_utc(now or datetime.now(timezone.utc))
    started=trial.get('launched_at')
    base=as_utc(started or trial['created_at'])
    age=max(0.,(now-base).total_seconds()/86400)
    if trial.get('retired_at'):
        return Decision('none','ALREADY_RETIRED','The experiment has already been retired.',age)
    if not trial.get('artifact_dir') or trial.get('verdict')!='NOT GUILTY':
        return Decision('none','NOT_EXECUTABLE','No court-approved, quality-checked artifact.',age)
    if not started:
        if age>=DRAFT_TIMEOUT_DAYS:
            return Decision('retire','UNLAUNCHED',
                            'Fourteen days passed without confirmation of a public launch. No claim of customer rejection; switch to another technique.',age)
        return Decision('keep','NEEDS_LAUNCH',
                        'Product created locally, but no real marketplace trial has started.',age)
    # "Views" and "sales" in v0.3 are USER-REPORTED ONLY, never verified automatically.
    views=int(trial.get('views') or 0)
    clicks=int(trial.get('clicks') or 0)
    sales=int(trial.get('sales') or 0)
    net=int(trial.get('gross_cents') or 0)-int(trial.get('fee_cents') or 0)
    if sales>0 and net>0:
        return Decision('keep','REPORTED_POSITIVE','User-reported positive net results. Continue testing; independently verify.',age)
    if age>=LIVE_TIMEOUT_DAYS:
        return Decision('retire','INCONCLUSIVE' if views==0 and clicks==0 and sales==0 else 'LOW_RETURN',
                        ('Fourteen days after launch without measurable data: tracking missing or no reach; '
                         'retire this experiment and try another approach, not a proven market failure.'
                         if views==0 and clicks==0 and sales==0 else
                         'Fourteen-day trial has no positive reported net earnings. Retire and pivot to a different technique.'),age)
    if age>=EARLY_REVIEW_DAYS and views>=MIN_EARLY_IMPRESSIONS and clicks==0 and sales==0:
        return Decision('retire','LOW_ENGAGEMENT',
                        'Seven days and at least 100 reported views without a click: switch techniques. Reported views are unverified.',age)
    return Decision('keep','RUNNING','Still inside the evidence-gathering window.',age)


def choose_new_technique(old_bot_key, case_counts, retired_bot_keys=()):
    """Pick a DIFFERENT industry lane, not a renamed copy of the same product.

    Limited to the known, audited bot catalog. Exhaustion is a pause rather than
    pretending to have invented and implemented a novel type of business.
    """
    original=next((b for b in BOTS if b.key==old_bot_key),None)
    if original is None:
        return None
    retired=set(retired_bot_keys)
    from .strategy import MAX_VARIANTS
    options=[b for b in BOTS if b.key!=old_bot_key and b.lane!=original.lane
             and b.key not in retired and case_counts.get(b.key,0)<MAX_VARIANTS
             and b.cost_to_draft<=0 and b.suggested_price>0]
    return min(options,key=lambda b:(case_counts.get(b.key,0),BOTS.index(b))) if options else None
