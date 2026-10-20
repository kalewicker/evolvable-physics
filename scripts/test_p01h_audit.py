"""Independent static matrix regressions; no law draws or transitions."""
import unittest
from audit_p01h import kind_matrix
from test_p01g_execution import rule


class KindMatrix(unittest.TestCase):
    def test_missing_and_incompatible_bodies(self):
        birth=rule(4);transfer=rule(3);transfer['id']=1;recycle=rule(7);recycle['id']=2
        m=kind_matrix([birth,transfer,recycle])
        self.assertEqual(m['birth_funding_pairs'],1)
        self.assertEqual(m['birth_recycling_pairs'],1)
        self.assertEqual(m['kind_compatible_funding_pairs'],[])
        self.assertEqual(m['kind_compatible_recycling_pairs'],[])
        self.assertEqual(kind_matrix([])['birth_rules'],0)

    def test_matching_pair_is_detected_and_contact_route_excluded(self):
        birth=rule(4);transfer=rule(3);transfer['id']=1;transfer['nodes'][1]={'kind':2,'state':0}
        recycle=rule(7);recycle['id']=2;recycle['nodes'][1]={'kind':2,'state':0}
        m=kind_matrix([birth,transfer,recycle])
        self.assertEqual(m['kind_compatible_funding_pairs'],[[0,1]])
        self.assertEqual(m['kind_compatible_recycling_pairs'],[[0,2]])
        transfer['edges'][0]['class']='Contact'
        self.assertEqual(kind_matrix([birth,transfer])['funding_rules'],0)

if __name__=='__main__':unittest.main()
