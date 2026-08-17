from sqladmin import ModelView
from app.models import Product, Bar, Stock, Order, OrderItem, SupplyInvoice, SupplyItem

class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.sku, Product.name, Product.category, Product.unit, Product.is_active]
    column_searchable_list = [Product.name, Product.sku, Product.category]
    column_sortable_list = [Product.id, Product.name, Product.category]
    column_default_sort = "id"
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"
    page_size = 50
    column_labels = {
        Product.id: "ID",
        Product.sku: "Артикул",
        Product.name: "Название",
        Product.category: "Категория",
        Product.unit: "Ед. изм.",
        Product.is_active: "Активен",
        Product.stock: "Остаток",
    }


class BarAdmin(ModelView, model=Bar):
    column_list = [Bar.id, Bar.name, Bar.telegram_chat_id, Bar.is_active]
    column_searchable_list = [Bar.name]
    column_sortable_list = [Bar.id, Bar.name]
    column_default_sort = "id"
    name = "Кофейня"
    name_plural = "Кофейни"
    icon = "fa-solid fa-store"
    column_labels = {
        Bar.id: "ID",
        Bar.name: "Название",
        Bar.telegram_chat_id: "ID Чата",
        Bar.is_active: "Активна",
    }


class StockAdmin(ModelView, model=Stock):
    column_list = [Stock.id, Stock.product_id, Stock.product, Stock.real_qty, Stock.reserved_qty, Stock.available_qty]
    column_searchable_list = [Stock.product_id]
    column_sortable_list = [Stock.id, Stock.real_qty, Stock.reserved_qty]
    column_default_sort = "id"
    name = "Остаток"
    name_plural = "Остатки"
    icon = "fa-solid fa-cubes"
    column_labels = {
        Stock.id: "ID",
        Stock.product_id: "ID Товара",
        Stock.product: "Товар",
        Stock.real_qty: "Фактический остаток",
        Stock.reserved_qty: "Резерв",
        Stock.available_qty: "Доступно",
    }


class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.bar_id, Order.status, Order.created_at, Order.updated_at]
    column_searchable_list = [Order.id]
    column_sortable_list = [Order.id, Order.created_at, Order.status]
    column_default_sort = [("created_at", True)]
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-shopping-cart"
    column_labels = {
        Order.id: "ID",
        Order.bar_id: "Кофейня",
        Order.status: "Статус",
        Order.created_at: "Создан",
        Order.updated_at: "Обновлен",
    }


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [OrderItem.id, OrderItem.order_id, OrderItem.product_id, OrderItem.requested_qty, OrderItem.confirmed_qty]
    column_searchable_list = [OrderItem.order_id, OrderItem.product_id]
    column_sortable_list = [OrderItem.id, OrderItem.order_id]
    name = "Позиция заказа"
    name_plural = "Позиции заказа"
    icon = "fa-solid fa-list-ol"
    column_labels = {
        OrderItem.id: "ID",
        OrderItem.order_id: "ID Заказа",
        OrderItem.product_id: "ID Товара",
        OrderItem.requested_qty: "Запрошено",
        OrderItem.confirmed_qty: "Собрано",
    }


class SupplyInvoiceAdmin(ModelView, model=SupplyInvoice):
    column_list = [SupplyInvoice.id, SupplyInvoice.invoice_number, SupplyInvoice.status, SupplyInvoice.created_at, SupplyInvoice.photo_file_id]
    column_searchable_list = [SupplyInvoice.invoice_number]
    column_sortable_list = [SupplyInvoice.id, SupplyInvoice.created_at, SupplyInvoice.status]
    column_default_sort = [("created_at", True)]
    name = "Накладная"
    name_plural = "Накладные"
    icon = "fa-solid fa-file-invoice"
    column_labels = {
        SupplyInvoice.id: "ID",
        SupplyInvoice.invoice_number: "Номер",
        SupplyInvoice.status: "Статус",
        SupplyInvoice.created_at: "Создана",
        SupplyInvoice.photo_file_id: "Фото",
    }


class SupplyItemAdmin(ModelView, model=SupplyItem):
    column_list = [SupplyItem.id, SupplyItem.invoice_id, SupplyItem.product_id, SupplyItem.quantity, SupplyItem.detected_name, SupplyItem.confidence_score]
    column_searchable_list = [SupplyItem.invoice_id, SupplyItem.product_id]
    column_sortable_list = [SupplyItem.id, SupplyItem.invoice_id]
    name = "Позиция накладной"
    name_plural = "Позиции накладных"
    icon = "fa-solid fa-boxes-packing"
    column_labels = {
        SupplyItem.id: "ID",
        SupplyItem.invoice_id: "ID Накладной",
        SupplyItem.product_id: "ID Товара",
        SupplyItem.quantity: "Кол-во",
        SupplyItem.detected_name: "Распознанное имя",
        SupplyItem.confidence_score: "Уверенность",
    }
