# KitchenOS - Scalable Restaurant Management & POS Platform

## Executive Summary

**Project:** KitchenOS - Enterprise Restaurant Management SaaS Platform  
**Timeline:** 2-Day MVP (production-ready foundation)  
**Team:** 1-2 developers  
**Target Cloud:** Oracle Cloud Infrastructure  

### Architecture Philosophy
- **Modular Monolith First** - Single deployable unit, boundary-based modules
- **Microservice-Ready** - Clean interfaces enabling future extraction
- **Event-Driven Foundation** - Domain events for async workflows and scalability
- **Multi-Tenant Native** - Row-level isolation with tenant_id, supporting 1000+ concurrent restaurants

---

## 1. SCALABLE ARCHITECTURE

### 1.1 System Overview
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                CLIENTS                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    POS      │  │    KDS     │  │   Admin     │  │  Super      │        │
│  │  Terminal   │  │  Display   │  │  Dashboard  │  │  Admin      │        │
│  │  (React)    │  │  (React)   │  │  (React)    │  │  (React)    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼───────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                 │ REST + WebSocket
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORACLE LOAD BALANCER                               │
│                         (Rate Limiting + SSL Offload)                        │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                        NGINX REVERSE PROXY                                   │
│              (Path-based routing, WebSocket upgrade, Gzip)                   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│   BACKEND CLUSTER  │   │   FRONTEND CDN    │   │   WEBSOCKET       │
│   (3+ Containers)  │   │   (Static Files)  │   │   SERVER CLUSTER  │
│                   │   │                   │   │   (Phoenix/Redis) │
│  ┌─────────────┐  │   └───────────────────┘   └───────────────────┘
│  │  FastAPI    │  │
│  │  App Pool   │  │         ┌───────────────────┐
│  └─────────────┘  │         │   STATIC ASSETS   │
│                   │         │   (React Build)   │
│  ┌─────────────┐  │         └───────────────────┘
│  │  Celery     │  │
│  │  Workers   │  │
│  └─────────────┘  │
└───────────────────┴─────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│   PostgreSQL      │   │      Redis        │   │    RabbitMQ       │
│   (Primary +      │   │   (Cache + Pub/   │   │   (Task Queue +   │
│    Read Replica)  │   │    Sub + Session) │   │    Dead Letter)   │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

### 1.2 Scalability Features

| Feature | Implementation | Scaling Strategy |
|---------|----------------|------------------|
| **Horizontal Scaling** | Stateless FastAPI app | Add more containers behind LB |
| **Database Scaling** | Read replicas + partitioning | Route reads to replicas |
| **Caching** | Redis cluster with TTL | Cache menu, user sessions |
| **Async Processing** | Celery + RabbitMQ | Scale workers independently |
| **Real-time** | WebSocket + Redis pub/sub | Horizontal WS servers |
| **Rate Limiting** | NGINX + Redis counters | Per-tenant rate limits |
| **Connection Pooling** | PgBouncer | 100s of concurrent connections |

### 1.3 Module Boundaries (Clean Architecture)
```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                          │
│   REST API │ GraphQL │ WebSocket │ Event Handlers               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                      APPLICATION LAYER                           │
│   Use Cases │ Commands │ Queries │ Event Handlers               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                       DOMAIN LAYER                               │
│   Entities │ Value Objects │ Domain Events │ Repository Interfaces│
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
│   Repositories │ External Services │ Caching │ Messaging         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. DATABASE ARCHITECTURE (PostgreSQL)

### 2.1 Multi-Tenant Strategy
```
STRATEGY: Shared Database + tenant_id column (row-level isolation)

Benefits:
- Simple operations (single DB, single backup)
- Cost-effective for 1000+ tenants
- Easy cross-tenant analytics
- Partition-ready for scale

Indexes:
- All tables: tenant_id + frequently queried columns (composite)
- Global queries: tenant_id as first column
```

### 2.2 Core Schema

```sql
-- ============================================
-- TENANT (Restaurant Organization)
-- ============================================
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    logo_url TEXT,
    phone VARCHAR(20),
    email VARCHAR(255) NOT NULL,
    subscription_plan VARCHAR(50) DEFAULT 'basic',
    subscription_status VARCHAR(20) DEFAULT 'trial',
    max_branches INTEGER DEFAULT 1,
    max_users INTEGER DEFAULT 10,
    max_terminals INTEGER DEFAULT 5,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(subscription_status);

-- ============================================
-- BRANCH (Individual Restaurant Location)
-- ============================================
CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'India',
    phone VARCHAR(20),
    email VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    currency VARCHAR(3) DEFAULT 'INR',
    tax_identifier VARCHAR(50),  -- GST Number
    business_type VARCHAR(50),   -- restaurant/café/cloud_kitchen/qsr
    opening_hours JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_branches_tenant ON branches(tenant_id);
CREATE INDEX idx_branches_active ON branches(tenant_id, is_active);

-- ============================================
-- USER (Staff/Admin Users)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL,  -- admin/manager/cashier/chef/waiter
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_branch ON users(branch_id);
CREATE INDEX idx_users_email ON users(tenant_id, email);

-- ============================================
-- DINING_TABLE
-- ============================================
CREATE TABLE dining_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    table_number VARCHAR(20) NOT NULL,
    capacity INTEGER DEFAULT 4,
    section VARCHAR(50),  -- terrace/main_bar/private
    is_active BOOLEAN DEFAULT true,
    current_order_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(branch_id, table_number)
);

CREATE INDEX idx_tables_branch ON dining_tables(branch_id);
CREATE INDEX idx_tables_order ON dining_tables(current_order_id) WHERE current_order_id IS NOT NULL;

-- ============================================
-- MENU_CATEGORY
-- ============================================
CREATE TABLE menu_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE CASCADE,  -- NULL = all branches
    parent_id UUID REFERENCES menu_categories(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categories_tenant ON menu_categories(tenant_id);
CREATE INDEX idx_categories_branch ON menu_categories(branch_id);
CREATE INDEX idx_categories_parent ON menu_categories(parent_id);

-- ============================================
-- MENU_ITEM
-- ============================================
CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES menu_categories(id),
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    item_code VARCHAR(50),
    bar_code VARCHAR(100),
    image_url TEXT,
    
    base_price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2),  -- For profit calculation
    
    tax_rate DECIMAL(5,2) DEFAULT 0,
    is_veg BOOLEAN DEFAULT true,
    contains_allergens JSONB DEFAULT '[]',
    
    preparation_time_minutes INTEGER DEFAULT 15,
    calories INTEGER,
    
    is_available BOOLEAN DEFAULT true,
    is_combo BOOLEAN DEFAULT false,
    combo_details JSONB,
    
    printer_routing JSONB,  -- {"station": "grill", "priority": "high"}
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_menu_tenant ON menu_items(tenant_id);
CREATE INDEX idx_menu_branch ON menu_items(branch_id);
CREATE INDEX idx_menu_category ON menu_items(category_id);
CREATE INDEX idx_menu_available ON menu_items(branch_id, is_available);

-- ============================================
-- MENU_VARIANT
-- ============================================
CREATE TABLE menu_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    price_adjustment DECIMAL(10,2) DEFAULT 0,
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MENU_MODIFIER_GROUP
-- ============================================
CREATE TABLE menu_modifier_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_item_id UUID NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,  -- "Size", "Toppings", "Extras"
    min_selections INTEGER DEFAULT 0,
    max_selections INTEGER DEFAULT 1,
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE menu_modifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES menu_modifier_groups(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) DEFAULT 0,
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true
);

-- ============================================
-- ORDER
-- ============================================
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    branch_id UUID NOT NULL REFERENCES branches(id),
    table_id UUID REFERENCES dining_tables(id),
    
    order_type VARCHAR(20) NOT NULL,  -- dine_in/takeaway/delivery/qr
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending → confirmed → preparing → ready → completed
    --            → cancelled
    
    customer_id UUID,  -- For registered customers
    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),
    
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    tip_amount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL DEFAULT 0,
    
    payment_status VARCHAR(20) DEFAULT 'pending',  -- pending/partial/paid/refunded
    
    special_instructions TEXT,
    source VARCHAR(20) DEFAULT 'pos',  -- pos/kds/qr/aggregator
    
    delivery_address JSONB,
    delivery_partner VARCHAR(50),
    aggregator_order_id VARCHAR(100),
    
    scheduled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    created_by UUID REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_tenant ON orders(tenant_id);
CREATE INDEX idx_orders_branch ON orders(branch_id);
CREATE INDEX idx_orders_status ON orders(branch_id, status);
CREATE INDEX idx_orders_date ON orders(branch_id, created_at);
CREATE INDEX idx_orders_table ON orders(table_id) WHERE table_id IS NOT NULL;
CREATE INDEX idx_orders_customer ON orders(customer_id) WHERE customer_id IS NOT NULL;

-- Partition by month for archival (optional)
-- PARTITION BY RANGE (created_at);

-- ============================================
-- ORDER_ITEM
-- ============================================
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL REFERENCES menu_items(id),
    
    item_name VARCHAR(255) NOT NULL,
    item_code VARCHAR(50),
    quantity DECIMAL(5,2) NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    
    variant_id UUID REFERENCES menu_variants(id),
    variant_name VARCHAR(255),
    modifiers JSONB DEFAULT '[]',  -- [{"id": "...", "name": "...", "price": ...}]
    
    cooking_instructions TEXT,
    course_type VARCHAR(20),  -- starter/main/dessert
    
    prep_status VARCHAR(20) DEFAULT 'pending',  -- pending/in_progress/ready/served
    prep_started_at TIMESTAMPTZ,
    ready_at TIMESTAMPTZ,
    served_at TIMESTAMPTZ,
    
    priority VARCHAR(10) DEFAULT 'normal',  -- normal/high/rush
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_menu ON order_items(menu_item_id);
CREATE INDEX idx_order_items_status ON order_items(order_id, prep_status);

-- ============================================
-- PAYMENT
-- ============================================
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    branch_id UUID NOT NULL REFERENCES branches(id),
    
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,  -- cash/card/UPI/wallet/aggregator
    
    gateway VARCHAR(50),  -- razorpay/stripe/paytm
    transaction_id VARCHAR(100),
    gateway_reference_id VARCHAR(100),
    
    status VARCHAR(20) DEFAULT 'pending',  -- pending/success/failed/refunded/cancelled
    
    refund_id UUID REFERENCES payments(id),
    refund_amount DECIMAL(10,2),
    refund_reason TEXT,
    
    idempotency_key VARCHAR(100) UNIQUE,
    metadata JSONB,
    
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_tenant ON payments(tenant_id);
CREATE INDEX idx_payments_idempotency ON payments(idempotency_key);

-- ============================================
-- TAX_CONFIG
-- ============================================
CREATE TABLE tax_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    branch_id UUID REFERENCES branches(id),  -- NULL = all branches
    name VARCHAR(100) NOT NULL,  -- "GST 18%", "VAT 12%"
    rate DECIMAL(5,2) NOT NULL,
    tax_type VARCHAR(20) DEFAULT 'gst',  -- gst/vat/sales/service
    applicable_to JSONB DEFAULT '["dine_in", "takeaway", "delivery"]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- COUPON
-- ============================================
CREATE TABLE coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    code VARCHAR(50) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20) NOT NULL,  -- percentage/fixed
    discount_value DECIMAL(10,2) NOT NULL,
    min_order_value DECIMAL(10,2) DEFAULT 0,
    max_discount DECIMAL(10,2),
    max_uses INTEGER,
    uses_count INTEGER DEFAULT 0,
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, code)
);

-- ============================================
-- CUSTOMER (CRM)
-- ============================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    
    date_of_birth DATE,
    anniversary DATE,
    
    loyalty_points INTEGER DEFAULT 0,
    wallet_balance DECIMAL(10,2) DEFAULT 0,
    
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0,
    average_order_value DECIMAL(10,2),
    
    customer_type VARCHAR(20) DEFAULT 'regular',  -- regular/member/vip
    membership_tier VARCHAR(20),
    
    preferences JSONB DEFAULT '{}',
    delivery_addresses JSONB DEFAULT '[]',
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, phone)
);

CREATE INDEX idx_customers_tenant ON customers(tenant_id);
CREATE INDEX idx_customers_phone ON customers(tenant_id, phone);
CREATE INDEX idx_customers_email ON customers(tenant_id, email) WHERE email IS NOT NULL;

-- ============================================
-- LOYALTY_TRANSACTION
-- ============================================
CREATE TABLE loyalty_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    transaction_type VARCHAR(20) NOT NULL,  -- earn/redeem/expire/adjust
    points INTEGER NOT NULL,
    order_id UUID REFERENCES orders(id),
    reason VARCHAR(255),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INVENTORY_ITEM
-- ============================================
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    branch_id UUID REFERENCES branches(id),  -- NULL = central
    category_id UUID,
    
    name VARCHAR(255) NOT NULL,
    item_code VARCHAR(50),
    bar_code VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'pcs',  -- kg/liter/pcs/pack
    
    current_stock DECIMAL(10,2) DEFAULT 0,
    minimum_stock DECIMAL(10,2) DEFAULT 0,
    reorder_level DECIMAL(10,2),
    reorder_quantity DECIMAL(10,2),
    
    cost_price DECIMAL(10,2),
    selling_price DECIMAL(10,2),
    
    supplier_id UUID,
    is_trackable BOOLEAN DEFAULT true,
    expires_on DATE,
    shelf_location VARCHAR(100),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_inventory_tenant ON inventory_items(tenant_id);
CREATE INDEX idx_inventory_branch ON inventory_items(branch_id);
CREATE INDEX idx_inventory_low_stock ON inventory_items(branch_id, current_stock) 
    WHERE current_stock <= minimum_stock;

-- ============================================
-- STOCK_MOVEMENT
-- ============================================
CREATE TABLE stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_item_id UUID NOT NULL REFERENCES inventory_items(id),
    branch_id UUID REFERENCES branches(id),
    
    movement_type VARCHAR(30) NOT NULL,  -- purchase/sale/adjustment/wastage/transfer/return
    quantity DECIMAL(10,2) NOT NULL,  -- Positive = in, Negative = out
    reference_type VARCHAR(50),  -- order/purchase/adjustment
    reference_id UUID,
    batch_number VARCHAR(50),
    expiry_date DATE,
    notes TEXT,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stock_item ON stock_movements(inventory_item_id);
CREATE INDEX idx_stock_date ON stock_movements(created_at);

-- ============================================
-- VENDOR
-- ============================================
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    gst_number VARCHAR(50),
    payment_terms VARCHAR(100),
    rating DECIMAL(2,1),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PURCHASE_ORDER
-- ============================================
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    branch_id UUID NOT NULL REFERENCES branches(id),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    
    status VARCHAR(20) DEFAULT 'draft',  -- draft/pending/approved/ordered/partial/received/cancelled
    expected_delivery DATE,
    
    subtotal DECIMAL(10,2),
    tax_amount DECIMAL(10,2),
    total DECIMAL(10,2),
    
    notes TEXT,
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- SHIFT
-- ============================================
CREATE TABLE shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id UUID NOT NULL REFERENCES branches(id),
    name VARCHAR(100) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    break_duration_minutes INTEGER DEFAULT 0,
    is_night_shift BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE shift_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shift_id UUID NOT NULL REFERENCES shifts(id),
    user_id UUID NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled/confirmed/absent
    check_in TIMESTAMPTZ,
    check_out TIMESTAMPTZ,
    work_hours DECIMAL(4,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(shift_id, user_id, date)
);

-- ============================================
-- AUDIT_LOG
-- ============================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    branch_id UUID REFERENCES branches(id),
    
    action VARCHAR(50) NOT NULL,  -- create/update/delete/login/logout
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    
    old_value JSONB,
    new_value JSONB,
    
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_date ON audit_logs(tenant_id, created_at);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
```

### 2.3 Scalability Optimizations

```sql
-- Connection pooling (PgBouncer)
-- pool_mode = transaction
-- max_client_conn = 200
-- default_pool_size = 20

-- Table partitioning for orders (by month)
CREATE TABLE orders_2026_01 PARTITION OF orders
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Materialized view for analytics (refresh hourly)
CREATE MATERIALIZED VIEW daily_sales_summary AS
SELECT 
    branch_id,
    DATE(created_at) as date,
    COUNT(*) as order_count,
    SUM(total) as total_sales,
    AVG(total) as avg_order_value
FROM orders
WHERE status = 'completed'
GROUP BY branch_id, DATE(created_at);

-- Index for common queries
CREATE INDEX idx_orders_branch_date_status ON orders(branch_id, created_at, status);
CREATE INDEX idx_order_items_order_item ON order_items(order_id, menu_item_id);
```

---

## 3. BACKEND ARCHITECTURE (FastAPI)

### 3.1 Project Structure (Scalable Monolith)
```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py          # Main v1 router
│   │   │   └── endpoints/         # Feature-based endpoints
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── tenants.py
│   │   │       ├── branches.py
│   │   │       ├── users.py
│   │   │       ├── menu.py
│   │   │       ├── orders.py
│   │   │       ├── billing.py
│   │   │       ├── payments.py
│   │   │       ├── inventory.py
│   │   │       ├── customers.py
│   │   │       ├── reports.py
│   │   │       └── admin.py
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   └── exceptions.py           # Custom exceptions
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings management
│   │   ├── security.py            # JWT, password hashing
│   │   ├── database.py            # SQLAlchemy setup
│   │   ├── redis.py               # Redis client
│   │   ├── rabbitmq.py            # RabbitMQ connection
│   │   └── exceptions.py          # App exceptions
│   │
│   ├── modules/                   # Bounded contexts
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   ├── tenant/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   ├── menu/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   ├── order/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── events.py          # Domain events
│   │   ├── billing/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── tax_calculator.py
│   │   ├── payment/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── gateways/          # Payment gateway adapters
│   │   │       ├── base.py
│   │   │       ├── razorpay.py
│   │   │       └── stripe.py
│   │   ├── inventory/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   └── customer/
│   │       ├── __init__.py
│   │       ├── schemas.py
│   │       ├── service.py
│   │       └── repository.py
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py            # Connection, session
│   │   ├── cache.py               # Redis cache layer
│   │   ├── messaging.py           # RabbitMQ publisher
│   │   └── websocket.py            # WebSocket manager
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── schemas.py             # Common schemas (Pagination, Response)
│   │   ├── middleware.py          # Custom middleware
│   │   └── utils.py               # Shared utilities
│   │
│   ├── workers/                   # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── order_tasks.py
│   │       ├── notification_tasks.py
│   │       └── report_tasks.py
│   │
│   └── main.py                    # FastAPI application
│
├── alembic/
│   ├── versions/                  # Migration files
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
├── pyproject.toml
├── pytest.ini
└── README.md
```

### 3.2 Core Configuration
```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "KitchenOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL")
    CACHE_TTL: int = 300  # 5 minutes
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL")
    
    # Tenant Settings
    MAX_TENANTS_FREE: int = 1
    MAX_BRANCHES_FREE: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Multi-tenant context
class TenantContext:
    tenant_id: str = None
    branch_id: str = None
    user_id: str = None
    
    def set(self, tenant_id: str = None, branch_id: str = None, user_id: str = None):
        self.tenant_id = tenant_id
        self.branch_id = branch_id
        self.user_id = user_id
    
    def clear(self):
        self.tenant_id = None
        self.branch_id = None
        self.user_id = None

tenant_context = TenantContext()
```

### 3.3 Database Setup
```python
# app/infrastructure/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Check connection health
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For dependency injection in FastAPI
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.4 API Dependencies (Multi-tenant)
```python
# app/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.infrastructure.database import get_db_session
from app.core.security import decode_token
from app.core.config import tenant_context

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Set tenant context
    tenant_context.set(
        tenant_id=payload.get("tenant_id"),
        branch_id=payload.get("branch_id"),
        user_id=payload.get("user_id")
    )
    
    return {
        "user_id": payload.get("user_id"),
        "tenant_id": payload.get("tenant_id"),
        "branch_id": payload.get("branch_id"),
        "role": payload.get("role")
    }

def require_role(*roles):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
```

### 3.5 Example: Order Service
```python
# app/modules/order/service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import uuid

from app.modules.order.schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate
)
from app.modules.order.repository import OrderRepository
from app.modules.order.events import OrderCreatedEvent, OrderStatusChangedEvent
from app.core.config import tenant_context

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrderRepository(db)
    
    def create_order(self, data: OrderCreate) -> OrderResponse:
        # Generate order number
        order_number = self._generate_order_number()
        
        # Calculate totals
        subtotal = sum(item.unit_price * item.quantity for item in data.items)
        tax_amount = subtotal * 0.18  # 18% GST
        total = subtotal + tax_amount - (data.discount_amount or 0)
        
        order = {
            "id": str(uuid.uuid4()),
            "order_number": order_number,
            "tenant_id": tenant_context.tenant_id,
            "branch_id": data.branch_id or tenant_context.branch_id,
            "table_id": data.table_id,
            "order_type": data.order_type,
            "status": "pending",
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total": total,
            "customer_id": data.customer_id,
            "created_by": tenant_context.user_id,
        }
        
        # Create order items
        order_items = []
        for item_data in data.items:
            order_items.append({
                "id": str(uuid.uuid4()),
                "menu_item_id": item_data.menu_item_id,
                "item_name": item_data.item_name,
                "quantity": item_data.quantity,
                "unit_price": item_data.unit_price,
                "total": item_data.unit_price * item_data.quantity,
            })
        
        result = self.repo.create_order_with_items(order, order_items)
        
        # Publish domain event (async via RabbitMQ)
        self._publish_event(OrderCreatedEvent(
            order_id=result["id"],
            order_number=order_number,
            tenant_id=order["tenant_id"],
            branch_id=order["branch_id"],
            total=total
        ))
        
        return result
    
    def update_status(self, order_id: str, new_status: str) -> OrderResponse:
        current = self.repo.get_order(order_id)
        if not current:
            raise ValueError("Order not found")
        
        old_status = current.status
        result = self.repo.update_order_status(order_id, new_status)
        
        # Publish status change event
        self._publish_event(OrderStatusChangedEvent(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=tenant_context.user_id
        ))
        
        # Trigger notifications based on status
        if new_status == "ready":
            self._notify_customer(order_id)
        
        return result
    
    def get_active_orders(self, branch_id: str = None) -> List[OrderResponse]:
        filters = {"tenant_id": tenant_context.tenant_id}
        if branch_id:
            filters["branch_id"] = branch_id
        
        return self.repo.get_orders_by_status(
            filters=filters,
            statuses=["pending", "confirmed", "preparing"]
        )
    
    def _generate_order_number(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        count = self.repo.get_today_order_count(tenant_context.tenant_id)
        return f"ORD-{today}-{count + 1:04d}"
    
    def _publish_event(self, event):
        # Async publish to RabbitMQ
        from app.infrastructure.messaging import publish
        publish("order_events", event.dict())
    
    def _notify_customer(self, order_id: str):
        from app.workers.tasks.notification_tasks import send_order_ready_notification
        send_order_ready_notification.delay(order_id)
```

---

## 4. FRONTEND ARCHITECTURE (React + TypeScript)

### 4.1 Project Structure
```
frontend/
├── apps/
│   ├── pos/                      # POS Terminal App
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── POSPage.tsx
│   │   │   │   ├── TableSelection.tsx
│   │   │   │   └── BillingPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── MenuGrid.tsx
│   │   │   │   ├── Cart.tsx
│   │   │   │   ├── OrderItem.tsx
│   │   │   │   ├── NumPad.tsx
│   │   │   │   └── PaymentModal.tsx
│   │   │   └── App.tsx
│   │   └── package.json
│   │
│   ├── admin/                    # Admin Dashboard
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── MenuManagement.tsx
│   │   │   │   ├── OrderHistory.tsx
│   │   │   │   ├── Reports.tsx
│   │   │   │   └── Settings.tsx
│   │   │   └── components/
│   │   └── package.json
│   │
│   ├── kds/                      # Kitchen Display System
│   │   └── src/
│   │       ├── pages/
│   │       │   └── KDSBoard.tsx
│   │       └── components/
│   │           ├── OrderCard.tsx
│   │           └── Timer.tsx
│   │
│   └── super-admin/              # SaaS Super Admin
│       └── src/
│           ├── pages/
│           │   ├── TenantManagement.tsx
│           │   └── SystemAnalytics.tsx
│           └── components/
│
├── packages/
│   ├── ui/                       # Shared UI Components
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Modal/
│   │   ├── Table/
│   │   ├── Card/
│   │   ├── Badge/
│   │   └── Select/
│   ├── hooks/                    # Shared Hooks
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   ├── useWebSocket.ts
│   │   └── useToast.ts
│   ├── stores/                   # Zustand Stores
│   │   ├── authStore.ts
│   │   ├── orderStore.ts
│   │   ├── menuStore.ts
│   │   └── settingsStore.ts
│   ├── api/                      # API Client
│   │   ├── client.ts
│   │   ├── endpoints/
│   │   │   ├── auth.ts
│   │   │   ├── orders.ts
│   │   │   ├── menu.ts
│   │   │   └── billing.ts
│   │   └── interceptors.ts
│   └── types/                    # Shared Types
│       ├── api.ts
│       ├── order.ts
│       └── menu.ts
│
├── infrastructure/
│   ├── docker/
│   └── k8s/
│
├── pnpm-workspace.yaml
├── turbo.json
└── package.json
```

### 4.2 State Management (Zustand)
```typescript
// packages/stores/orderStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CartItem {
  id: string;
  menuItemId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  variants?: { id: string; name: string; price: number }[];
  modifiers?: { id: string; name: string; price: number }[];
  notes?: string;
}

interface OrderState {
  // Current order
  currentOrder: {
    id?: string;
    orderNumber?: string;
    type: 'dine_in' | 'takeaway' | 'delivery';
    tableId?: string;
    items: CartItem[];
    customerId?: string;
    notes?: string;
  };
  
  // Actions
  addItem: (item: CartItem) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
  updateItemModifiers: (itemId: string, modifiers: CartItem['modifiers']) => void;
  setOrderType: (type: OrderState['currentOrder']['type']) => void;
  setTableId: (tableId: string) => void;
  setCustomerId: (customerId: string) => void;
  clearCart: () => void;
  
  // Computed
  getSubtotal: () => number;
  getTax: () => number;
  getTotal: () => number;
  getItemCount: () => number;
}

export const useOrderStore = create<OrderState>()(
  persist(
    (set, get) => ({
      currentOrder: {
        type: 'dine_in',
        items: [],
      },
      
      addItem: (item) => set((state) => ({
        currentOrder: {
          ...state.currentOrder,
          items: [...state.currentOrder.items, { ...item, id: crypto.randomUUID() }]
        }
      })),
      
      updateItemQuantity: (itemId, quantity) => set((state) => ({
        currentOrder: {
          ...state.currentOrder,
          items: state.currentOrder.items.map(item =>
            item.id === itemId ? { ...item, quantity } : item
          )
        }
      })),
      
      removeItem: (itemId) => set((state) => ({
        currentOrder: {
          ...state.currentOrder,
          items: state.currentOrder.items.filter(item => item.id !== itemId)
        }
      })),
      
      setOrderType: (type) => set((state) => ({
        currentOrder: { ...state.currentOrder, type }
      })),
      
      setTableId: (tableId) => set((state) => ({
        currentOrder: { ...state.currentOrder, tableId }
      })),
      
      setCustomerId: (customerId) => set((state) => ({
        currentOrder: { ...state.currentOrder, customerId }
      })),
      
      clearCart: () => set({
        currentOrder: { type: 'dine_in', items: [] }
      }),
      
      getSubtotal: () => {
        const items = get().currentOrder.items;
        return items.reduce((sum, item) => {
          const basePrice = item.unitPrice * item.quantity;
          const variantPrice = (item.variants || []).reduce((v, w) => v + w.price, 0) * item.quantity;
          const modPrice = (item.modifiers || []).reduce((m, n) => m + n.price, 0) * item.quantity;
          return sum + basePrice + variantPrice + modPrice;
        }, 0);
      },
      
      getTax: () => get().getSubtotal() * 0.18, // 18% GST
      getTotal: () => get().getSubtotal() + get().getTax(),
      getItemCount: () => get().currentOrder.items.reduce((sum, item) => sum + item.quantity, 0),
    }),
    { name: 'pos-order-store' }
  )
);
```

### 4.3 WebSocket Hook
```typescript
// packages/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useOrderStore } from '../stores/orderStore';

interface WebSocketMessage {
  event: string;
  data: any;
}

export function useWebSocket(branchId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const { addItem, updateItemQuantity } = useOrderStore();
  
  const connect = useCallback(() => {
    const wsUrl = `${process.env.WS_URL}/ws/kds/${branchId}`;
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };
    
    wsRef.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      switch (message.event) {
        case 'kds:new_order':
          // Show notification, update order list
          break;
        case 'kds:order_update':
          // Update prep status
          break;
        case 'kds:order_completed':
          // Remove from KDS, trigger notification
          break;
      }
    };
    
    wsRef.current.onclose = () => {
      // Reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 5000);
    };
  }, [branchId]);
  
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
  
  return wsRef.current;
}
```

### 4.4 POS Page Component
```typescript
// apps/pos/src/pages/POSPage.tsx
import React, { useState, useEffect } from 'react';
import { useOrderStore } from '@restropop/stores/orderStore';
import { useMenuStore } from '@restropop/stores/menuStore';
import { MenuGrid } from '../components/MenuGrid';
import { Cart } from '../components/Cart';
import { NumPad } from '../components/NumPad';
import { PaymentModal } from '../components/PaymentModal';

export function POSPage() {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [showPayment, setShowPayment] = useState(false);
  const { currentOrder, addItem } = useOrderStore();
  const { categories, menuItems, fetchMenu } = useMenuStore();
  
  useEffect(() => {
    fetchMenu();
  }, []);
  
  const filteredItems = activeCategory
    ? menuItems.filter(item => item.categoryId === activeCategory)
    : menuItems;
  
  const handleAddToCart = (item: any) => {
    addItem({
      id: crypto.randomUUID(),
      menuItemId: item.id,
      name: item.name,
      quantity: 1,
      unitPrice: item.basePrice,
    });
  };
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Panel - Menu */}
      <div className="flex-1 flex flex-col">
        {/* Category Tabs */}
        <div className="bg-white border-b px-4 py-2 flex gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-4 py-2 rounded-lg whitespace-nowrap ${
              !activeCategory ? 'bg-primary text-white' : 'bg-gray-100'
            }`}
          >
            All Items
          </button>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap ${
                activeCategory === cat.id ? 'bg-primary text-white' : 'bg-gray-100'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
        
        {/* Menu Grid */}
        <div className="flex-1 p-4 overflow-auto">
          <MenuGrid
            items={filteredItems}
            onItemClick={handleAddToCart}
          />
        </div>
      </div>
      
      {/* Right Panel - Cart & Billing */}
      <div className="w-96 bg-white border-l flex flex-col">
        <Cart />
        
        {/* Billing Summary */}
        <div className="border-t p-4 space-y-2">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>₹{useOrderStore.getState().getSubtotal().toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-green-600">
            <span>Tax (GST 18%)</span>
            <span>₹{useOrderStore.getState().getTax().toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-bold text-lg border-t pt-2">
            <span>Total</span>
            <span>₹{useOrderStore.getState().getTotal().toFixed(2)}</span>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="p-4 space-y-2">
          <button
            onClick={() => setShowPayment(true)}
            disabled={currentOrder.items.length === 0}
            className="w-full py-4 bg-green-600 text-white rounded-lg font-semibold disabled:bg-gray-300"
          >
            Pay ₹{useOrderStore.getState().getTotal().toFixed(2)}
          </button>
          <button className="w-full py-3 bg-gray-200 rounded-lg">
            Hold Order
          </button>
        </div>
      </div>
      
      {/* Payment Modal */}
      {showPayment && (
        <PaymentModal
          amount={useOrderStore.getState().getTotal()}
          onClose={() => setShowPayment(false)}
          onSuccess={() => {
            setShowPayment(false);
            useOrderStore.getState().clearCart();
          }}
        />
      )}
    </div>
  );
}
```

---

## 5. REAL-TIME ARCHITECTURE

### 5.1 WebSocket Event Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  POS/KDS    │────►│   Redis     │────►│  All KDS    │
│  Clients    │     │   Pub/Sub   │     │  Clients    │
└─────────────┘     └─────────────┘     └─────────────┘
                          ▲
                          │
┌─────────────┐     ┌─────────────┐
│   Backend   │────►│  RabbitMQ   │
│   Service   │     │  (Events)   │
└─────────────┘     └─────────────┘
```

### 5.2 WebSocket Manager
```python
# app/infrastructure/websocket.py
from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        # branch_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user info
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, branch_id: str, user_info: dict):
        await websocket.accept()
        
        if branch_id not in self.active_connections:
            self.active_connections[branch_id] = set()
        
        self.active_connections[branch_id].add(websocket)
        self.connection_info[websocket] = {"branch_id": branch_id, **user_info}
    
    def disconnect(self, websocket: WebSocket):
        info = self.connection_info.get(websocket)
        if info:
            branch_id = info.get("branch_id")
            if branch_id and branch_id in self.active_connections:
                self.active_connections[branch_id].discard(websocket)
        self.connection_info.pop(websocket, None)
    
    async def send_to_branch(self, branch_id: str, event: str, data: dict):
        if branch_id not in self.active_connections:
            return
        
        message = json.dumps({"event": event, "data": data})
        
        # Send to all connections in branch
        disconnected = []
        for websocket in self.active_connections[branch_id]:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)
        
        # Clean up disconnected
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast(self, event: str, data: dict):
        for branch_id in self.active_connections:
            await self.send_to_branch(branch_id, event, data)

manager = ConnectionManager()

# Domain event handlers
async def handle_order_created(event: dict):
    await manager.send_to_branch(
        event["branch_id"],
        "kds:new_order",
        {
            "order_id": event["order_id"],
            "order_number": event["order_number"],
            "items": event["items"],
            "created_at": event["created_at"]
        }
    )

async def handle_order_status_changed(event: dict):
    await manager.send_to_branch(
        event["branch_id"],
        "kds:order_update",
        {
            "order_id": event["order_id"],
            "old_status": event["old_status"],
            "new_status": event["new_status"]
        }
    )
```

---

## 6. INFRASTRUCTURE (Docker + Oracle Cloud)

### 6.1 Docker Compose (Development)
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/restropop
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
    depends_on:
      - db
      - redis
      - rabbitmq
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=restropop
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"

  pgadmin:
    image: dpage/pgadmin4
    ports:
      - "5050:80"
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@restropop.com
      - PGADMIN_DEFAULT_PASSWORD=admin

volumes:
  pgdata:
```

### 6.2 Docker Compose (Oracle Cloud Production)
```yaml
version: '3.8'

services:
  backend:
    image: ${REGISTRY}/restropop-backend:${TAG}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
      - rabbitmq
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    image: ${REGISTRY}/restropop-backend:${TAG}
    command: celery -A app.workers.celery_app worker --loglevel=info
    deploy:
      replicas: 2
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_URL=${RABBITMQ_URL}
    depends_on:
      - db
      - redis
      - rabbitmq

  frontend:
    image: ${REGISTRY}/restropop-frontend:${TAG}
    deploy:
      replicas: 2
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - pgdata:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
    volumes:
      - redisdata:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend

volumes:
  pgdata:
  redisdata:

networks:
  default:
    driver: overlay
```

### 6.3 Oracle Cloud Setup
```bash
# Oracle Cloud Infrastructure Requirements

# 1. Compute Instance (for container deployment)
# Shape: VM.Standard3.Flex (2 OCPU, 16GB RAM minimum)
# OS: Oracle Linux 8

# 2. Database (Autonomous Database or self-managed PostgreSQL)
# For MVP: Self-managed on compute
# For Production: Oracle Autonomous Database with pg_connect

# 3. Networking
# - Create VCN with public subnets
# - Configure security lists for ports 80, 443, 22
# - Load Balancer for HA

# 4. Storage
# - Block volume for database (500GB minimum)
# - Object storage for backups

# Deployment steps:
# 1. SSH to instance
# 2. Install Docker and Docker Compose
# 3. Clone repository
# 4. Set environment variables
# 5. docker-compose -f docker-compose.prod.yml up -d
```

### 6.4 NGINX Configuration
```nginx
# nginx.conf (Production)
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/s;
    
    upstream backend {
        least_conn;
        server backend:8000;
        keepalive 32;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Redirect to HTTPS (uncomment when SSL is configured)
        # return 301 https://$host$request_uri;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # WebSocket endpoints
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 86400;
        }
        
        # Frontend (React build)
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
                proxy_pass http://frontend;
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # Health check endpoint
        location /health {
            proxy_pass http://backend;
            access_log off;
        }
    }
}
```

---

## 7. CELERY BACKGROUND TASKS

### 7.1 Celery Configuration
```python
# app/workers/celery_app.py
from celery import Celery
from celery.schedules import crontab
import os

celery_app = Celery(
    "restropop",
    broker=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379"),
    include=[
        "app.workers.tasks.order_tasks",
        "app.workers.tasks.notification_tasks",
        "app.workers.tasks.report_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=4,
    worker_concurrency=4,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "app.workers.tasks.auth_tasks.cleanup_expired_tokens",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "generate-daily-reports": {
        "task": "app.workers.tasks.report_tasks.generate_daily_summary",
        "schedule": crontab(minute=30, hour=0),  # Midnight + 30 min
    },
    "check-low-stock": {
        "task": "app.workers.tasks.inventory_tasks.check_low_stock_alerts",
        "schedule": crontab(minute=0, hour=8),  # 8 AM daily
    },
    "expire-loyalty-points": {
        "task": "app.workers.tasks.loyalty_tasks.expire_points",
        "schedule": crontab(minute=0, hour=1),  # 1 AM daily
    },
}
```

### 7.2 Example Tasks
```python
# app/workers/tasks/notification_tasks.py
from app.workers.celery_app import celery_app
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_order_ready_notification(self, order_id: str):
    """
    Send notification when order is ready for pickup/delivery
    """
    from app.infrastructure.database import get_db_session
    from app.modules.notification.service import NotificationService
    
    try:
        db = next(get_db_session())
        service = NotificationService(db)
        
        # Get order details
        order = service.get_order(order_id)
        if not order:
            logger.warning(f"Order {order_id} not found for notification")
            return
        
        # Send SMS
        if order.customer_phone:
            service.send_sms(
                phone=order.customer_phone,
                message=f"Your order #{order.order_number} is ready for pickup!"
            )
        
        # Send WhatsApp
        if order.customer_phone:
            service.send_whatsapp(
                phone=order.customer_phone,
                template="order_ready",
                params={"order_number": order.order_number}
            )
        
        logger.info(f"Notification sent for order {order_id}")
        
    except Exception as e:
        logger.error(f"Failed to send notification for order {order_id}: {e}")
        raise self.retry(exc=e)

@celery_app.task
def send_daily_summary(tenant_id: str, branch_id: str):
    """
    Generate and send daily sales summary to manager
    """
    from app.infrastructure.database import get_db_session
    from app.modules.reports.service import ReportService
    
    db = next(get_db_session())
    service = ReportService(db)
    
    report = service.generate_daily_summary(tenant_id, branch_id)
    
    # Get branch manager email
    # Send email with report
    
    return report

@celery_app.task
def process_delayed_order_actions(order_id: str, action: str):
    """
    Process actions that need to happen after a delay
    e.g., auto-cancel unpaid orders after 30 minutes
    """
    from app.infrastructure.database import get_db_session
    from app.modules.order.service import OrderService
    
    db = next(get_db_session())
    service = OrderService(db)
    
    if action == "auto_cancel":
        service.cancel_if_unpaid(order_id)
```

---

## 8. API CONTRACTS

### 8.1 Authentication

```typescript
// POST /api/v1/auth/register
interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  phone: string;
  business_type: 'restaurant' | 'cafe' | 'cloud_kitchen' | 'qsr';
}

interface RegisterResponse {
  tenant: Tenant;
  user: User;
  access_token: string;
  refresh_token: string;
}

// POST /api/v1/auth/login
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

// POST /api/v1/auth/refresh
interface RefreshRequest {
  refresh_token: string;
}

interface RefreshResponse {
  access_token: string;
  expires_in: number;
}
```

### 8.2 Orders

```typescript
// POST /api/v1/orders
interface CreateOrderRequest {
  branch_id?: string;
  table_id?: string;
  order_type: 'dine_in' | 'takeaway' | 'delivery' | 'qr';
  customer_id?: string;
  items: OrderItemRequest[];
  discount_amount?: number;
  notes?: string;
}

interface OrderItemRequest {
  menu_item_id: string;
  item_name: string;
  quantity: number;
  unit_price: number;
  variant_id?: string;
  modifiers?: { id: string; name: string; price: number }[];
  notes?: string;
}

interface OrderResponse {
  id: string;
  order_number: string;
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'completed' | 'cancelled';
  order_type: string;
  items: OrderItemResponse[];
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total: number;
  payment_status: 'pending' | 'partial' | 'paid' | 'refunded';
  created_at: string;
}

// PUT /api/v1/orders/{id}/status
interface UpdateOrderStatusRequest {
  status: string;
  notes?: string;
}
```

### 8.3 Billing

```typescript
// POST /api/v1/billing/generate
interface GenerateBillRequest {
  order_id: string;
  discount_amount?: number;
  tip_amount?: number;
  apply_coupon?: string;
}

interface BillResponse {
  order_id: string;
  order_number: string;
  subtotal: number;
  tax_breakdown: { name: string; rate: number; amount: number }[];
  tax_total: number;
  discount_amount: number;
  tip_amount: number;
  total: number;
  amount_paid: number;
  amount_due: number;
}

// POST /api/v1/payments
interface ProcessPaymentRequest {
  order_id: string;
  amount: number;
  payment_method: 'cash' | 'card' | 'UPI' | 'wallet' | 'razorpay' | 'stripe';
  gateway_reference_id?: string;
  idempotency_key: string;
}

interface PaymentResponse {
  id: string;
  order_id: string;
  amount: number;
  status: 'pending' | 'success' | 'failed' | 'refunded';
  payment_method: string;
  transaction_id?: string;
  processed_at: string;
}

// POST /api/v1/payments/{id}/refund
interface RefundRequest {
  amount?: number;  // Partial refund amount
  reason: string;
}
```

---

## 9. 2-DAY IMPLEMENTATION ROADMAP

### Day 1: Foundation + Core Backend (0-12 hours)

| Hour | Task | Deliverables |
|------|------|--------------|
| 0-1 | Project scaffolding, Docker setup | Repository initialized, Docker working |
| 1-2 | Database models + Alembic migrations | All core tables created |
| 2-3 | JWT authentication endpoints | Login, register, refresh working |
| 3-4 | Tenant/Branch/User CRUD | Full admin CRUD API |
| 4-5 | Menu category/item CRUD | Full menu management API |
| 5-6 | Order creation API | Create orders with items |
| 6-7 | Billing API + GST calculation | Generate bills, calculate taxes |
| 7-8 | Payment processing | Cash/card payment handling |
| 8-10 | Celery setup + notification tasks | Background task infrastructure |
| 10-12 | API testing + documentation | OpenAPI docs, test with Postman |

### Day 2: Frontend + Deployment (0-12 hours)

| Hour | Task | Deliverables |
|------|------|--------------|
| 0-1 | React + Vite scaffold, routing | Frontend project ready |
| 1-2 | Auth context + API client | Login flow working |
| 2-3 | Menu display + category tabs | Menu grid UI |
| 3-4 | Cart functionality | Add/remove items, quantity update |
| 5-6 | POS page complete | Full POS interface |
| 6-7 | Billing page + payment modal | Payment flow |
| 7-8 | Basic KDS display | Kitchen order view |
| 8-9 | WebSocket integration | Real-time updates |
| 9-10 | Docker Compose production config | docker-compose.prod.yml |
| 10-11 | Oracle Cloud deployment | Running on OCI |
| 11-12 | Testing + bug fixes | Working production system |

---

## 10. PRODUCTION READINESS CHECKLIST

### Infrastructure
- [ ] PostgreSQL configured with connection pooling (PgBouncer)
- [ ] Redis configured with persistence
- [ ] RabbitMQ with durable queues
- [ ] Multi-container orchestration
- [ ] Health check endpoints
- [ ] Graceful shutdown configured

### Security
- [ ] JWT with refresh token rotation
- [ ] Password hashing with bcrypt
- [ ] Rate limiting configured
- [ ] Security headers (CSP, HSTS, etc.)
- [ ] Audit logging enabled
- [ ] Secrets via environment variables

### Monitoring
- [ ] Prometheus metrics endpoint
- [ ] Structured logging (JSON)
- [ ] Request ID tracing
- [ ] Health check endpoint
- [ ] Error tracking

### Backup & Recovery
- [ ] Automated database backups
- [ ] Backup restoration tested
- [ ] RTO/RPO defined

### Scalability Ready
- [ ] Stateless application design
- [ ] External session storage (Redis)
- [ ] Database connection pooling
- [ ] Asset CDN configuration
- [ ] Auto-scaling configuration

---

## 11. POST-MVP ROADMAP

| Phase | Features | Timeline |
|-------|----------|----------|
| Week 1-2 | Inventory management, vendor CRUD, purchase orders | Week 3-4 |
| Week 3-4 | KDS real-time display, chef assignment, timers | Week 5-6 |
| Week 5-6 | CRM, customer profiles, loyalty points | Week 7-8 |
| Week 7-8 | Analytics dashboard, reports, export | Week 9-10 |
| Week 9-10 | Employee management, shifts, attendance | Week 11-12 |
| Week 11-12 | Payment gateway integrations, aggregators | Week 13-14 |
| Week 13-14 | Multi-branch sync, franchise management | Week 15-16 |
| Week 15-16 | Super admin panel, subscription billing | Week 17-18 |

---

This plan provides a **production-ready, scalable foundation** that can handle real restaurant operations from day 1, with clear paths to expand into the full enterprise platform.
