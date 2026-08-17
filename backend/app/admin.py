from sqladmin import ModelView
from app.models import Product, Bar, Stock, Order, OrderItem, SupplyInvoice, SupplyItem

class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.sku, Product.name, Product.category, Product.unit, Product.is_active]
    column_searchable_list = [Product.name, Product.sku, Product.category]
    column_sortable_list = [Product.id, Product.name, Product.category]
    column_default_sort = "id"
    name = "Product"
    name_plural = "Products"
    icon = "fa-solid fa-box"
    page_size = 50


class BarAdmin(ModelView, model=Bar):
    column_list = [Bar.id, Bar.name, Bar.telegram_chat_id, Bar.is_active]
    column_searchable_list = [Bar.name]
    column_sortable_list = [Bar.id, Bar.name]
    column_default_sort = "id"
    name = "Coffee Bar"
    name_plural = "Coffee Bars"
    icon = "fa-solid fa-store"


class StockAdmin(ModelView, model=Stock):
    column_list = [Stock.id, Stock.product_id, Stock.product, Stock.real_qty, Stock.reserved_qty, Stock.available_qty]
    column_searchable_list = [Stock.product_id]
    column_sortable_list = [Stock.id, Stock.real_qty, Stock.reserved_qty]
    column_default_sort = "id"
    name = "Stock"
    name_plural = "Stocks"
    icon = "fa-solid fa-cubes"


class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.bar_id, Order.status, Order.created_at, Order.updated_at]
    column_searchable_list = [Order.id]
    column_sortable_list = [Order.id, Order.created_at, Order.status]
    column_default_sort = [("created_at", True)]
    name = "Order"
    name_plural = "Orders"
    icon = "fa-solid fa-shopping-cart"


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [OrderItem.id, OrderItem.order_id, OrderItem.product_id, OrderItem.requested_qty, OrderItem.confirmed_qty]
    column_searchable_list = [OrderItem.order_id, OrderItem.product_id]
    column_sortable_list = [OrderItem.id, OrderItem.order_id]
    name = "Order Item"
    name_plural = "Order Items"
    icon = "fa-solid fa-list-ol"


class SupplyInvoiceAdmin(ModelView, model=SupplyInvoice):
    column_list = [SupplyInvoice.id, SupplyInvoice.invoice_number, SupplyInvoice.status, SupplyInvoice.created_at, SupplyInvoice.photo_file_id]
    column_searchable_list = [SupplyInvoice.invoice_number]
    column_sortable_list = [SupplyInvoice.id, SupplyInvoice.created_at, SupplyInvoice.status]
    column_default_sort = [("created_at", True)]
    name = "Supply Invoice"
    name_plural = "Supply Invoices"
    icon = "fa-solid fa-file-invoice"


class SupplyItemAdmin(ModelView, model=SupplyItem):
    column_list = [SupplyItem.id, SupplyItem.invoice_id, SupplyItem.product_id, SupplyItem.quantity, SupplyItem.detected_name, SupplyItem.confidence_score]
    column_searchable_list = [SupplyItem.invoice_id, SupplyItem.product_id]
    column_sortable_list = [SupplyItem.id, SupplyItem.invoice_id]
    name = "Supply Item"
    name_plural = "Supply Items"
    icon = "fa-solid fa-boxes-packing"
