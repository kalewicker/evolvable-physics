"""Invented rule/body/world records. Never evolves a world or constructs a law."""
import copy
import unittest
import audit
import generator_v2
import diagnose_p01g as diag
from test_p01g_execution import rule


def world():
    return {'nodes':{'42':{'kind':1,'state':0,'matter':5,'activation':6},
                     '100':{'kind':2,'state':0,'matter':1,'activation':1}},
            'edges':{'0':{'class':'Structural','kind':0,'ends':[42,100]}},
            'next_node':101,'next_edge':1,'dissipated':1}


def pair(form):
    r=rule(form);r['nodes'][1]={'kind':2,'state':0};return r


class ReadOnlyDiagnosis(unittest.TestCase):
    def test_first_change_invariance_including_noops_and_blocked_guards(self):
        noop=rule(0);noop['nodes'][0]={'kind':2,'state':None}
        guarded={'id':1,'nodes':[{'kind':2,'state':1}],'edges':[],'absent':[],
                 'ops':[{'op':'AddState','node':0,'delta':1}]}
        with diag.read_only():
            self.assertTrue(diag.state_frozen([noop,guarded],2,0))
            guarded['nodes'][0]['state']=None
            self.assertFalse(diag.state_frozen([noop,guarded],2,0))

    def test_static_kind_and_proved_state_blocks(self):
        birth=rule(4);recycle=pair(7);recycle['id']=1;recycle['nodes'][1]['state']=1
        r=diag.compatibility([birth,recycle],birth,recycle)
        self.assertEqual(r['excluded_by'],['invariant_child_state'])
        mutable=rule(0);mutable['nodes'][0]={'kind':2,'state':None};mutable['ops'][0]['value']=1
        self.assertTrue(diag.compatibility([birth,recycle,mutable],birth,recycle)['not_excluded_by_kind_or_proved_state_invariance'])
        recycle['nodes'][0]['kind']=3
        self.assertIn('donor_kind',diag.compatibility([birth,recycle],birth,recycle)['excluded_by'])

    def test_funding_and_recycling_algebra_without_application(self):
        w=world()
        with diag.read_only():
            self.assertEqual(diag.conditions('funding',pair(3),[42,100],w),[])
            self.assertEqual(diag.conditions('recycling',pair(7),[42,100],w),[])
            w['edges']['1']={'class':'Contact','kind':0,'ends':[100,42]}
            w['nodes']['42']['activation']=w['nodes']['100']['activation']=0
            self.assertEqual(diag.conditions('recycling',pair(7),[42,100],w),['target_other_incidence','activation'])

    def test_descendant_matter_activation_and_integer_bounds(self):
        w=world();r=rule(4);r['nodes'][0]['kind']=2
        self.assertEqual(diag.conditions('descendant_birth',r,[100],w),['matter','activation'])
        w['nodes']['100'].update(matter=3,activation=2)
        self.assertEqual(diag.conditions('descendant_birth',r,[100],w),[])
        w['next_node']=2**64-1
        self.assertEqual(diag.conditions('descendant_birth',r,[100],w),['integer_bounds'])

    def test_exclusive_first_blocker_and_overlapping_conditions(self):
        w=world();w['nodes']['42']['state']=1;w['nodes']['42']['activation']=0
        r=pair(3);r['nodes'][0]['state']=0;c=diag.counter()
        diag.exposure(c,'funding',r,[42,100],w,{}, {}, {},0)
        self.assertEqual(c['first_blocker'],{'donor_state':1})
        self.assertEqual(c['failed_conditions_overlapping'],{'donor_state':1,'activation':1})
        self.assertEqual(sum(c['first_blocker'].values()),c['exposures'])

    def test_candidate_disagreement_fails_closed(self):
        with self.assertRaisesRegex(AssertionError,'Algebra/candidate mismatch'):
            diag.exposure(diag.counter(),'funding',pair(3),[42,100],world(),{}, {}, {},0)

    def test_scheduler_saved_footprints_and_commit_partition(self):
        a={'rule':0,'binding':[42],'priority':'01','reads':['node:42'],'writes':['node:42']}
        b={'rule':1,'binding':[42,100],'priority':'02','reads':['node:42','node:100'],'writes':['node:100']}
        frame={'candidates':[a,b],'events':[{'id':70,'candidate':a}]}
        candidates,losses,events=diag.scheduler(frame)
        self.assertEqual(losses[(1,(42,100))]['winner_event'],70)
        self.assertEqual(losses[(1,(42,100))]['conflicting_keys'],['node:42'])
        bad=copy.deepcopy(frame);bad['events'].append({'id':71,'candidate':b})
        with self.assertRaisesRegex(AssertionError,'scheduler partition'):diag.scheduler(bad)

    def test_transition_and_sampler_calls_are_blocked(self):
        with diag.read_only():
            for f,args in [(audit.execute,(None,None,None)),(audit.enumerate_candidates,(None,None)),
                           (generator_v2.construct,(4000,0))]:
                with self.assertRaisesRegex(RuntimeError,'forbids'):f(*args)

    def test_track_gate_keeps_newborn_members_and_rejects_changed_label(self):
        track={'first':0,'last':7,'ambiguous':False,'observations':8,'similar_observations':8,
               'active_epochs':7,'all_members':[42,100],'active_members':[42,100],'active_persistence':False}
        protocol={'min_duration':8,'min_active_epoch_denominator':2,'min_active_epoch_numerator':1}
        estimator={'tracks':[track],'supported':False,'samples':[[]],'excluded_large':0}
        report={'prefix_detection':{'connected':copy.deepcopy(estimator),'interaction':copy.deepcopy(estimator)}}
        result=diag.report_diagnosis(report,protocol)
        self.assertEqual(result['connected']['failed_track_conditions_overlapping'],{'duration':1})
        report['prefix_detection']['connected']['tracks'][0]['active_persistence']=True
        with self.assertRaisesRegex(AssertionError,'Stored track gate mismatch'):diag.report_diagnosis(report,protocol)

if __name__=='__main__':unittest.main()
