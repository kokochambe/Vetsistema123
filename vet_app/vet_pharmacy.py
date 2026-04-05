#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ветеринарная аптека - Система управления запасами и продажами
Рабочая программа на Python с использованием tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional
import json
import os


@dataclass
class Product:
    """Класс товара"""
    id: int
    name: str
    category: str
    price: float
    quantity: int
    unit: str
    manufacturer: str
    expiration_date: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'quantity': self.quantity,
            'unit': self.unit,
            'manufacturer': self.manufacturer,
            'expiration_date': self.expiration_date
        }


@dataclass
class SaleItem:
    """Элемент продажи"""
    product_id: int
    product_name: str
    quantity: int
    price: float
    
    @property
    def subtotal(self) -> float:
        return self.quantity * self.price


@dataclass
class Sale:
    """Продажа"""
    id: int
    date: str
    items: List[SaleItem]
    total_amount: float
    customer_name: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'items': [{'product_id': i.product_id, 'product_name': i.product_name, 
                      'quantity': i.quantity, 'price': i.price} for i in self.items],
            'total_amount': self.total_amount,
            'customer_name': self.customer_name
        }


class Database:
    """Класс базы данных (хранение в памяти + JSON файл)"""
    
    CATEGORIES = ["Корма", "Лекарства", "Аксессуары", "Гигиена", "Витамины"]
    UNITS = ["шт", "кг", "г", "л", "мл", "уп", "фл", "таб"]
    
    def __init__(self, db_file="vet_data.json"):
        self.db_file = db_file
        self.products: List[Product] = []
        self.sales: List[Sale] = []
        self.load_data()
        
        if not self.products:
            self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Инициализация тестовыми данными"""
        sample_products = [
            Product(1, "Royal Canin Adult Dog", "Корма", 2500, 50, "кг", "Royal Canin", 
                   (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y")),
            Product(2, "Whiskas для кошек", "Корма", 450, 100, "шт", "Mars",
                   (datetime.now() + timedelta(days=240)).strftime("%d.%m.%Y")),
            Product(3, "Амоксициллин вет.", "Лекарства", 350, 30, "фл", "Нита-Фарм",
                   (datetime.now() + timedelta(days=540)).strftime("%d.%m.%Y")),
            Product(4, "Ошейник от блох", "Аксессуары", 890, 25, "шт", "Beaphar",
                   (datetime.now() + timedelta(days=730)).strftime("%d.%m.%Y")),
            Product(5, "Шампунь для собак", "Гигиена", 650, 40, "мл", "Bio-Groom",
                   (datetime.now() + timedelta(days=720)).strftime("%d.%m.%Y")),
            Product(6, "Гамавит", "Лекарства", 280, 15, "фл", "Микроген",
                   (datetime.now() + timedelta(days=180)).strftime("%d.%m.%Y")),
            Product(7, "Корм Pro Plan", "Корма", 1800, 8, "кг", "Purina",
                   (datetime.now() + timedelta(days=300)).strftime("%d.%m.%Y")),
        ]
        self.products.extend(sample_products)
        self.save_data()
    
    def save_data(self):
        """Сохранение данных в JSON файл"""
        try:
            data = {
                'products': [p.to_dict() for p in self.products],
                'sales': [s.to_dict() for s in self.sales]
            }
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def load_data(self):
        """Загрузка данных из JSON файла"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.products = [Product(**p) for p in data.get('products', [])]
                sales_data = data.get('sales', [])
                self.sales = []
                for s in sales_data:
                    items = [SaleItem(**i) for i in s.get('items', [])]
                    sale = Sale(s['id'], s['date'], items, s['total_amount'], s['customer_name'])
                    self.sales.append(sale)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.products = []
            self.sales = []
    
    def add_product(self, product: Product) -> bool:
        """Добавление товара"""
        try:
            max_id = max((p.id for p in self.products), default=0)
            product.id = max_id + 1
            self.products.append(product)
            self.save_data()
            return True
        except Exception as e:
            print(f"Ошибка добавления: {e}")
            return False
    
    def update_product(self, product: Product) -> bool:
        """Обновление товара"""
        try:
            for i, p in enumerate(self.products):
                if p.id == product.id:
                    self.products[i] = product
                    self.save_data()
                    return True
            return False
        except Exception as e:
            print(f"Ошибка обновления: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Удаление товара"""
        try:
            self.products = [p for p in self.products if p.id != product_id]
            self.save_data()
            return True
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID"""
        for p in self.products:
            if p.id == product_id:
                return p
        return None
    
    def create_sale(self, items: List[SaleItem], customer_name: str) -> Optional[Sale]:
        """Создание продажи"""
        try:
            # Проверяем наличие товаров
            for item in items:
                product = self.get_product_by_id(item.product_id)
                if not product or product.quantity < item.quantity:
                    return None
            
            # Уменьшаем количество
            for item in items:
                product = self.get_product_by_id(item.product_id)
                if product:
                    product.quantity -= item.quantity
            
            # Создаем продажу
            max_id = max((s.id for s in self.sales), default=0)
            total = sum(item.subtotal for item in items)
            sale = Sale(
                id=max_id + 1,
                date=datetime.now().strftime("%d.%m.%Y %H:%M"),
                items=items,
                total_amount=total,
                customer_name=customer_name or "Розничный покупатель"
            )
            self.sales.append(sale)
            self.save_data()
            return sale
        except Exception as e:
            print(f"Ошибка создания продажи: {e}")
            return None
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Получение товаров с низким запасом"""
        return [p for p in self.products if p.quantity <= threshold]
    
    def get_expiring_products(self, days: int = 30) -> List[Product]:
        """Получение товаров с истекающим сроком"""
        expiring = []
        today = datetime.now()
        for p in self.products:
            try:
                exp_date = datetime.strptime(p.expiration_date, "%d.%m.%Y")
                if (exp_date - today).days <= days:
                    expiring.append(p)
            except:
                pass
        return expiring


class ProductDialog(tk.Toplevel):
    """Диалог добавления/редактирования товара"""
    
    def __init__(self, parent, db: Database, product: Optional[Product] = None):
        super().__init__(parent)
        self.db = db
        self.product = product
        self.result = None
        
        self.title("Редактирование товара" if product else "Добавление товара")
        self.geometry("400x500+400+200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название
        ttk.Label(main_frame, text="Название товара:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Категория
        ttk.Label(main_frame, text="Категория:").pack(anchor=tk.W)
        self.category_combo = ttk.Combobox(main_frame, values=self.db.CATEGORIES, state="readonly", width=37)
        self.category_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Цена
        ttk.Label(main_frame, text="Цена (₽):").pack(anchor=tk.W)
        self.price_entry = ttk.Entry(main_frame, width=40)
        self.price_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Количество
        ttk.Label(main_frame, text="Количество:").pack(anchor=tk.W)
        self.quantity_entry = ttk.Entry(main_frame, width=40)
        self.quantity_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Единица измерения
        ttk.Label(main_frame, text="Единица измерения:").pack(anchor=tk.W)
        self.unit_combo = ttk.Combobox(main_frame, values=self.db.UNITS, state="readonly", width=37)
        self.unit_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Производитель
        ttk.Label(main_frame, text="Производитель:").pack(anchor=tk.W)
        self.manufacturer_entry = ttk.Entry(main_frame, width=40)
        self.manufacturer_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Срок годности
        ttk.Label(main_frame, text="Срок годности (ДД.ММ.ГГГГ):").pack(anchor=tk.W)
        self.exp_date_entry = ttk.Entry(main_frame, width=40)
        self.exp_date_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.RIGHT)
        
        # Заполнение данными при редактировании
        if self.product:
            self.name_entry.insert(0, self.product.name)
            self.category_combo.set(self.product.category)
            self.price_entry.insert(0, str(self.product.price))
            self.quantity_entry.insert(0, str(self.product.quantity))
            self.unit_combo.set(self.product.unit)
            self.manufacturer_entry.insert(0, self.product.manufacturer)
            self.exp_date_entry.insert(0, self.product.expiration_date)
        else:
            # Значения по умолчанию
            self.category_combo.current(0)
            self.unit_combo.current(0)
            tomorrow = (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y")
            self.exp_date_entry.insert(0, tomorrow)
    
    def validate_input(self) -> bool:
        """Проверка введенных данных"""
        if not self.name_entry.get().strip():
            messagebox.showwarning("Ошибка", "Введите название товара")
            return False
        
        if not self.category_combo.get():
            messagebox.showwarning("Ошибка", "Выберите категорию")
            return False
        
        try:
            price = float(self.price_entry.get())
            if price <= 0:
                raise ValueError()
        except:
            messagebox.showwarning("Ошибка", "Введите корректную цену")
            return False
        
        try:
            quantity = int(self.quantity_entry.get())
            if quantity < 0:
                raise ValueError()
        except:
            messagebox.showwarning("Ошибка", "Введите корректное количество")
            return False
        
        if not self.manufacturer_entry.get().strip():
            messagebox.showwarning("Ошибка", "Введите производителя")
            return False
        
        try:
            datetime.strptime(self.exp_date_entry.get(), "%d.%m.%Y")
        except:
            messagebox.showwarning("Ошибка", "Введите дату в формате ДД.ММ.ГГГГ")
            return False
        
        return True
    
    def save(self):
        """Сохранение товара"""
        if not self.validate_input():
            return
        
        if self.product:
            # Редактирование
            self.product.name = self.name_entry.get().strip()
            self.product.category = self.category_combo.get()
            self.product.price = float(self.price_entry.get())
            self.product.quantity = int(self.quantity_entry.get())
            self.product.unit = self.unit_combo.get()
            self.product.manufacturer = self.manufacturer_entry.get().strip()
            self.product.expiration_date = self.exp_date_entry.get()
            self.result = self.product
        else:
            # Добавление
            self.result = Product(
                id=0,
                name=self.name_entry.get().strip(),
                category=self.category_combo.get(),
                price=float(self.price_entry.get()),
                quantity=int(self.quantity_entry.get()),
                unit=self.unit_combo.get(),
                manufacturer=self.manufacturer_entry.get().strip(),
                expiration_date=self.exp_date_entry.get()
            )
        
        self.destroy()
    
    def cancel(self):
        self.result = None
        self.destroy()


class VetApp:
    """Основное приложение"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🏥 Ветеринарная аптека - Управление запасами и продажами")
        self.root.geometry("1200x700")
        
        self.db = Database()
        self.current_sale_items: List[SaleItem] = []
        
        self.create_menu()
        self.create_widgets()
        self.refresh_products()
        self.update_status()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def create_widgets(self):
        # Создаем вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка Товары
        self.products_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text="📦 Товары")
        self.create_products_tab()
        
        # Вкладка Продажи
        self.sales_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sales_frame, text="🛒 Продажи")
        self.create_sales_tab()
        
        # Вкладка Отчеты
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="📊 Отчеты")
        self.create_reports_tab()
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        statusbar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.info_var = tk.StringVar(value="")
        infobar = ttk.Label(self.root, textvariable=self.info_var, relief=tk.SUNKEN, anchor=tk.E)
        infobar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_products_tab(self):
        # Панель инструментов
        toolbar = ttk.Frame(self.products_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="➕ Добавить", command=self.add_product).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Редактировать", command=self.edit_product).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Удалить", command=self.delete_product).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        
        ttk.Label(toolbar, text="Фильтр:").pack(side=tk.LEFT, padx=(10, 5))
        self.category_filter = ttk.Combobox(toolbar, values=["Все"] + self.db.CATEGORIES, 
                                           state="readonly", width=15)
        self.category_filter.set("Все")
        self.category_filter.pack(side=tk.LEFT, padx=2)
        self.category_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_products())
        
        self.low_stock_var = tk.BooleanVar()
        low_stock_chk = ttk.Checkbutton(toolbar, text="Мало на складе", 
                                       variable=self.low_stock_var,
                                       command=self.refresh_products)
        low_stock_chk.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(toolbar, text="🔄 Обновить", command=self.refresh_products).pack(side=tk.RIGHT)
        
        # Таблица товаров
        columns = ("id", "name", "category", "price", "quantity", "unit", "manufacturer", "expiration")
        self.products_tree = ttk.Treeview(self.products_frame, columns=columns, show="headings", height=20)
        
        self.products_tree.heading("id", text="ID")
        self.products_tree.heading("name", text="Название")
        self.products_tree.heading("category", text="Категория")
        self.products_tree.heading("price", text="Цена (₽)")
        self.products_tree.heading("quantity", text="Количество")
        self.products_tree.heading("unit", text="Ед.")
        self.products_tree.heading("manufacturer", text="Производитель")
        self.products_tree.heading("expiration", text="Срок годности")
        
        self.products_tree.column("id", width=50)
        self.products_tree.column("name", width=200)
        self.products_tree.column("category", width=100)
        self.products_tree.column("price", width=80)
        self.products_tree.column("quantity", width=70)
        self.products_tree.column("unit", width=50)
        self.products_tree.column("manufacturer", width=150)
        self.products_tree.column("expiration", width=100)
        
        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(self.products_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        
        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязка двойного клика
        self.products_tree.bind("<Double-1>", lambda e: self.edit_product())
    
    def create_sales_tab(self):
        # Верхняя панель
        top_frame = ttk.LabelFrame(self.sales_frame, text="Добавление товаров в продажу", padding="10")
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Выбор товара
        ttk.Label(top_frame, text="Товар:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.sale_product_combo = ttk.Combobox(top_frame, state="readonly", width=50)
        self.sale_product_combo.grid(row=0, column=1, padx=5, pady=5)
        self.update_sale_product_combo()
        
        # Количество
        ttk.Label(top_frame, text="Количество:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.sale_quantity_entry = ttk.Entry(top_frame, width=10)
        self.sale_quantity_entry.insert(0, "1")
        self.sale_quantity_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Кнопки
        ttk.Button(top_frame, text="➕ Добавить", command=self.add_to_sale).grid(row=0, column=4, padx=10)
        ttk.Button(top_frame, text="🗑️ Очистить", command=self.clear_sale).grid(row=0, column=5, padx=5)
        
        # Клиент
        ttk.Label(top_frame, text="Клиент:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.customer_entry = ttk.Entry(top_frame, width=50)
        self.customer_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(top_frame, text="💰 Оформить продажу", command=self.complete_sale).grid(row=1, column=4, rowspan=2, padx=10, sticky=tk.NS)
        
        # Таблица текущей продажи
        mid_frame = ttk.Frame(self.sales_frame)
        mid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("name", "price", "quantity", "subtotal")
        self.sale_items_tree = ttk.Treeview(mid_frame, columns=columns, show="headings", height=10)
        
        self.sale_items_tree.heading("name", text="Товар")
        self.sale_items_tree.heading("price", text="Цена (₽)")
        self.sale_items_tree.heading("quantity", text="Количество")
        self.sale_items_tree.heading("subtotal", text="Сумма (₽)")
        
        self.sale_items_tree.column("name", width=300)
        self.sale_items_tree.column("price", width=80)
        self.sale_items_tree.column("quantity", width=80)
        self.sale_items_tree.column("subtotal", width=100)
        
        scrollbar = ttk.Scrollbar(mid_frame, orient=tk.VERTICAL, command=self.sale_items_tree.yview)
        self.sale_items_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sale_items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Итого
        bottom_frame = ttk.Frame(self.sales_frame)
        bottom_frame.pack(fill=tk.X)
        
        self.total_label = ttk.Label(bottom_frame, text="Итого: 0.00 ₽", font=("Arial", 14, "bold"), foreground="green")
        self.total_label.pack(side=tk.RIGHT)
    
    def create_reports_tab(self):
        # Панель управления
        control_frame = ttk.Frame(self.reports_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="🔄 Обновить", command=self.refresh_reports).pack(side=tk.LEFT)
        
        # Вложенные вкладки отчетов
        reports_notebook = ttk.Notebook(self.reports_frame)
        reports_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Продажи
        sales_report_frame = ttk.Frame(reports_notebook)
        reports_notebook.add(sales_report_frame, text="Продажи")
        
        columns = ("id", "date", "customer", "items_count", "total")
        self.sales_report_tree = ttk.Treeview(sales_report_frame, columns=columns, show="headings", height=15)
        
        self.sales_report_tree.heading("id", text="№")
        self.sales_report_tree.heading("date", text="Дата")
        self.sales_report_tree.heading("customer", text="Клиент")
        self.sales_report_tree.heading("items_count", text="Товаров")
        self.sales_report_tree.heading("total", text="Сумма (₽)")
        
        self.sales_report_tree.column("id", width=50)
        self.sales_report_tree.column("date", width=140)
        self.sales_report_tree.column("customer", width=150)
        self.sales_report_tree.column("items_count", width=70)
        self.sales_report_tree.column("total", width=100)
        
        scrollbar = ttk.Scrollbar(sales_report_frame, orient=tk.VERTICAL, command=self.sales_report_tree.yview)
        self.sales_report_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sales_report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Мало на складе
        low_stock_frame = ttk.Frame(reports_notebook)
        reports_notebook.add(low_stock_frame, text="Мало на складе")
        
        columns = ("name", "category", "quantity", "unit")
        self.low_stock_tree = ttk.Treeview(low_stock_frame, columns=columns, show="headings", height=15)
        
        self.low_stock_tree.heading("name", text="Название")
        self.low_stock_tree.heading("category", text="Категория")
        self.low_stock_tree.heading("quantity", text="Остаток")
        self.low_stock_tree.heading("unit", text="Ед.")
        
        self.low_stock_tree.column("name", width=300)
        self.low_stock_tree.column("category", width=120)
        self.low_stock_tree.column("quantity", width=80)
        self.low_stock_tree.column("unit", width=60)
        
        scrollbar = ttk.Scrollbar(low_stock_frame, orient=tk.VERTICAL, command=self.low_stock_tree.yview)
        self.low_stock_tree.configure(yscrollcommand=scrollbar.set)
        
        self.low_stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Истекает срок
        expiring_frame = ttk.Frame(reports_notebook)
        reports_notebook.add(expiring_frame, text="Истекает срок")
        
        columns = ("name", "category", "expiration", "quantity")
        self.expiring_tree = ttk.Treeview(expiring_frame, columns=columns, show="headings", height=15)
        
        self.expiring_tree.heading("name", text="Название")
        self.expiring_tree.heading("category", text="Категория")
        self.expiring_tree.heading("expiration", text="Срок годности")
        self.expiring_tree.heading("quantity", text="Остаток")
        
        self.expiring_tree.column("name", width=300)
        self.expiring_tree.column("category", width=120)
        self.expiring_tree.column("expiration", width=120)
        self.expiring_tree.column("quantity", width=80)
        
        scrollbar = ttk.Scrollbar(expiring_frame, orient=tk.VERTICAL, command=self.expiring_tree.yview)
        self.expiring_tree.configure(yscrollcommand=scrollbar.set)
        
        self.expiring_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Методы для вкладки Товары
    def refresh_products(self):
        # Очистка таблицы
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Фильтрация
        products = self.db.products.copy()
        
        category = self.category_filter.get()
        if category != "Все":
            products = [p for p in products if p.category == category]
        
        if self.low_stock_var.get():
            products = [p for p in products if p.quantity <= 10]
        
        # Заполнение
        for p in products:
            self.products_tree.insert("", tk.END, values=(
                p.id, p.name, p.category, f"{p.price:.2f}", 
                p.quantity, p.unit, p.manufacturer, p.expiration_date
            ))
        
        self.update_info()
    
    def add_product(self):
        dialog = ProductDialog(self.root, self.db)
        self.root.wait_window(dialog)
        
        if dialog.result:
            if self.db.add_product(dialog.result):
                self.refresh_products()
                self.update_sale_product_combo()
                self.set_status(f"Добавлен товар: {dialog.result.name}")
                self.update_info()
    
    def edit_product(self):
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар для редактирования")
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item['values'][0]
        product = self.db.get_product_by_id(product_id)
        
        if product:
            dialog = ProductDialog(self.root, self.db, product)
            self.root.wait_window(dialog)
            
            if dialog.result:
                if self.db.update_product(dialog.result):
                    self.refresh_products()
                    self.update_sale_product_combo()
                    self.set_status(f"Обновлен товар: {dialog.result.name}")
    
    def delete_product(self):
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар для удаления")
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить товар \"{product_name}\"?"):
            if self.db.delete_product(product_id):
                self.refresh_products()
                self.update_sale_product_combo()
                self.set_status(f"Удален товар: {product_name}")
    
    # Методы для вкладки Продажи
    def update_sale_product_combo(self):
        available = [p for p in self.db.products if p.quantity > 0]
        self.sale_product_combo['values'] = [
            f"{p.name} ({p.price} ₽, доступно: {p.quantity} {p.unit})" 
            for p in available
        ]
        self.sale_product_combo.state_ids = {p.name: p.id for p in available}
    
    def add_to_sale(self):
        selected = self.sale_product_combo.get()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        
        try:
            quantity = int(self.sale_quantity_entry.get())
            if quantity <= 0:
                raise ValueError()
        except:
            messagebox.showwarning("Ошибка", "Введите корректное количество")
            return
        
        # Получаем ID товара
        product_name = selected.split(" (")[0]
        product_id = self.sale_product_combo.state_ids.get(product_name)
        product = self.db.get_product_by_id(product_id)
        
        if product.quantity < quantity:
            messagebox.showerror("Ошибка", f"Недостаточно товара. Доступно: {product.quantity}")
            return
        
        # Проверяем, есть ли уже в продаже
        for item in self.current_sale_items:
            if item.product_id == product_id:
                item.quantity += quantity
                self.update_sale_items_display()
                self.set_status(f"Добавлено: {product.name} x{quantity}")
                return
        
        # Добавляем новый элемент
        self.current_sale_items.append(SaleItem(
            product_id=product_id,
            product_name=product.name,
            quantity=quantity,
            price=product.price
        ))
        
        self.update_sale_items_display()
        self.sale_quantity_entry.delete(0, tk.END)
        self.sale_quantity_entry.insert(0, "1")
        self.set_status(f"Добавлено: {product.name} x{quantity}")
    
    def update_sale_items_display(self):
        # Очистка
        for item in self.sale_items_tree.get_children():
            self.sale_items_tree.delete(item)
        
        # Заполнение
        total = 0
        for item in self.current_sale_items:
            subtotal = item.subtotal
            total += subtotal
            self.sale_items_tree.insert("", tk.END, values=(
                item.product_name, f"{item.price:.2f}", 
                item.quantity, f"{subtotal:.2f}"
            ))
        
        self.total_label.config(text=f"Итого: {total:.2f} ₽")
    
    def clear_sale(self):
        self.current_sale_items.clear()
        self.update_sale_items_display()
        self.customer_entry.delete(0, tk.END)
        self.set_status("Корзина очищена")
    
    def complete_sale(self):
        if not self.current_sale_items:
            messagebox.showwarning("Внимание", "Добавьте товары в продажу")
            return
        
        customer = self.customer_entry.get().strip()
        sale = self.db.create_sale(self.current_sale_items, customer)
        
        if sale:
            messagebox.showinfo("Успешно", f"Продажа оформлена!\nСумма: {sale.total_amount:.2f} ₽")
            self.current_sale_items.clear()
            self.update_sale_items_display()
            self.update_sale_product_combo()
            self.refresh_products()
            self.refresh_reports()
            self.customer_entry.delete(0, tk.END)
            self.set_status(f"Продажа №{sale.id} на сумму {sale.total_amount:.2f} ₽")
            self.update_info()
        else:
            messagebox.showerror("Ошибка", "Не удалось оформить продажу")
    
    # Методы для вкладки Отчеты
    def refresh_reports(self):
        # Продажи
        for item in self.sales_report_tree.get_children():
            self.sales_report_tree.delete(item)
        
        for sale in sorted(self.db.sales, key=lambda s: s.id, reverse=True):
            self.sales_report_tree.insert("", tk.END, values=(
                sale.id, sale.date, sale.customer_name,
                len(sale.items), f"{sale.total_amount:.2f}"
            ))
        
        # Мало на складе
        for item in self.low_stock_tree.get_children():
            self.low_stock_tree.delete(item)
        
        for p in self.db.get_low_stock_products():
            self.low_stock_tree.insert("", tk.END, values=(
                p.name, p.category, p.quantity, p.unit
            ))
        
        # Истекает срок
        for item in self.expiring_tree.get_children():
            self.expiring_tree.delete(item)
        
        for p in self.db.get_expiring_products():
            self.expiring_tree.insert("", tk.END, values=(
                p.name, p.category, p.expiration_date, p.quantity
            ))
        
        self.set_status("Отчеты обновлены")
    
    # Вспомогательные методы
    def set_status(self, message):
        self.status_var.set(message)
    
    def update_status(self):
        self.update_info()
    
    def update_info(self):
        products_count = len(self.db.products)
        today_sales = len([s for s in self.db.sales 
                          if s.date.startswith(datetime.now().strftime("%d.%m.%Y"))])
        self.info_var.set(f"Товаров: {products_count} | Продаж сегодня: {today_sales}")
    
    def show_about(self):
        messagebox.showinfo("О программе", 
                           "Ветеринарная аптека v1.0\n\n"
                           "Система управления запасами и продажами\n"
                           "ветеринарных товаров.\n\n"
                           "© 2024")


def main():
    root = tk.Tk()
    
    # Настройка стиля
    style = ttk.Style()
    style.theme_use('clam')
    
    app = VetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
