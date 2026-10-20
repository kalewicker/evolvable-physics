"""Counterexample records for scope claims; no transition engine is invoked."""
import copy
import unittest
import diagnose_p01


def fixture_record():
    return {'nodes':{str(i):{'kind':1,'state':0,'matter':8,'activation':8} for i in range(8)},
        'edges':{str(i):{'class':'Contact','kind':0,'ends':[i,(i+1)%8]} for i in range(8)},
        'next_node':8,'next_edge':8,'epoch':0,'dissipated':0,'matter_total':80,'activation_total':64,
        'next_event':0,'writers':{}}


class DiagnosticTests(unittest.TestCase):
    def test_scope_accepts_zero_resource_isolate_but_rejects_attachment(self):
        initial=fixture_record();world=copy.deepcopy(initial)
        world['nodes']['8']={'kind':2,'state':0,'matter':0,'activation':0}
        world['nodes']['0']['matter']-=1;world['next_node']=9
        self.assertEqual(diagnose_p01.world_scope(initial,world,initial),1)
        attached=copy.deepcopy(world);attached['edges']['8']={'class':'Structural','kind':0,'ends':[0,8]}
        attached['next_edge']=9;attached['nodes']['0']['matter']-=1
        with self.assertRaisesRegex(AssertionError,'Newborn/novel structural route'):
            diagnose_p01.world_scope(initial,attached,world)
        funded=copy.deepcopy(world);funded['nodes']['8']['matter']=1;funded['nodes']['0']['matter']-=1
        with self.assertRaisesRegex(AssertionError,'Newborn resource gain'):
            diagnose_p01.world_scope(initial,funded,world)

    def test_immutable_contact_counterexample_is_rejected(self):
        initial=fixture_record();world=copy.deepcopy(initial)
        del world['edges']['0'];world['nodes']['0']['matter']+=1
        with self.assertRaises(AssertionError):diagnose_p01.world_scope(initial,world,initial)

    def test_track_reasons_preserve_inactive_member_and_detect_changed_label(self):
        p={'min_duration':8,'min_active_epoch_denominator':2,'min_active_epoch_numerator':1}
        track={'first':0,'last':10,'ambiguous':False,'observations':11,'similar_observations':11,
               'active_epochs':10,'all_members':[0,1],'active_members':[1],'active_persistence':False}
        self.assertEqual(diagnose_p01.failed_gates(track,p),['inactive_members'])
        track['active_persistence']=True
        with self.assertRaisesRegex(AssertionError,'Stored track gate mismatch'):diagnose_p01.failed_gates(track,p)

    def test_scope_rejects_unknown_rule_shape(self):
        rule={'nodes':[{'kind':1,'state':None},{'kind':1,'state':None}],
              'edges':[{'class':'Structural','kind':0,'ends':[0,1]}],'absent':[],
              'ops':[{'op':'DeleteEdge','account':1,'kind':0,'ends':[0,1]}, {'op':'DeleteNode','node':0,'recipient':1}]}
        self.assertEqual(diagnose_p01.rule_form(rule),7)
        rule['ops'][0]['account']=0
        with self.assertRaises(AssertionError):diagnose_p01.rule_form(rule)
