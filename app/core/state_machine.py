from dataclasses import dataclass


@dataclass
class Transition:
    from_state: str
    to_state: str
    requires_approval: bool = False
    automation_hook: str | None = None


class StateMachine:
    def __init__(self, name, transitions: list[Transition]):
        self.name = name
        self.transitions = transitions
        self._lookup = {(t.from_state, t.to_state): t for t in self.transitions}

    def can_transition(self, from_state, to_state):
        return (from_state, to_state) in self._lookup

    def get_transition(self, from_state, to_state):
        return self._lookup.get((from_state, to_state))


# --- Listing Machine ---
# Valid paths:
#   draft → active
#   active → pending, under_contract, off_market
#   pending → active, under_contract, off_market
#   under_contract → sold, active, off_market
#   sold → (terminal, no exits)
#   off_market → active (can relist)

LISTING_MACHINE = StateMachine(
    name="listing",
    transitions=[
        #   draft → active
        Transition(
            from_state="draft",
            to_state="active",
            automation_hook="listing.active",
        ),
        #   active -> pending, under_contract, off_market
        Transition(
            from_state="active",
            to_state="pending",
            requires_approval=True,
            automation_hook="listing.pending",
        ),
        Transition(
            from_state="active",
            to_state="under_contract",
            requires_approval=True,
            automation_hook="listing.under_contract",
        ),
        Transition(
            from_state="active",
            to_state="off_market",
            requires_approval=True,
            automation_hook="listing.off_market",
        ),
        #   pending -> active, under_contract, off_market
        Transition(
            from_state="pending",
            to_state="active",
            requires_approval=True,
            automation_hook="listing.active",
        ),
        Transition(
            from_state="pending",
            to_state="under_contract",
            requires_approval=True,
            automation_hook="listing.under_contract",
        ),
        Transition(
            from_state="pending",
            to_state="off_market",
            requires_approval=True,
            automation_hook="listing.off_market",
        ),
        #   under_contract -> sold, active, off_market
        Transition(
            from_state="under_contract",
            to_state="sold",
            automation_hook="listing.sold",
        ),
        Transition(
            from_state="under_contract",
            to_state="active",
            automation_hook="listing.active",
        ),
        Transition(
            from_state="under_contract",
            to_state="off_market",
            automation_hook="listing.off_market",
        ),
        #   off_market -> active (can relist)
        Transition(
            from_state="off_market",
            to_state="active",
            automation_hook="listing.active",
        ),
    ],
)


# --- Pipeline Machine ---
# Valid paths (linear with some exits):
#   new -> contacted, lost
#   contacted -> showing_scheduled, lost
#   showing_scheduled -> offer_submitted, lost
#   offer_submitted -> negotiating, lost
#   negotiating -> under_contract, lost
#   under_contract -> closed, lost
#   closed →-> (terminal)
#   lost -> contacted (re-engage path)


PIPELINE_MACHINE = StateMachine(
    name="pipeline",
    transitions=[
        # new -> contacted, lost
        Transition(
            from_state="new",
            to_state="contacted",
            automation_hook="pipeline.contacted",
        ),
        Transition(
            from_state="new",
            to_state="lost",
            automation_hook="pipeline.lost",
        ),
        # contacted -> showing_scheduled, lost
        Transition(
            from_state="contacted",
            to_state="showing_scheduled",
            automation_hook="pipeline.showing_scheduled",
        ),
        Transition(
            from_state="contacted",
            to_state="lost",
            automation_hook="pipeline.lost",
        ),
        # showing_scheduled -> offer_submitted, lost
        Transition(
            from_state="showing_scheduled",
            to_state="offer_submitted",
            automation_hook="pipeline.offer_submitted",
        ),
        Transition(
            from_state="showing_scheduled",
            to_state="lost",
            automation_hook="pipeline.lost",
        ),
        # offer_submitted -> negotiating, lost
        Transition(
            from_state="offer_submitted",
            to_state="negotiating",
            requires_approval=True,
            automation_hook="pipeline.negotiating",
        ),
        Transition(
            from_state="offer_submitted",
            to_state="lost",
            requires_approval=True,
            automation_hook="pipeline.lost",
        ),
        # negotiating -> under_contract, lost
        Transition(
            from_state="negotiating",
            to_state="under_contract",
            requires_approval=True,
            automation_hook="pipeline.under_contract",
        ),
        Transition(
            from_state="negotiating",
            to_state="lost",
            requires_approval=True,
            automation_hook="pipeline.lost",
        ),
        # under_contract -> closed, lost
        Transition(
            from_state="under_contract",
            to_state="closed",
            requires_approval=True,
            automation_hook="pipeline.closed",
        ),
        Transition(
            from_state="under_contract",
            to_state="lost",
            requires_approval=True,
            automation_hook="pipeline.lost",
        ),
        # lost -> contacted (re-engage path)
        Transition(
            from_state="lost",
            to_state="contacted",
            requires_approval=True,
            automation_hook="pipeline.contacted",
        ),
    ],
)


# --- Document Machine ---
# Valid paths:
#   draft -> sent, voided
#   sent -> signed, voided
#   signed -> voided
#   voided -> (terminal)

DOCUMENT_MACHINE = StateMachine(
    name="document",
    transitions=[
        # draft -> sent, voided
        Transition(
            from_state="draft",
            to_state="sent",
            requires_approval=True,
            automation_hook="document.sent",
        ),
        Transition(
            from_state="draft",
            to_state="voided",
            automation_hook="document.voided",
        ),
        # sent -> signed, voided
        Transition(
            from_state="sent",
            to_state="signed",
            automation_hook="document.signed",
        ),
        Transition(
            from_state="sent",
            to_state="voided",
            automation_hook="document.voided",
        ),
        # signed -> voided
        Transition(
            from_state="signed",
            to_state="voided",
            automation_hook="document.voided",
        ),
    ],
)
