import unittest
from botfarm.court import Proposal, adjudicate

class CourtTests(unittest.TestCase):
    def test_safe_local_draft_allowed(self):
        v=adjudicate(Proposal(bot_key='x',title='Original sticker'))
        self.assertEqual(v.verdict,'NOT GUILTY')
        self.assertEqual(len(v.jury),5)
        self.assertEqual(len(v.witnesses),4)
        self.assertTrue(v.human_release_required)
    def test_no_auto_publish(self):
        self.assertEqual(adjudicate(Proposal('x','Sell','publish_to_marketplace')).verdict,'GUILTY')
    def test_money_not_free(self):
        self.assertEqual(adjudicate(Proposal('x','Paid',expenditure_usd=.01)).verdict,'GUILTY')
    def test_nan_cost_denied(self):
        self.assertEqual(adjudicate(Proposal('x','NaN',expenditure_usd=float('nan'))).verdict,'GUILTY')
    def test_unknown_rights(self):
        self.assertEqual(adjudicate(Proposal('x','Trademark',third_party_ip=True,has_rights=False)).verdict,'GUILTY')
    def test_inventory_not_verified(self):
        self.assertEqual(adjudicate(Proposal('x','Physical',requires_inventory=True)).verdict,'GUILTY')
    def test_deceptive_claim(self):
        self.assertEqual(adjudicate(Proposal('x','Fake',deceptive_claim=True)).verdict,'GUILTY')
    def test_income_guarantee(self):
        self.assertEqual(adjudicate(Proposal('x','Guaranteed',expected_revenue_claim='$1B')).verdict,'GUILTY')
    def test_outreach_blocked(self):
        self.assertEqual(adjudicate(Proposal('x','Unsolicited',requires_outreach=True)).verdict,'GUILTY')
    def test_license_issue(self):
        self.assertEqual(adjudicate(Proposal('x','License',license_issue=True)).verdict,'GUILTY')
    def test_rights_released_attempt(self):
        self.assertEqual(adjudicate(Proposal('x','Auto release',rights_released=True)).verdict,'GUILTY')
    def test_jury_cannot_override_judge(self):
        j=adjudicate(Proposal('x','Cost',expenditure_usd=0.001))
        self.assertEqual(j.verdict,'GUILTY')
    def test_finite_evidence_count(self):
        p=Proposal('x','Case',evidence_links=tuple('https://example.com/'+str(i) for i in range(20)))
        self.assertLessEqual(len(adjudicate(p).evidence),6)
