"""Control-only subprocess for simulated campaign-parent loss."""
import json
import sys
from pathlib import Path
import campaign
import audit_integration
p=json.loads(Path(sys.argv[2]).read_text())
initial=audit_integration.initial('driven_pair',0)
campaign.run_campaign(Path(sys.argv[1]),p,mode='engineering_control',controls=[initial]*p['denominator'],
                      faults={(0,'native'):'crash_parent'})
