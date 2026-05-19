from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Text, JSON, Date, Time
from sqlalchemy.sql import func
import uuid
from app.infrastructure.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    logo_url = Column(Text)
    phone = Column(String(20))
    email = Column(String(255), nullable=False)
    subscription_plan = Column(String(50), default='basic')
    subscription_status = Column(String(20), default='trial')
    max_branches = Column(Integer, default=1)
    max_users = Column(Integer, default=10)
    max_terminals = Column(Integer, default=5)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Branch(Base):
    __tablename__ = "branches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(20), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default='India')
    phone = Column(String(20))
    email = Column(String(255))
    timezone = Column(String(50), default='Asia/Kolkata')
    currency = Column(String(3), default='INR')
    tax_identifier = Column(String(50))
    business_type = Column(String(50))
    opening_hours = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="SET NULL"))
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"))
    parent_id = Column(String(36), ForeignKey("menu_categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    display_order = Column(Integer, default=0)
    image_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"))
    category_id = Column(String(36), ForeignKey("menu_categories.id"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    item_code = Column(String(50))
    bar_code = Column(String(100))
    image_url = Column(Text)

    base_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))

    tax_rate = Column(Numeric(5, 2), default=0)
    is_veg = Column(Boolean, default=True)
    contains_allergens = Column(JSON, default=[])

    preparation_time_minutes = Column(Integer, default=15)
    calories = Column(Integer)

    is_available = Column(Boolean, default=True)
    is_combo = Column(Boolean, default=False)
    combo_details = Column(JSON)

    printer_routing = Column(JSON)
    recipe_ingredients = Column(JSON, default=[])

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_number = Column(String(50), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    table_id = Column(String(36), ForeignKey("dining_tables.id"))

    order_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='pending')

    customer_id = Column(String(36))
    customer_name = Column(String(255))
    customer_phone = Column(String(20))

    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    tip_amount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False, default=0)

    payment_status = Column(String(20), default='pending')

    special_instructions = Column(Text)
    source = Column(String(20), default='pos')

    delivery_address = Column(JSON)
    delivery_partner = Column(String(50))
    aggregator_order_id = Column(String(100))

    scheduled_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    created_by = Column(String(36), ForeignKey("users.id"))
    assigned_to = Column(String(36), ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(String(36), ForeignKey("menu_items.id"), nullable=False)

    item_name = Column(String(255), nullable=False)
    item_code = Column(String(50))
    quantity = Column(Numeric(5, 2), nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)

    variant_id = Column(String(36), ForeignKey("menu_variants.id"))
    variant_name = Column(String(255))
    modifiers = Column(JSON, default=[])

    cooking_instructions = Column(Text)
    course_type = Column(String(20))

    prep_status = Column(String(20), default='pending')
    prep_started_at = Column(DateTime(timezone=True))
    ready_at = Column(DateTime(timezone=True))
    served_at = Column(DateTime(timezone=True))

    priority = Column(String(10), default='normal')

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(30), nullable=False)

    gateway = Column(String(50))
    transaction_id = Column(String(100))
    gateway_reference_id = Column(String(100))

    status = Column(String(20), default='pending')

    refund_id = Column(String(36), ForeignKey("payments.id"))
    refund_amount = Column(Numeric(10, 2))
    refund_reason = Column(Text)

    idempotency_key = Column(String(100), unique=True)
    payment_metadata = Column(JSON)

    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MenuVariant(Base):
    __tablename__ = "menu_variants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    menu_item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    name = Column(String(255), nullable=False)
    price_adjustment = Column(Numeric(10, 2), default=0)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MenuModifierGroup(Base):
    __tablename__ = "menu_modifier_groups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    menu_item_id = Column(String(36), ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"))
    name = Column(String(100), nullable=False)
    min_selections = Column(Integer, default=0)
    max_selections = Column(Integer, default=1)
    is_required = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class MenuModifier(Base):
    __tablename__ = "menu_modifiers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    group_id = Column(String(36), ForeignKey("menu_modifier_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), default=0)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class DiningTable(Base):
    __tablename__ = "dining_tables"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    table_number = Column(String(20), nullable=False)
    capacity = Column(Integer, default=4)
    section = Column(String(50))
    is_active = Column(Boolean, default=True)
    current_order_id = Column(String(36), ForeignKey("orders.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TaxConfig(Base):
    __tablename__ = "tax_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id"))
    name = Column(String(100), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
    tax_type = Column(String(20), default='gst')
    applicable_to = Column(JSON, default='["dine_in", "takeaway", "delivery"]')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text)
    discount_type = Column(String(20), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_order_value = Column(Numeric(10, 2), default=0)
    max_discount = Column(Numeric(10, 2))
    max_uses = Column(Integer)
    uses_count = Column(Integer, default=0)
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)

    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20), nullable=False)
    alternate_phone = Column(String(20))

    date_of_birth = Column(Date)
    anniversary = Column(Date)

    loyalty_points = Column(Integer, default=0)
    wallet_balance = Column(Numeric(10, 2), default=0)

    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(12, 2), default=0)
    average_order_value = Column(Numeric(10, 2))

    customer_type = Column(String(20), default='regular')
    membership_tier = Column(String(20))

    preferences = Column(JSON, default={})
    delivery_addresses = Column(JSON, default='[]')

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    points = Column(Integer, nullable=False)
    order_id = Column(String(36), ForeignKey("orders.id"))
    reason = Column(String(255))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryCategory(Base):
    __tablename__ = "inventory_categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id"))
    category_id = Column(String(36), ForeignKey("inventory_categories.id"))

    name = Column(String(255), nullable=False)
    item_code = Column(String(50))
    bar_code = Column(String(100))
    unit = Column(String(50), default='pcs')

    current_stock = Column(Numeric(10, 2), default=0)
    minimum_stock = Column(Numeric(10, 2), default=0)
    reorder_level = Column(Numeric(10, 2))
    reorder_quantity = Column(Numeric(10, 2))

    cost_price = Column(Numeric(10, 2))
    selling_price = Column(Numeric(10, 2))

    supplier_id = Column(String(36), ForeignKey("vendors.id"))
    is_trackable = Column(Boolean, default=True)
    expires_on = Column(Date)
    shelf_location = Column(String(100))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    inventory_item_id = Column(String(36), ForeignKey("inventory_items.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id"))

    movement_type = Column(String(30), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    reference_type = Column(String(50))
    reference_id = Column(String(36))
    batch_number = Column(String(50))
    expiry_date = Column(Date)
    notes = Column(Text)

    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    gst_number = Column(String(50))
    payment_terms = Column(String(100))
    rating = Column(Numeric(2, 1))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_number = Column(String(50), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=False)

    status = Column(String(20), default='draft')
    expected_delivery = Column(Date)

    subtotal = Column(Numeric(10, 2))
    tax_amount = Column(Numeric(10, 2))
    total = Column(Numeric(10, 2))

    notes = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"))
    approved_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_duration_minutes = Column(Integer, default=0)
    is_night_shift = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), default='scheduled')
    check_in = Column(DateTime(timezone=True))
    check_out = Column(DateTime(timezone=True))
    work_hours = Column(Numeric(4, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"))
    branch_id = Column(String(36), ForeignKey("branches.id"))

    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36))

    old_value = Column(JSON)
    new_value = Column(JSON)

    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_id = Column(String(36))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
