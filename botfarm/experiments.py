"""Conservative improvement suggestions based only on manually recorded outcomes."""
from collections import defaultdict
from .storage import Store


def recommendations(store: Store):
    by_bot=defaultdict(list)
    for m in store.metrics():
        by_bot[m['bot_key']].append(m)
    suggestions=[]
    for bot, trials in sorted(by_bot.items()):
        evaluated=[t for t in trials if t['views']>=20]
        if not evaluated:
            suggestions.append({'bot':bot,'status':'NEED_REAL_DATA',
                                'detail':'Collect at least 20 real impressions per version before ranking.'})
            continue
        # Smoothed conversion rate avoids declaring 1 sale / 1 view a winner.
        best=max(evaluated,key=lambda t: (t['sales']+1)/(t['views']+50))
        suggestions.append({'bot':bot,'status':'EXPLORATORY_LEADER',
            'detail':f"Case #{best['id']} has the best smoothed reported sales/view signal among versions with 20+ views. Verify the data before adapting; do not claim a proven winner.",
            'case_id':best['id'],'views':best['views'],'reported_sales':best['sales']})
    return suggestions
