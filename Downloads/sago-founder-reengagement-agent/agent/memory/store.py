from dataclasses import dataclass
from .schemas import DealState


@dataclass
class InMemoryStore:
    deals: dict

    def __init__(self):
        self.deals = {}

    def upsert_deal(self, deal):
        self.deals[deal.deal_id] = deal

    def get_deal(self, deal_id):
        return self.deals.get(deal_id)
