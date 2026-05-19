from dataclasses import dataclass


@dataclass
class OrderCreatedEvent:
    order_id: str
    order_number: str
    tenant_id: str
    branch_id: str
    total: float

    def dict(self):
        return {
            "order_id": self.order_id,
            "order_number": self.order_number,
            "tenant_id": self.tenant_id,
            "branch_id": self.branch_id,
            "total": self.total,
        }


@dataclass
class OrderStatusChangedEvent:
    order_id: str
    old_status: str
    new_status: str
    updated_by: str

    def dict(self):
        return {
            "order_id": self.order_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "updated_by": self.updated_by,
        }
