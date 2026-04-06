#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ВетАптека ULTIMATE v2.0
Система управления ветеринарной аптекой
- База данных SQLite
- Регистрация/Авторизация
- Управление товарами, продажами, закупками
- Расширенная номенклатура (30+ товаров)
- Современный дизайн
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

# ============================================================================
# КОНФИГУРАЦИЯ И СТИЛИ
# ============================================================================

class Config:
    """Конфигурация приложения"""
    APP_NAME = "ВетАптека ULTIMATE"
    VERSION = "2.0"
    DB_NAME = "vet_pharmacy_ultimate.db"
    
    # Цветовая палитра (современная)
    COLORS = {
        'primary': '#4F46E5',      # Индиго
        'primary_dark': '#4338CA',
        'secondary': '#10B981',    # Изумруд
        'accent': '#F59E0B',       # Янтарь
        'danger': '#EF4444',       # Красный
        'warning': '#F97316',      # Оранжевый
        'success': '#22C55E',      # Зеленый
        'info': '#3B82F6',         # Синий
        
        'bg_main': '#F9FAFB',      # Светлый фон
        'bg_card': '#FFFFFF',      # Фон карточек
        'bg_sidebar': '#1E293B',   # Темный сайдбар
        'text_main': '#1F2937',    # Основной текст
        'text_muted': '#6B7280',   # Приглушенный текст
        'border': '#E5E7EB',       # Границы
        'hover': '#F3F4F6',        # Фон при наведении
    }
    
    # Шрифты
    FONTS = {
        'title': ('Segoe UI', 18, 'bold'),
        'heading': ('Segoe UI', 14, 'bold'),
        'normal': ('Segoe UI', 11),
        'small': ('Segoe UI', 9),
        'button': ('Segoe UI', 11, 'bold'),
    }


# ============================================================================
# БАЗА ДАННЫХ
# ============================================================================

class Database:
    """Управление базой данных"""
    
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.init_database()
        self.seed_data()
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_database(self):
        """Инициализация таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT CHECK(role IN ('admin', 'seller')) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Таблица категорий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')
        
        # Таблица поставщиков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                brand TEXT,
                price REAL NOT NULL,
                cost REAL NOT NULL,
                quantity INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 5,
                unit TEXT DEFAULT 'шт',
                expiry_date DATE,
                description TEXT,
                barcode TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        
        # Таблица заказов поставщикам
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_date DATE,
                status TEXT CHECK(status IN ('draft', 'sent', 'in_transit', 'delivered', 'cancelled')) DEFAULT 'draft',
                total_cost REAL DEFAULT 0,
                notes TEXT,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Таблица позиций заказа
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                cost_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # Таблица продаж
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                discount REAL DEFAULT 0,
                final_amount REAL NOT NULL,
                payment_method TEXT CHECK(payment_method IN ('cash', 'card', 'mixed')) DEFAULT 'cash',
                seller_id INTEGER NOT NULL,
                customer_name TEXT,
                notes TEXT,
                FOREIGN KEY (seller_id) REFERENCES users(id)
            )
        ''')
        
        # Таблица позиций продажи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def seed_data(self):
        """Заполнение начальными данными"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверка наличия пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Создание пользователей по умолчанию
            users = [
                ('admin', self._hash_password('admin123'), 'Администратор Системы', 'admin'),
                ('seller', self._hash_password('seller123'), 'Продавец Иванов', 'seller'),
                ('manager', self._hash_password('manager123'), 'Менеджер Петров', 'admin'),
            ]
            cursor.executemany(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                users
            )
        
        # Проверка наличия категорий
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            categories = [
                ('Корма', 'Сухие и влажные корма для животных'),
                ('Лекарства', 'Ветеринарные препараты и медикаменты'),
                ('Аксессуары', 'Ошейники, поводки, переноски'),
                ('Гигиена', 'Шампуни, средства ухода'),
                ('Витамины', 'Витаминные добавки и БАДы'),
                ('Игрушки', 'Игрушки для собак и кошек'),
                ('Наполнители', 'Наполнители для лотков'),
                ('Лакомства', 'Вкусняшки для питомцев'),
            ]
            cursor.executemany(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                categories
            )
        
        # Проверка наличия поставщиков
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        if cursor.fetchone()[0] == 0:
            suppliers = [
                ('ООО "ВетТорг"', 'Петров Сергей', '+7 (495) 123-45-67', 'info@vettorg.ru', 'Москва, ул. Складская, 15', 'Крупный оптовик'),
                ('ИП "ЗооСнаб"', 'Сидорова Анна', '+7 (812) 987-65-43', 'anna@zoosnab.ru', 'Санкт-Петербург, пр. Невский, 100', 'Быстрая доставка'),
                ('ЗАО "АгроВет"', 'Козлов Дмитрий', '+7 (495) 555-00-11', 'sales@agrovet.ru', 'Москва, ш. Волоколамское, 50', 'Официальный дистрибьютор Royal Canin'),
                ('ООО "ПетФуд"', 'Николаева Елена', '+7 (903) 777-88-99', 'elena@petfood.ru', 'Казань, ул. Промышленная, 20', 'Специализация на кормах'),
                ('ВетСервис Плюс', 'Морозов Игорь', '+7 (999) 111-22-33', 'igor@vetservice.ru', 'Екатеринбург, ул. Ленина, 75', 'Лекарства и оборудование'),
            ]
            cursor.executemany(
                "INSERT INTO suppliers (name, contact_person, phone, email, address, notes) VALUES (?, ?, ?, ?, ?, ?)",
                suppliers
            )
        
        # Проверка наличия товаров
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            # Получаем ID категорий
            cursor.execute("SELECT id, name FROM categories")
            cat_ids = {name: id for id, name in cursor.fetchall()}
            
            products = [
                # Корма
                ('Royal Canin Adult Dog 15kg', cat_ids['Корма'], 'Royal Canin', 4500, 3200, 20, 5, 'кг', '2025-12-01', 'Корм для взрослых собак средних пород', '5601234567890'),
                ('Acana Heritage Dog 11.4kg', cat_ids['Корма'], 'Acana', 5200, 3800, 15, 5, 'кг', '2025-11-15', 'Беззерновой корм премиум класса', '5601234567891'),
                ('Hills Science Plan Cat 10kg', cat_ids['Корма'], 'Hills', 3800, 2700, 25, 8, 'кг', '2025-10-20', 'Лечебный корм для кошек', '5601234567892'),
                ('Pro Plan Adult Cat 10kg', cat_ids['Корма'], 'Pro Plan', 3200, 2300, 30, 10, 'кг', '2025-09-30', 'Полнорационный корм для кошек', '5601234567893'),
                ('Grandorf Adult Rabbit 10kg', cat_ids['Корма'], 'Grandorf', 4100, 2900, 12, 5, 'кг', '2025-08-15', 'Гипоаллергенный корм с кроликом', '5601234567894'),
                ('Monge Puppy Lamb 12kg', cat_ids['Корма'], 'Monge', 3900, 2800, 18, 6, 'кг', '2025-07-20', 'Корм для щенков с ягненком', '5601234567895'),
                
                # Лекарства
                ('Гамавит 100мл', cat_ids['Лекарства'], 'Ветбиохим', 450, 280, 50, 15, 'фл', '2025-06-01', 'Иммуномодулятор', '5601234567896'),
                ('Фиприст Спот-он для кошек', cat_ids['Лекарства'], 'Merial', 890, 550, 40, 10, 'уп', '2025-05-15', 'От блох и клещей', '5601234567897'),
                ('Альбендазол таблетки', cat_ids['Лекарства'], 'Астравет', 120, 65, 100, 30, 'уп', '2026-01-01', 'Противоглистное', '5601234567898'),
                ('Хлоргексидин вет. 100мл', cat_ids['Лекарства'], 'Веда', 85, 45, 80, 20, 'фл', '2025-12-31', 'Антисептик', '5601234567899'),
                ('Травматин инъекции 100мл', cat_ids['Лекарства'], 'Гомеопатия', 620, 380, 25, 8, 'фл', '2025-04-20', 'Противовоспалительное', '5601234567900'),
                
                # Аксессуары
                ('Ошейник Triol средний', cat_ids['Аксессуары'], 'Triol', 350, 180, 60, 15, 'шт', None, 'Регулируемый ошейник', '5601234567901'),
                ('Поводок-рулетка 5м', cat_ids['Аксессуары'], 'Ferplast', 1200, 750, 30, 10, 'шт', None, 'Для собак до 25кг', '5601234567902'),
                ('Переноска средняя', cat_ids['Аксессуары'], 'Trixie', 2500, 1600, 15, 5, 'шт', None, 'Для кошек и мелких собак', '5601234567903'),
                ('Миска керамическая', cat_ids['Аксессуары'], 'ZooMark', 280, 150, 50, 20, 'шт', None, 'Объем 500мл', '5601234567904'),
                ('Лежанка мягкая 60см', cat_ids['Аксессуары'], 'PetComfort', 1800, 1100, 20, 8, 'шт', None, 'Съемный чехол', '5601234567905'),
                
                # Гигиена
                ('Шампунь для собак гипоаллергенный', cat_ids['Гигиена'], 'Beaphar', 520, 320, 35, 10, 'фл', '2026-03-01', '250мл', '5601234567906'),
                ('Кондиционер для шерсти', cat_ids['Гигиена'], 'Espree', 680, 420, 25, 8, 'фл', '2026-02-15', '355мл', '5601234567907'),
                ('Лосьон для ушей', cat_ids['Гигиена'], 'Otifree', 450, 280, 40, 12, 'фл', '2025-11-30', '60мл', '5601234567908'),
                ('Зубная паста для животных', cat_ids['Гигиена'], 'Tropiclean', 380, 230, 45, 15, 'туб', '2026-04-20', '70мл', '5601234567909'),
                ('Когтерез для кошек', cat_ids['Гигиена'], 'Trixie', 290, 160, 55, 20, 'шт', None, 'Нержавеющая сталь', '5601234567910'),
                
                # Витамины
                ('Витаминный комплекс для щенков', cat_ids['Витамины'], 'Canina', 890, 550, 30, 10, 'уп', '2025-09-01', '120 таблеток', '5601234567911'),
                ('Биоритм для пожилых собак', cat_ids['Витамины'], 'Веда', 650, 400, 25, 8, 'уп', '2025-08-15', '60 таблеток', '5601234567912'),
                ('Пивные дрожжи с чесноком', cat_ids['Витамины'], 'Агроветзащита', 180, 95, 70, 25, 'уп', '2026-01-20', '100 таблеток', '5601234567913'),
                
                # Игрушки
                ('Мяч резиновый большой', cat_ids['Игрушки'], 'Kong', 850, 520, 40, 15, 'шт', None, 'Прочный мяч для крупных собак', '5601234567914'),
                ('Канат игровой 3 узла', cat_ids['Игрушки'], 'Trixie', 320, 180, 60, 20, 'шт', None, 'Для перетягивания', '5601234567915'),
                ('Мышь интерактивная', cat_ids['Игрушки'], 'Petstages', 450, 280, 35, 12, 'шт', None, 'С кошачьей мятой', '5601234567916'),
                ('Пуллер кольцо среднее', cat_ids['Игрушки'], 'Puller', 680, 420, 25, 10, 'шт', None, 'Для активных тренировок', '5601234567917'),
                
                # Наполнители
                ('Наполнитель древесный 10л', cat_ids['Наполнители'], 'Чистые Лапки', 280, 160, 80, 30, 'уп', None, 'Комкующийся', '5601234567918'),
                ('Наполнитель силикагель 5л', cat_ids['Наполнители'], 'SiCat', 520, 320, 50, 20, 'уп', None, 'Поглощает запахи', '5601234567919'),
                ('Наполнитель минеральный 8кг', cat_ids['Наполнители'], 'Барсик', 190, 110, 100, 40, 'уп', None, 'Эконом вариант', '5601234567920'),
                
                # Лакомства
                ('Палочки говяжьи сушеные', cat_ids['Лакомства'], 'DentaStix', 320, 190, 70, 25, 'уп', '2026-05-01', '270г', '5601234567921'),
                ('Подушечки с начинкой', cat_ids['Лакомства'], 'Petkult', 180, 100, 90, 30, 'уп', '2026-04-15', '150г', '5601234567922'),
                ('Косточки из жил', cat_ids['Лакомства'], 'Happy Dog', 250, 145, 65, 20, 'уп', '2026-06-20', '200г', '5601234567923'),
            ]
            
            cursor.executemany('''
                INSERT INTO products 
                (name, category_id, brand, price, cost, quantity, min_quantity, unit, expiry_date, description, barcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', products)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Аутентификация пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self._hash_password(password)
        cursor.execute('''
            SELECT id, username, full_name, role 
            FROM users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'role': row[3]
            }
        return None
    
    def register_user(self, username: str, password: str, full_name: str, role: str) -> Tuple[bool, str]:
        """Регистрация нового пользователя"""
        if not username or not password or not full_name:
            return False, "Все поля обязательны для заполнения"
        
        if len(username) < 3:
            return False, "Имя пользователя должно быть не менее 3 символов"
        
        if len(password) < 6:
            return False, "Пароль должен быть не менее 6 символов"
        
        if role not in ['admin', 'seller']:
            return False, "Неверная роль"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self._hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, full_name, role))
            conn.commit()
            return True, "Пользователь успешно зарегистрирован"
        except sqlite3.IntegrityError:
            return False, "Пользователь с таким именем уже существует"
        finally:
            conn.close()
    
    # Методы для работы с товарами
    def get_categories(self) -> List[Tuple]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description FROM categories ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def get_products(self, category_id: Optional[int] = None, search: str = '') -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT p.id, p.name, c.name as category, p.brand, p.price, p.cost, 
                   p.quantity, p.min_quantity, p.unit, p.expiry_date, p.description, p.barcode
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        '''
        params = []
        
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        
        if search:
            query += " AND (p.name LIKE ? OR p.brand LIKE ? OR p.barcode LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY p.name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'id': row[0], 'name': row[1], 'category': row[2], 'brand': row[3],
                'price': row[4], 'cost': row[5], 'quantity': row[6], 'min_quantity': row[7],
                'unit': row[8], 'expiry_date': row[9], 'description': row[10], 'barcode': row[11]
            })
        return products
    
    def add_product(self, name: str, category_id: int, brand: str, price: float, 
                    cost: float, quantity: int, min_quantity: int, unit: str,
                    expiry_date: Optional[str], description: str, barcode: str) -> Tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO products 
                (name, category_id, brand, price, cost, quantity, min_quantity, unit, expiry_date, description, barcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, category_id, brand, price, cost, quantity, min_quantity, unit, expiry_date, description, barcode))
            conn.commit()
            return True, "Товар добавлен"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def update_product(self, product_id: int, **kwargs) -> Tuple[bool, str]:
        if not kwargs:
            return False, "Нет данных для обновления"
        
        fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [product_id]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"UPDATE products SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
            conn.commit()
            return True, "Товар обновлен"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def delete_product(self, product_id: int) -> Tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            return True, "Товар удален"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    # Методы для поставщиков
    def get_suppliers(self, active_only: bool = True) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, name, contact_person, phone, email, address, notes FROM suppliers"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        suppliers = []
        for row in rows:
            suppliers.append({
                'id': row[0], 'name': row[1], 'contact_person': row[2],
                'phone': row[3], 'email': row[4], 'address': row[5], 'notes': row[6]
            })
        return suppliers
    
    def add_supplier(self, name: str, contact_person: str, phone: str, 
                     email: str, address: str, notes: str) -> Tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO suppliers (name, contact_person, phone, email, address, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, contact_person, phone, email, address, notes))
            conn.commit()
            return True, "Поставщик добавлен"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    # Методы для заказов
    def create_purchase_order(self, supplier_id: int, expected_date: str, 
                              notes: str, user_id: int) -> Tuple[bool, int, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO purchase_orders (supplier_id, expected_date, notes, created_by)
                VALUES (?, ?, ?, ?)
            ''', (supplier_id, expected_date, notes, user_id))
            order_id = cursor.lastrowid
            conn.commit()
            return True, order_id, "Заказ создан"
        except Exception as e:
            return False, 0, str(e)
        finally:
            conn.close()
    
    def add_order_item(self, order_id: int, product_id: int, quantity: int, cost_price: float) -> Tuple[bool, str]:
        subtotal = quantity * cost_price
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO purchase_order_items (order_id, product_id, quantity, cost_price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, product_id, quantity, cost_price, subtotal))
            
            # Обновляем общую сумму заказа
            cursor.execute('''
                UPDATE purchase_orders 
                SET total_cost = (SELECT SUM(subtotal) FROM purchase_order_items WHERE order_id = ?)
                WHERE id = ?
            ''', (order_id, order_id))
            
            conn.commit()
            return True, "Товар добавлен в заказ"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def get_purchase_orders(self, status_filter: Optional[str] = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT po.id, s.name as supplier, po.order_date, po.expected_date, 
                   po.status, po.total_cost, po.notes, u.full_name as created_by
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            JOIN users u ON po.created_by = u.id
        '''
        params = []
        
        if status_filter:
            query += " WHERE po.status = ?"
            params.append(status_filter)
        
        query += " ORDER BY po.order_date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row[0], 'supplier': row[1], 'order_date': row[2],
                'expected_date': row[3], 'status': row[4], 'total_cost': row[5],
                'notes': row[6], 'created_by': row[7]
            })
        return orders
    
    def get_order_items(self, order_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT poi.id, p.name, poi.quantity, poi.cost_price, poi.subtotal
            FROM purchase_order_items poi
            JOIN products p ON poi.product_id = p.id
            WHERE poi.order_id = ?
        ''', (order_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        for row in rows:
            items.append({
                'id': row[0], 'product_name': row[1], 'quantity': row[2],
                'cost_price': row[3], 'subtotal': row[4]
            })
        return items
    
    def update_order_status(self, order_id: int, status: str) -> Tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE purchase_orders SET status = ? WHERE id = ?
            ''', (status, order_id))
            conn.commit()
            
            # Если статус "delivered", пополняем склад
            if status == 'delivered':
                cursor.execute('''
                    SELECT product_id, quantity FROM purchase_order_items WHERE order_id = ?
                ''', (order_id,))
                items = cursor.fetchall()
                
                for product_id, quantity in items:
                    cursor.execute('''
                        UPDATE products SET quantity = quantity + ? WHERE id = ?
                    ''', (quantity, product_id))
            
            conn.commit()
            return True, f"Статус изменен на '{status}'"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    # Методы для продаж
    def create_sale(self, items: List[Dict], discount: float, payment_method: str,
                    seller_id: int, customer_name: str, notes: str) -> Tuple[bool, int, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Рассчитываем суммы
            total_amount = sum(item['subtotal'] for item in items)
            final_amount = total_amount - discount
            
            # Создаем продажу
            cursor.execute('''
                INSERT INTO sales (total_amount, discount, final_amount, payment_method, seller_id, customer_name, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (total_amount, discount, final_amount, payment_method, seller_id, customer_name, notes))
            
            sale_id = cursor.lastrowid
            
            # Добавляем позиции и списываем товар
            for item in items:
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['product_id'], item['quantity'], item['price'], item['subtotal']))
                
                # Списываем со склада
                cursor.execute('''
                    UPDATE products SET quantity = quantity - ? WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            conn.commit()
            return True, sale_id, "Продажа оформлена"
        except Exception as e:
            conn.rollback()
            return False, 0, str(e)
        finally:
            conn.close()
    
    def get_sales_history(self, days: int = 30) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.id, s.sale_date, s.final_amount, s.payment_method, 
                   u.full_name as seller, s.customer_name
            FROM sales s
            JOIN users u ON s.seller_id = u.id
            WHERE s.sale_date >= date('now', ?)
            ORDER BY s.sale_date DESC
        ''', (f'-{days} days',))
        
        rows = cursor.fetchall()
        conn.close()
        
        sales = []
        for row in rows:
            sales.append({
                'id': row[0], 'date': row[1], 'amount': row[2],
                'payment_method': row[3], 'seller': row[4], 'customer': row[5]
            })
        return sales
    
    def get_low_stock_products(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, c.name as category, p.quantity, p.min_quantity, p.unit
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.quantity <= p.min_quantity
            ORDER BY p.quantity ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'id': row[0], 'name': row[1], 'category': row[2],
                'quantity': row[3], 'min_quantity': row[4], 'unit': row[5]
            })
        return products
    
    def get_expiring_products(self, days: int = 30) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, category_id, expiry_date, quantity, unit
            FROM products
            WHERE expiry_date IS NOT NULL 
              AND expiry_date <= date('now', ?)
              AND expiry_date >= date('now')
            ORDER BY expiry_date ASC
        ''', (f'+{days} days',))
        
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'id': row[0], 'name': row[1], 'expiry_date': row[3],
                'quantity': row[4], 'unit': row[5]
            })
        return products


# ============================================================================
# GUI КОМПОНЕНТЫ
# ============================================================================

class StyledButton(tk.Button):
    """Стилизованная кнопка"""
    def __init__(self, parent, text, command=None, variant='primary', **kwargs):
        colors = Config.COLORS
        fonts = Config.FONTS
        
        bg = colors.get(variant, colors['primary'])
        fg = '#FFFFFF'
        
        super().__init__(parent, text=text, command=command, 
                        bg=bg, fg=fg, font=fonts['button'],
                        relief='flat', padx=15, pady=8, **kwargs)
        
        self.bind('<Enter>', lambda e: self.config(bg=colors.get(f'{variant}_dark', colors['primary_dark'])))
        self.bind('<Leave>', lambda e: self.config(bg=bg))


class StyledEntry(tk.Entry):
    """Стилизованное поле ввода"""
    def __init__(self, parent, **kwargs):
        colors = Config.COLORS
        fonts = Config.FONTS
        
        super().__init__(parent, font=fonts['normal'], 
                        bg='#FFFFFF', fg=colors['text_main'],
                        relief='solid', borderwidth=1, **kwargs)
        
        self.config(highlightbackground=colors['border'], 
                   highlightcolor=colors['primary'],
                   highlightthickness=1)


class CardFrame(tk.Frame):
    """Карточка с тенью"""
    def __init__(self, parent, **kwargs):
        colors = Config.COLORS
        super().__init__(parent, bg=colors['bg_card'], **kwargs)


# ============================================================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================

class VetPharmacyApp:
    """Основное приложение"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{Config.APP_NAME} v{Config.VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        self.db = Database(Config.DB_NAME)
        self.current_user = None
        
        self.colors = Config.COLORS
        self.fonts = Config.FONTS
        
        self.setup_styles()
        self.show_login_screen()
    
    def setup_styles(self):
        """Настройка стилей для ttk виджетов"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка Treeview
        style.configure("Treeview", 
                       background='#FFFFFF',
                       foreground=self.colors['text_main'],
                       fieldbackground='#FFFFFF',
                       rowheight=30,
                       font=self.fonts['normal'])
        style.configure("Treeview.Heading", 
                       font=self.fonts['heading'],
                       background=self.colors['bg_sidebar'],
                       foreground='#FFFFFF')
        style.map("Treeview", 
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', '#FFFFFF')])
        
        # Настройка Notebook
        style.configure("TNotebook", background=self.colors['bg_main'])
        style.configure("TNotebook.Tab", 
                       padding=[15, 8],
                       font=self.fonts['normal'])
        style.configure("TFrame", background=self.colors['bg_main'])
        style.configure("TLabel", background=self.colors['bg_main'], 
                       foreground=self.colors['text_main'])
    
    def clear_screen(self):
        """Очистка экрана"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Экран авторизации"""
        self.clear_screen()
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg=self.colors['bg_main'])
        main_frame.pack(fill='both', expand=True)
        
        # Левая панель (декоративная)
        left_panel = tk.Frame(main_frame, bg=self.colors['primary'], width=400)
        left_panel.pack(side='left', fill='both')
        
        # Логотип и название
        logo_frame = tk.Frame(left_panel, bg=self.colors['primary'])
        logo_frame.place(relx=0.5, rely=0.4, anchor='center')
        
        tk.Label(logo_frame, text="🐾", font=('Segoe UI', 80), 
                bg=self.colors['primary'], fg='#FFFFFF').pack()
        tk.Label(logo_frame, text="ВетАптека", font=('Segoe UI', 28, 'bold'), 
                bg=self.colors['primary'], fg='#FFFFFF').pack(pady=10)
        tk.Label(logo_frame, text="ULTRA", font=('Segoe UI', 18), 
                bg=self.colors['primary'], fg='#E0E7FF').pack()
        
        # Правая панель (форма входа)
        right_panel = tk.Frame(main_frame, bg=self.colors['bg_main'])
        right_panel.pack(side='right', fill='both', expand=True)
        
        form_frame = tk.Frame(right_panel, bg=self.colors['bg_main'])
        form_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Заголовок
        tk.Label(form_frame, text="Вход в систему", 
                font=self.fonts['title'], bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(pady=(0, 30))
        
        # Поля ввода
        input_frame = tk.Frame(form_frame, bg=self.colors['bg_main'], width=350)
        input_frame.pack()
        
        tk.Label(input_frame, text="Имя пользователя", 
                font=self.fonts['normal'], bg=self.colors['bg_main'],
                fg=self.colors['text_muted']).pack(anchor='w', pady=(0, 5))
        
        self.login_username = StyledEntry(input_frame, width=40)
        self.login_username.pack(fill='x', pady=(0, 20))
        
        tk.Label(input_frame, text="Пароль", 
                font=self.fonts['normal'], bg=self.colors['bg_main'],
                fg=self.colors['text_muted']).pack(anchor='w', pady=(0, 5))
        
        self.login_password = StyledEntry(input_frame, width=40, show='•')
        self.login_password.pack(fill='x', pady=(0, 30))
        
        # Кнопка входа
        login_btn = StyledButton(form_frame, text="Войти", 
                                command=self.handle_login, width=30)
        login_btn.pack(pady=10)
        
        # Кнопка регистрации
        register_btn = tk.Button(form_frame, text="Нет аккаунта? Зарегистрироваться",
                                command=self.show_register_screen,
                                font=self.fonts['normal'],
                                bg=self.colors['bg_main'],
                                fg=self.colors['primary'],
                                relief='flat', cursor='hand2')
        register_btn.pack(pady=10)
        
        # Тестовые учетки
        test_frame = tk.Frame(form_frame, bg=self.colors['bg_main'])
        test_frame.pack(pady=20)
        
        tk.Label(test_frame, text="Тестовые учетки:", 
                font=self.fonts['small'], bg=self.colors['bg_main'],
                fg=self.colors['text_muted']).pack()
        tk.Label(test_frame, text="admin / admin123  |  seller / seller123", 
                font=self.fonts['small'], bg=self.colors['bg_main'],
                fg=self.colors['text_muted']).pack()
        
        # Привязка Enter
        self.login_password.bind('<Return>', lambda e: self.handle_login())
    
    def show_register_screen(self):
        """Экран регистрации"""
        self.clear_screen()
        
        main_frame = tk.Frame(self.root, bg=self.colors['bg_main'])
        main_frame.pack(fill='both', expand=True)
        
        # Форма регистрации по центру
        form_frame = tk.Frame(main_frame, bg=self.colors['bg_card'], 
                             padx=50, pady=40)
        form_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Заголовок
        tk.Label(form_frame, text="Регистрация нового пользователя", 
                font=self.fonts['title'], bg=self.colors['bg_card'],
                fg=self.colors['text_main']).pack(pady=(0, 30))
        
        # Поля ввода
        fields_frame = tk.Frame(form_frame, bg=self.colors['bg_card'], width=400)
        fields_frame.pack()
        
        labels = ["Имя пользователя", "ФИО", "Пароль", "Подтверждение пароля"]
        self.reg_entries = {}
        
        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, 
                    font=self.fonts['normal'], bg=self.colors['bg_card'],
                    fg=self.colors['text_muted']).pack(anchor='w', pady=(0, 5))
            
            entry = StyledEntry(fields_frame, width=45)
            entry.pack(fill='x', pady=(0, 20))
            self.reg_entries[label] = entry
        
        # Выбор роли
        tk.Label(fields_frame, text="Роль", 
                font=self.fonts['normal'], bg=self.colors['bg_card'],
                fg=self.colors['text_muted']).pack(anchor='w', pady=(0, 5))
        
        self.reg_role = tk.StringVar(value='seller')
        role_frame = tk.Frame(fields_frame, bg=self.colors['bg_card'])
        role_frame.pack(fill='x', pady=(0, 30))
        
        tk.Radiobutton(role_frame, text="Продавец", variable=self.reg_role, 
                      value='seller', bg=self.colors['bg_card'],
                      font=self.fonts['normal']).pack(side='left', padx=10)
        tk.Radiobutton(role_frame, text="Администратор", variable=self.reg_role, 
                      value='admin', bg=self.colors['bg_card'],
                      font=self.fonts['normal']).pack(side='left', padx=10)
        
        # Кнопки
        btn_frame = tk.Frame(form_frame, bg=self.colors['bg_card'])
        btn_frame.pack(fill='x')
        
        StyledButton(btn_frame, text="Зарегистрироваться", 
                    command=self.handle_register).pack(side='left', padx=5)
        StyledButton(btn_frame, text="Назад ко входу", 
                    command=self.show_login_screen, variant='secondary').pack(side='left', padx=5)
    
    def handle_login(self):
        """Обработка входа"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите имя пользователя и пароль")
            return
        
        user = self.db.authenticate(username, password)
        if user:
            self.current_user = user
            self.show_main_app()
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")
    
    def handle_register(self):
        """Обработка регистрации"""
        username = self.reg_entries["Имя пользователя"].get().strip()
        full_name = self.reg_entries["ФИО"].get().strip()
        password = self.reg_entries["Пароль"].get()
        confirm = self.reg_entries["Подтверждение пароля"].get()
        role = self.reg_role.get()
        
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        
        success, message = self.db.register_user(username, password, full_name, role)
        
        if success:
            messagebox.showinfo("Успех", message)
            self.show_login_screen()
        else:
            messagebox.showerror("Ошибка", message)
    
    def show_main_app(self):
        """Основное приложение"""
        self.clear_screen()
        
        # Верхняя панель
        top_bar = tk.Frame(self.root, bg=self.colors['bg_card'], height=70)
        top_bar.pack(fill='x')
        top_bar.pack_propagate(False)
        
        # Логотип
        logo_frame = tk.Frame(top_bar, bg=self.colors['bg_card'])
        logo_frame.pack(side='left', padx=20)
        
        tk.Label(logo_frame, text="🐾 ВетАптека", 
                font=('Segoe UI', 20, 'bold'), 
                bg=self.colors['bg_card'], 
                fg=self.colors['primary']).pack()
        
        # Информация о пользователе
        user_frame = tk.Frame(top_bar, bg=self.colors['bg_card'])
        user_frame.pack(side='right', padx=20)
        
        tk.Label(user_frame, text=f"👤 {self.current_user['full_name']}", 
                font=self.fonts['normal'], 
                bg=self.colors['bg_card'], 
                fg=self.colors['text_main']).pack(side='top', anchor='e')
        
        tk.Label(user_frame, text=f"Роль: {'Администратор' if self.current_user['role'] == 'admin' else 'Продавец'}", 
                font=self.fonts['small'], 
                bg=self.colors['bg_card'], 
                fg=self.colors['text_muted']).pack(side='top', anchor='e')
        
        StyledButton(user_frame, text="Выход", 
                    command=self.logout, variant='danger').pack(side='left', padx=10)
        
        # Разделительная линия
        sep = tk.Frame(self.root, bg=self.colors['border'], height=1)
        sep.pack(fill='x')
        
        # Основная область
        main_area = tk.Frame(self.root, bg=self.colors['bg_main'])
        main_area.pack(fill='both', expand=True)
        
        # Боковое меню
        sidebar = tk.Frame(main_area, bg=self.colors['bg_sidebar'], width=220)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Пункты меню
        menu_items = [
            ("📊 Главная", "dashboard"),
            ("🛒 Продажи", "sales"),
            ("📦 Товары", "products"),
            ("📈 Отчеты", "reports"),
        ]
        
        if self.current_user['role'] == 'admin':
            menu_items.append(("🚚 Закупки", "purchases"))
            menu_items.append(("👥 Поставщики", "suppliers"))
            menu_items.append(("👤 Пользователи", "users"))
        
        self.menu_buttons = {}
        for i, (text, key) in enumerate(menu_items):
            btn = tk.Button(sidebar, text=text, 
                           font=self.fonts['normal'],
                           bg=self.colors['bg_sidebar'],
                           fg='#FFFFFF' if i == 0 else '#94A3B8',
                           relief='flat',
                           padx=20, pady=15,
                           anchor='w',
                           cursor='hand2',
                           command=lambda k=key: self.switch_tab(k))
            btn.pack(fill='x')
            self.menu_buttons[key] = btn
        
        # Выделение активного пункта
        self.menu_buttons['dashboard'].config(bg=self.colors['primary'], fg='#FFFFFF')
        
        # Область контента
        self.content_area = tk.Frame(main_area, bg=self.colors['bg_main'])
        self.content_area.pack(side='right', fill='both', expand=True)
        
        # Показываем дашборд
        self.switch_tab('dashboard')
    
    def switch_tab(self, tab_name: str):
        """Переключение вкладок"""
        # Сброс стилей кнопок
        for key, btn in self.menu_buttons.items():
            if key == tab_name:
                btn.config(bg=self.colors['primary'], fg='#FFFFFF')
            else:
                btn.config(bg=self.colors['bg_sidebar'], fg='#94A3B8')
        
        # Очистка контента
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        # Показ нужной вкладки
        if tab_name == 'dashboard':
            self.show_dashboard()
        elif tab_name == 'sales':
            self.show_sales_tab()
        elif tab_name == 'products':
            self.show_products_tab()
        elif tab_name == 'reports':
            self.show_reports_tab()
        elif tab_name == 'purchases' and self.current_user['role'] == 'admin':
            self.show_purchases_tab()
        elif tab_name == 'suppliers' and self.current_user['role'] == 'admin':
            self.show_suppliers_tab()
        elif tab_name == 'users' and self.current_user['role'] == 'admin':
            self.show_users_tab()
    
    def show_dashboard(self):
        """Главная панель"""
        container = tk.Frame(self.content_area, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Заголовок
        tk.Label(container, text="Панель управления", 
                font=self.fonts['title'], 
                bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(anchor='w', pady=(0, 20))
        
        # Карточки статистики
        stats_frame = tk.Frame(container, bg=self.colors['bg_main'])
        stats_frame.pack(fill='x', pady=10)
        
        # Получаем данные
        products = self.db.get_products()
        low_stock = self.db.get_low_stock_products()
        sales = self.db.get_sales_history(7)
        
        stats = [
            ("📦 Всего товаров", str(len(products)), self.colors['info']),
            ("⚠️ Низкий запас", str(len(low_stock)), self.colors['warning']),
            ("💰 Продаж за неделю", str(len(sales)), self.colors['success']),
            ("🏷️ Категорий", str(len(self.db.get_categories())), self.colors['accent']),
        ]
        
        for i, (title, value, color) in enumerate(stats):
            card = CardFrame(stats_frame, padx=20, pady=15)
            card.grid(row=0, column=i, padx=10, sticky='ew')
            stats_frame.columnconfigure(i, weight=1)
            
            tk.Label(card, text=title, font=self.fonts['normal'], 
                    bg=self.colors['bg_card'], 
                    fg=self.colors['text_muted']).pack(anchor='w')
            tk.Label(card, text=value, font=('Segoe UI', 28, 'bold'), 
                    bg=self.colors['bg_card'], 
                    fg=color).pack(anchor='w')
        
        # Предупреждения
        warnings_frame = tk.Frame(container, bg=self.colors['bg_main'])
        warnings_frame.pack(fill='both', expand=True, pady=20)
        
        if low_stock:
            tk.Label(warnings_frame, text="⚠️ Товары с низким запасом:", 
                    font=self.fonts['heading'], 
                    bg=self.colors['bg_main'],
                    fg=self.colors['warning']).pack(anchor='w', pady=(0, 10))
            
            columns = ('name', 'category', 'quantity', 'min_qty')
            tree = ttk.Treeview(warnings_frame, columns=columns, show='headings', height=5)
            
            headers = ["Товар", "Категория", "На складе", "Минимум"]
            for col, header in zip(columns, headers):
                tree.heading(col, text=header)
                tree.column(col, width=150)
            
            for item in low_stock[:5]:
                tree.insert('', 'end', values=(item['name'], item['category'], 
                                              f"{item['quantity']} {item['unit']}", 
                                              item['min_quantity']))
            
            tree.pack(fill='x')
    
    def show_products_tab(self):
        """Вкладка товаров"""
        container = tk.Frame(self.content_area, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Заголовок и кнопки
        header_frame = tk.Frame(container, bg=self.colors['bg_main'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(header_frame, text="Управление товарами", 
                font=self.fonts['title'], 
                bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(side='left')
        
        StyledButton(header_frame, text="+ Добавить товар", 
                    command=self.add_product_dialog).pack(side='right')
        
        # Фильтры
        filter_frame = tk.Frame(container, bg=self.colors['bg_main'])
        filter_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(filter_frame, text="Категория:", 
                font=self.fonts['normal'], 
                bg=self.colors['bg_main']).pack(side='left', padx=(0, 10))
        
        self.prod_category = tk.StringVar(value='all')
        cat_combo = ttk.Combobox(filter_frame, textvariable=self.prod_category, 
                                state='readonly', width=20)
        
        categories = [('Все категории', 'all')] + [(c[1], c[0]) for c in self.db.get_categories()]
        cat_combo['values'] = [c[0] for c in categories]
        cat_combo.current(0)
        cat_combo.pack(side='left', padx=(0, 20))
        cat_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_products_table())
        
        tk.Label(filter_frame, text="Поиск:", 
                font=self.fonts['normal'], 
                bg=self.colors['bg_main']).pack(side='left', padx=(0, 10))
        
        self.prod_search = StyledEntry(filter_frame, width=30)
        self.prod_search.pack(side='left', padx=(0, 10))
        self.prod_search.bind('<KeyRelease>', lambda e: self.refresh_products_table())
        
        # Таблица товаров
        table_frame = CardFrame(container)
        table_frame.pack(fill='both', expand=True)
        
        columns = ('id', 'name', 'category', 'brand', 'price', 'quantity', 'status')
        self.products_tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        headers = ["ID", "Название", "Категория", "Бренд", "Цена", "Кол-во", "Статус"]
        widths = [50, 250, 120, 100, 80, 80, 100]
        
        for col, header, width in zip(columns, headers, widths):
            self.products_tree.heading(col, text=header)
            self.products_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', 
                                 command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        
        self.products_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Контекстное меню
        self.products_tree.bind('<Double-1>', lambda e: self.edit_product_dialog())
        
        # Кнопки действий
        action_frame = tk.Frame(container, bg=self.colors['bg_main'])
        action_frame.pack(fill='x', pady=10)
        
        StyledButton(action_frame, text="✏️ Редактировать", 
                    command=self.edit_product_dialog).pack(side='left', padx=5)
        StyledButton(action_frame, text="🗑️ Удалить", 
                    command=self.delete_product, variant='danger').pack(side='left', padx=5)
        
        self.refresh_products_table()
    
    def refresh_products_table(self):
        """Обновление таблицы товаров"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        cat_value = self.prod_category.get()
        category_id = None if cat_value == 'all' else cat_value
        
        if category_id == 'all':
            category_id = None
        
        # Получаем ID категории если выбрано не "все"
        if cat_value != 'all':
            for cat in self.db.get_categories():
                if cat[1] == cat_value:
                    category_id = cat[0]
                    break
        
        search = self.prod_search.get()
        products = self.db.get_products(category_id, search)
        
        for p in products:
            status = "✓ В наличии" if p['quantity'] > p['min_quantity'] else "⚠️ Мало"
            if p['quantity'] == 0:
                status = "❌ Нет"
            
            self.products_tree.insert('', 'end', values=(
                p['id'], p['name'], p['category'], p['brand'],
                f"{p['price']:.0f} ₽", f"{p['quantity']} {p['unit']}", status
            ))
    
    def add_product_dialog(self):
        """Диалог добавления товара"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить товар")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'], padx=30, pady=20)
        frame.pack(fill='both', expand=True)
        
        categories = self.db.get_categories()
        
        fields = {
            'name': ('Название товара', ''),
            'brand': ('Бренд', ''),
            'price': ('Цена продажи (₽)', ''),
            'cost': ('Закупочная цена (₽)', ''),
            'quantity': ('Количество', '0'),
            'min_quantity': ('Мин. запас', '5'),
            'unit': ('Ед. измерения', 'шт'),
            'barcode': ('Штрихкод', ''),
            'expiry_date': ('Срок годности (ГГГГ-ММ-ДД)', ''),
            'description': ('Описание', ''),
        }
        
        entries = {}
        for key, (label, default) in fields.items():
            tk.Label(frame, text=label, bg=self.colors['bg_card'],
                    fg=self.colors['text_muted']).pack(anchor='w', pady=(10, 5))
            
            if key == 'category_id':
                entry = ttk.Combobox(frame, values=[c[1] for c in categories], state='readonly')
            else:
                entry = StyledEntry(frame)
                entry.insert(0, default)
            
            entry.pack(fill='x')
            entries[key] = entry
        
        # Категория отдельно
        tk.Label(frame, text="Категория", bg=self.colors['bg_card'],
                fg=self.colors['text_muted']).pack(anchor='w', pady=(10, 5))
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(frame, textvariable=category_var, 
                                     values=[c[1] for c in categories], state='readonly')
        category_combo.current(0)
        category_combo.pack(fill='x')
        
        def save():
            try:
                cat_name = category_var.get()
                cat_id = next(c[0] for c in categories if c[1] == cat_name)
                
                success, msg = self.db.add_product(
                    name=entries['name'].get(),
                    category_id=cat_id,
                    brand=entries['brand'].get(),
                    price=float(entries['price'].get()),
                    cost=float(entries['cost'].get()),
                    quantity=int(entries['quantity'].get()),
                    min_quantity=int(entries['min_quantity'].get()),
                    unit=entries['unit'].get(),
                    expiry_date=entries['expiry_date'].get() or None,
                    description=entries['description'].get(),
                    barcode=entries['barcode'].get()
                )
                
                if success:
                    messagebox.showinfo("Успех", msg)
                    dialog.destroy()
                    self.refresh_products_table()
                else:
                    messagebox.showerror("Ошибка", msg)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        StyledButton(frame, text="Сохранить", command=save).pack(pady=20)
    
    def edit_product_dialog(self):
        """Диалог редактирования товара"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар")
            return
        
        item = self.products_tree.item(selection[0])
        product_id = item['values'][0]
        
        products = self.db.get_products()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактировать товар")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'], padx=30, pady=20)
        frame.pack(fill='both', expand=True)
        
        fields = {
            'name': ('Название', product['name']),
            'brand': ('Бренд', product['brand'] or ''),
            'price': ('Цена (₽)', str(product['price'])),
            'cost': ('Закупка (₽)', str(product['cost'])),
            'quantity': ('Количество', str(product['quantity'])),
            'min_quantity': ('Мин. запас', str(product['min_quantity'])),
            'unit': ('Ед. изм.', product['unit']),
            'barcode': ('Штрихкод', product['barcode'] or ''),
            'expiry_date': ('Срок (ГГГГ-ММ-ДД)', product['expiry_date'] or ''),
            'description': ('Описание', product['description'] or ''),
        }
        
        entries = {}
        for key, (label, default) in fields.items():
            tk.Label(frame, text=label, bg=self.colors['bg_card'],
                    fg=self.colors['text_muted']).pack(anchor='w', pady=(10, 5))
            entry = StyledEntry(frame)
            entry.insert(0, default)
            entry.pack(fill='x')
            entries[key] = entry
        
        def save():
            try:
                success, msg = self.db.update_product(
                    product_id,
                    name=entries['name'].get(),
                    brand=entries['brand'].get(),
                    price=float(entries['price'].get()),
                    cost=float(entries['cost'].get()),
                    quantity=int(entries['quantity'].get()),
                    min_quantity=int(entries['min_quantity'].get()),
                    unit=entries['unit'].get(),
                    expiry_date=entries['expiry_date'].get() or None,
                    description=entries['description'].get(),
                    barcode=entries['barcode'].get()
                )
                
                if success:
                    messagebox.showinfo("Успех", msg)
                    dialog.destroy()
                    self.refresh_products_table()
                else:
                    messagebox.showerror("Ошибка", msg)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        StyledButton(frame, text="Сохранить", command=save).pack(pady=20)
    
    def delete_product(self):
        """Удаление товара"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите товар")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранный товар?"):
            item = self.products_tree.item(selection[0])
            product_id = item['values'][0]
            success, msg = self.db.delete_product(product_id)
            
            if success:
                messagebox.showinfo("Успех", msg)
                self.refresh_products_table()
            else:
                messagebox.showerror("Ошибка", msg)
    
    def show_sales_tab(self):
        """Вкладка продаж - единый интерфейс"""
        container = tk.Frame(self.content_area, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Заголовок
        header_frame = tk.Frame(container, bg=self.colors['bg_main'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(header_frame, text="🛒 Продажи", 
                font=self.fonts['title'], 
                bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(side='left')
        
        # Основная панель продаж (слева) и история (справа)
        main_pane = tk.PanedWindow(container, orient='horizontal', 
                                   bg=self.colors['bg_main'],
                                   sashwidth=8, sashrelief='raised')
        main_pane.pack(fill='both', expand=True)
        
        # ===== ЛЕВАЯ ПАНЕЛЬ - НОВАЯ ПРОДАЖА =====
        left_frame = CardFrame(main_pane, padx=15, pady=15)
        main_pane.add(left_frame, width=650)
        
        # Заголовок левой панели
        left_header = tk.Frame(left_frame, bg=self.colors['bg_card'])
        left_header.pack(fill='x', pady=(0, 15))
        
        tk.Label(left_header, text="➕ Новая продажа", 
                font=self.fonts['heading'], 
                bg=self.colors['bg_card'],
                fg=self.colors['primary']).pack(side='left')
        
        # Поиск товара
        search_frame = tk.Frame(left_frame, bg=self.colors['bg_card'])
        search_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(search_frame, text="🔍 Поиск:", 
                font=self.fonts['normal'],
                bg=self.colors['bg_card'],
                fg=self.colors['text_muted']).pack(side='left', padx=(0, 8))
        
        self.sale_search_entry = StyledEntry(search_frame, width=35)
        self.sale_search_entry.pack(side='left', fill='x', expand=True)
        self.sale_search_entry.bind('<KeyRelease>', lambda e: self.refresh_sale_products())
        
        # Список товаров для продажи
        products_container = CardFrame(left_frame, padx=5, pady=5)
        products_container.pack(fill='both', expand=True, pady=(0, 10))
        
        tk.Label(products_container, text="📦 Товары в наличии", 
                font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['bg_card'],
                fg=self.colors['text_main']).pack(fill='x', pady=(5, 10))
        
        columns = ('id', 'name', 'brand', 'price', 'quantity', 'unit')
        self.sale_products_tree = ttk.Treeview(products_container, columns=columns, show='headings', height=8)
        
        headers = ["ID", "Название", "Бренд", "Цена", "Остаток", "Ед."]
        widths = [40, 200, 100, 70, 60, 50]
        for col, header, width in zip(columns, headers, widths):
            self.sale_products_tree.heading(col, text=header)
            self.sale_products_tree.column(col, width=width, minwidth=width)
        
        scrollbar = ttk.Scrollbar(products_container, orient="vertical", command=self.sale_products_tree.yview)
        self.sale_products_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sale_products_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.sale_products_tree.bind('<Double-1>', lambda e: self.add_to_cart_from_tree())
        
        # Корзина
        cart_container = CardFrame(left_frame, padx=10, pady=10)
        cart_container.pack(fill='both', expand=True, pady=(0, 10))
        
        tk.Label(cart_container, text="🛒 Корзина покупателя", 
                font=('Segoe UI', 11, 'bold'), 
                bg=self.colors['bg_card'],
                fg=self.colors['accent']).pack(fill='x', pady=(0, 10))
        
        cart_columns = ('name', 'quantity', 'price', 'subtotal')
        self.cart_tree = ttk.Treeview(cart_container, columns=cart_columns, show='headings', height=5)
        
        cart_headers = ["Товар", "Кол-во", "Цена", "Сумма"]
        cart_widths = [180, 60, 70, 80]
        for col, header, width in zip(cart_columns, cart_headers, cart_widths):
            self.cart_tree.heading(col, text=header)
            self.cart_tree.column(col, width=width)
        
        self.cart_tree.pack(fill='x', pady=(0, 10))
        
        # Итого и оплата
        totals_frame = tk.Frame(cart_container, bg=self.colors['bg_card'])
        totals_frame.pack(fill='x')
        
        self.cart_total_label = tk.Label(totals_frame, text="Итого: 0 ₽", 
                              font=('Segoe UI', 16, 'bold'),
                              bg=self.colors['bg_card'],
                              fg=self.colors['primary'])
        self.cart_total_label.pack(side='left', padx=(0, 20))
        
        # Способ оплаты
        payment_frame = tk.Frame(totals_frame, bg=self.colors['bg_card'])
        payment_frame.pack(side='right')
        
        tk.Label(payment_frame, text="💳 Оплата:", 
                font=self.fonts['normal'],
                bg=self.colors['bg_card'],
                fg=self.colors['text_muted']).pack(side='left', padx=(0, 8))
        
        self.payment_var = tk.StringVar(value='cash')
        
        cash_btn = tk.Radiobutton(payment_frame, text="Наличные", variable=self.payment_var, 
                       value='cash', bg=self.colors['bg_card'],
                       activebackground=self.colors['bg_card'],
                       font=self.fonts['normal'],
                       selectcolor=self.colors['bg_card'])
        cash_btn.pack(side='left', padx=5)
        
        card_btn = tk.Radiobutton(payment_frame, text="Карта", variable=self.payment_var, 
                       value='card', bg=self.colors['bg_card'],
                       activebackground=self.colors['bg_card'],
                       font=self.fonts['normal'],
                       selectcolor=self.colors['bg_card'])
        card_btn.pack(side='left', padx=5)
        
        # Кнопки действий
        action_frame = tk.Frame(left_frame, bg=self.colors['bg_card'])
        action_frame.pack(fill='x', pady=(10, 0))
        
        StyledButton(action_frame, text="➕ Добавить", 
                    command=self.add_to_cart_from_tree, variant='primary').pack(side='left', padx=5)
        StyledButton(action_frame, text="➖ Удалить", 
                    command=self.remove_from_cart, variant='danger').pack(side='left', padx=5)
        StyledButton(action_frame, text="🗑 Очистить корзину", 
                    command=self.clear_cart, variant='secondary').pack(side='left', padx=5)
        
        # Скидка и завершение
        checkout_frame = tk.Frame(left_frame, bg=self.colors['bg_card'])
        checkout_frame.pack(fill='x', pady=(15, 0))
        
        discount_frame = tk.Frame(checkout_frame, bg=self.colors['bg_card'])
        discount_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(discount_frame, text="Скидка (₽):", 
                font=self.fonts['normal'],
                bg=self.colors['bg_card'],
                fg=self.colors['text_muted']).pack(side='left', padx=(0, 8))
        
        self.discount_entry = StyledEntry(discount_frame, width=10)
        self.discount_entry.insert(0, "0")
        self.discount_entry.pack(side='left')
        
        StyledButton(checkout_frame, text="✅ Оформить продажу", 
                    command=self.complete_sale, variant='success', 
                    padx=25, pady=10).pack(side='right')
        
        # Инициализация корзины
        self.cart = []
        self.refresh_sale_products()
        
        # ===== ПРАВАЯ ПАНЕЛЬ - ИСТОРИЯ ПРОДАЖ =====
        right_frame = CardFrame(main_pane, padx=15, pady=15)
        main_pane.add(right_frame, width=500)
        
        # Заголовок правой панели
        right_header = tk.Frame(right_frame, bg=self.colors['bg_card'])
        right_header.pack(fill='x', pady=(0, 15))
        
        tk.Label(right_header, text="📋 История продаж", 
                font=self.fonts['heading'], 
                bg=self.colors['bg_card'],
                fg=self.colors['info']).pack(side='left')
        
        # Фильтры
        filter_frame = tk.Frame(right_frame, bg=self.colors['bg_card'])
        filter_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(filter_frame, text="Период:", 
                font=self.fonts['normal'],
                bg=self.colors['bg_card'],
                fg=self.colors['text_muted']).pack(side='left', padx=(0, 8))
        
        self.history_days_var = tk.StringVar(value="7")
        days_combo = ttk.Combobox(filter_frame, textvariable=self.history_days_var, 
                                 values=["7", "14", "30", "90"], 
                                 width=5, state="readonly")
        days_combo.pack(side='left', padx=(0, 10))
        days_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_sales_history())
        
        StyledButton(filter_frame, text="Обновить", 
                    command=self.refresh_sales_history, variant='secondary').pack(side='left')
        
        # Таблица истории
        history_container = CardFrame(right_frame, padx=5, pady=5)
        history_container.pack(fill='both', expand=True)
        
        hist_columns = ('id', 'date', 'amount', 'payment', 'seller')
        self.sales_history_tree = ttk.Treeview(history_container, columns=hist_columns, show='headings', height=15)
        
        hist_headers = ["№", "Дата/Время", "Сумма", "Оплата", "Продавец"]
        hist_widths = [40, 130, 80, 70, 120]
        for col, header, width in zip(hist_columns, hist_headers, hist_widths):
            self.sales_history_tree.heading(col, text=header)
            self.sales_history_tree.column(col, width=width)
        
        hist_scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.sales_history_tree.yview)
        self.sales_history_tree.configure(yscrollcommand=hist_scrollbar.set)
        
        self.sales_history_tree.pack(side='left', fill='both', expand=True)
        hist_scrollbar.pack(side='right', fill='y')
        
        self.sales_history_tree.bind('<Double-1>', lambda e: self.show_sale_details())
        
        # Статистика за период
        stats_frame = tk.Frame(right_frame, bg=self.colors['bg_card'])
        stats_frame.pack(fill='x', pady=(10, 0))
        
        self.history_stats_label = tk.Label(stats_frame, text="", 
                                           font=self.fonts['normal'],
                                           bg=self.colors['bg_card'],
                                           fg=self.colors['text_muted'])
        self.history_stats_label.pack(side='left')
        
        self.refresh_sales_history()
    
    def refresh_sale_products(self):
        """Обновить список товаров для продажи"""
        for item in self.sale_products_tree.get_children():
            self.sale_products_tree.delete(item)
        
        search = self.sale_search_entry.get() if hasattr(self, 'sale_search_entry') else ""
        products = self.db.get_products(search=search)
        
        for p in products:
            if p['quantity'] > 0:
                self.sale_products_tree.insert('', 'end', values=(
                    p['id'], p['name'], p['brand'], 
                    f"{p['price']:.0f}", p['quantity'], p['unit']
                ))
    
    def add_to_cart_from_tree(self):
        """Добавить товар из дерева товаров в корзину"""
        selection = self.sale_products_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар из списка")
            return
        
        item = self.sale_products_tree.item(selection[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        price = float(item['values'][3])
        
        qty = simpledialog.askinteger("Количество", "Введите количество:", 
                                     initialvalue=1, minvalue=1)
        if qty and qty > 0:
            products = self.db.get_products()
            product = next((p for p in products if p['id'] == product_id), None)
            
            if product and qty <= product['quantity']:
                subtotal = price * qty
                
                # Проверяем, есть ли уже такой товар в корзине
                for cart_item in self.cart:
                    if cart_item['product_id'] == product_id:
                        cart_item['quantity'] += qty
                        cart_item['subtotal'] = cart_item['price'] * cart_item['quantity']
                        self.update_cart_display()
                        return
                
                self.cart.append({
                    'product_id': product_id,
                    'name': product_name,
                    'quantity': qty,
                    'price': price,
                    'subtotal': subtotal
                })
                self.update_cart_display()
            else:
                messagebox.showerror("Ошибка", "Недостаточно товара на складе")
    
    def update_cart_display(self):
        """Обновить отображение корзины"""
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        
        total = 0
        for item in self.cart:
            self.cart_tree.insert('', 'end', values=(
                item['name'], item['quantity'], 
                f"{item['price']:.0f}", f"{item['subtotal']:.0f}"
            ))
            total += item['subtotal']
        
        self.cart_total_label.config(text=f"Итого: {total:.0f} ₽")
    
    def remove_from_cart(self):
        """Удалить товар из корзины"""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар в корзине")
            return
        
        idx = self.cart_tree.index(selection[0])
        self.cart.pop(idx)
        self.update_cart_display()
    
    def clear_cart(self):
        """Очистить корзину"""
        self.cart = []
        self.update_cart_display()
    
    def complete_sale(self):
        """Завершить продажу"""
        if not self.cart:
            messagebox.showwarning("Предупреждение", "Корзина пуста")
            return
        
        try:
            discount = float(self.discount_entry.get() or 0)
            if discount < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректное значение скидки")
            return
        
        total = sum(item['subtotal'] for item in self.cart)
        if discount > total:
            messagebox.showerror("Ошибка", "Скидка не может превышать сумму заказа")
            return
        
        success, sale_id, msg = self.db.create_sale(
            items=self.cart,
            discount=discount,
            payment_method=self.payment_var.get(),
            seller_id=self.current_user['id'],
            customer_name='',
            notes=''
        )
        
        if success:
            messagebox.showinfo("Успех", f"Продажа #{sale_id} оформлена!\n{msg}")
            self.cart = []
            self.discount_entry.delete(0, 'end')
            self.discount_entry.insert(0, "0")
            self.update_cart_display()
            self.refresh_sale_products()
            self.refresh_sales_history()
        else:
            messagebox.showerror("Ошибка", msg)
    
    def refresh_sales_history(self):
        """Обновить историю продаж"""
        for item in self.sales_history_tree.get_children():
            self.sales_history_tree.delete(item)
        
        days = int(self.history_days_var.get())
        sales = self.db.get_sales_history(days)
        
        total_amount = 0
        for s in sales:
            self.sales_history_tree.insert('', 'end', values=(
                s['id'], 
                s['sale_date'][:16].replace('T', ' '),
                f"{s['final_amount']:.0f}",
                "💳" if s['payment_method'] == 'card' else "💵",
                s['seller_name'][:15]
            ))
            total_amount += s['final_amount']
        
        self.history_stats_label.config(
            text=f"📊 Продаж: {len(sales)} | Сумма: {total_amount:.0f} ₽"
        )
    
    def show_sale_details(self):
        """Показать детали продажи"""
        selection = self.sales_history_tree.selection()
        if not selection:
            return
        
        item = self.sales_history_tree.item(selection[0])
        sale_id = item['values'][0]
        
        # Получаем детали продажи из БД
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT si.product_id, si.name, si.quantity, si.price, si.subtotal
            FROM sale_items si
            WHERE si.sale_id = ?
        ''', (sale_id,))
        items = cursor.fetchall()
        conn.close()
        
        if not items:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Детали продажи #{sale_id}")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(frame, text=f"📋 Продажа #{sale_id}", 
                font=self.fonts['heading'],
                bg=self.colors['bg_card'],
                fg=self.colors['info']).pack(pady=(0, 15))
        
        columns = ('name', 'qty', 'price', 'subtotal')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        headers = ["Товар", "Кол-во", "Цена", "Сумма"]
        for col, header in zip(columns, headers):
            tree.heading(col, text=header)
            tree.column(col, width=100)
        
        tree.pack(fill='both', expand=True)
        
        for name, qty, price, subtotal in items:
            tree.insert('', 'end', values=(name[:25], qty, f"{price:.0f}", f"{subtotal:.0f}"))
        
        StyledButton(frame, text="Закрыть", 
                    command=dialog.destroy).pack(pady=(15, 0))
    
    def show_sales_history(self):
        """История продаж"""
        dialog = tk.Toplevel(self.root)
        dialog.title("История продаж")
        dialog.geometry("900x500")
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        columns = ('id', 'date', 'amount', 'payment', 'seller', 'customer')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        headers = ["№", "Дата", "Сумма", "Оплата", "Продавец", "Клиент"]
        widths = [50, 150, 100, 80, 150, 200]
        
        for col, header, width in zip(columns, headers, widths):
            tree.heading(col, text=header)
            tree.column(col, width=width)
        
        tree.pack(fill='both', expand=True)
        
        sales = self.db.get_sales_history(30)
        for s in sales:
            tree.insert('', 'end', values=(
                s['id'], s['date'], f"{s['amount']:.0f} ₽",
                'Наличные' if s['payment_method'] == 'cash' else 'Карта',
                s['seller'], s['customer'] or '-'
            ))
    
    def show_reports_tab(self):
        """Вкладка отчетов"""
        container = tk.Frame(self.content_area, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(container, text="Отчеты и аналитика", 
                font=self.fonts['title'], 
                bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(anchor='w', pady=(0, 20))
        
        # Кнопки отчетов
        btn_frame = tk.Frame(container, bg=self.colors['bg_main'])
        btn_frame.pack(fill='x', pady=10)
        
        StyledButton(btn_frame, text="⚠️ Низкий запас", 
                    command=self.show_low_stock_report).pack(side='left', padx=5)
        StyledButton(btn_frame, text="📅 Истекающий срок", 
                    command=self.show_expiring_report).pack(side='left', padx=5)
        StyledButton(btn_frame, text="📊 Продажи за период", 
                    command=self.show_sales_report).pack(side='left', padx=5)
    
    def show_low_stock_report(self):
        """Отчет по низкому запасу"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Товары с низким запасом")
        dialog.geometry("700x400")
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        columns = ('name', 'category', 'quantity', 'min_qty')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        headers = ["Товар", "Категория", "На складе", "Минимум"]
        for col, header in zip(columns, headers):
            tree.heading(col, text=header)
            tree.column(col, width=150)
        
        tree.pack(fill='both', expand=True)
        
        items = self.db.get_low_stock_products()
        for item in items:
            tree.insert('', 'end', values=(
                item['name'], item['category'],
                f"{item['quantity']} {item['unit']}", item['min_quantity']
            ))
    
    def show_expiring_report(self):
        """Отчет по истекающему сроку"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Товары с истекающим сроком")
        dialog.geometry("700x400")
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        columns = ('name', 'expiry_date', 'quantity')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        headers = ["Товар", "Срок годности", "Кол-во"]
        for col, header in zip(columns, headers):
            tree.heading(col, text=header)
            tree.column(col, width=200)
        
        tree.pack(fill='both', expand=True)
        
        items = self.db.get_expiring_products(60)
        for item in items:
            tree.insert('', 'end', values=(
                item['name'], item['expiry_date'], f"{item['quantity']} {item['unit']}"
            ))
    
    def show_sales_report(self):
        """Отчет по продажам"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Отчет по продажам")
        dialog.geometry("800x500")
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'])
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Период
        period_frame = tk.Frame(frame, bg=self.colors['bg_card'])
        period_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(period_frame, text="Дней:", bg=self.colors['bg_card']).pack(side='left')
        days_var = tk.StringVar(value='30')
        days_entry = StyledEntry(period_frame, textvariable=days_var, width=10)
        days_entry.pack(side='left', padx=10)
        
        def load_report():
            for item in tree.get_children():
                tree.delete(item)
            
            try:
                days = int(days_var.get())
            except:
                days = 30
            
            sales = self.db.get_sales_history(days)
            total = sum(s['amount'] for s in sales)
            
            for s in sales:
                tree.insert('', 'end', values=(
                    s['id'], s['date'], f"{s['amount']:.0f} ₽",
                    s['payment_method'], s['seller']
                ))
            
            total_label.config(text=f"Итого за {days} дней: {total:.0f} ₽")
        
        StyledButton(period_frame, text="Показать", command=load_report).pack(side='left')
        
        # Таблица
        columns = ('id', 'date', 'amount', 'payment', 'seller')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        headers = ["№", "Дата", "Сумма", "Оплата", "Продавец"]
        for col, header in zip(columns, headers):
            tree.heading(col, text=header)
            tree.column(col, width=120)
        
        tree.pack(fill='both', expand=True)
        
        total_label = tk.Label(frame, text="", 
                              font=self.fonts['heading'],
                              bg=self.colors['bg_card'],
                              fg=self.colors['primary'])
        total_label.pack(pady=10)
        
        load_report()
    
    def show_purchases_tab(self):
        """Вкладка закупок (только для админа)"""
        container = tk.Frame(self.content_area, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(container, text="Управление закупками", 
                font=self.fonts['title'], 
                bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(anchor='w', pady=(0, 20))
        
        # Кнопки
        btn_frame = tk.Frame(container, bg=self.colors['bg_main'])
        btn_frame.pack(fill='x', pady=10)
        
        StyledButton(btn_frame, text="+ Новый заказ", 
                    command=self.new_purchase_order).pack(side='left', padx=5)
        StyledButton(btn_frame, text="🔄 Обновить", 
                    command=lambda: self.refresh_orders_table()).pack(side='left', padx=5)
        
        # Фильтр по статусу
        filter_frame = tk.Frame(container, bg=self.colors['bg_main'])
        filter_frame.pack(fill='x', pady=10)
        
        tk.Label(filter_frame, text="Статус:", 
                bg=self.colors['bg_main']).pack(side='left', padx=(0, 10))
        
        self.order_status = tk.StringVar(value='all')
        status_combo = ttk.Combobox(filter_frame, textvariable=self.order_status,
                                   values=['all', 'draft', 'sent', 'in_transit', 'delivered', 'cancelled'],
                                   state='readonly', width=15)
        status_combo.current(0)
        status_combo.pack(side='left')
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_orders_table())
        
        # Таблица заказов
        table_frame = CardFrame(container)
        table_frame.pack(fill='both', expand=True, pady=10)
        
        columns = ('id', 'supplier', 'date', 'expected', 'status', 'total', 'created_by')
        self.orders_tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        headers = ["№", "Поставщик", "Дата заказа", "Ожидается", "Статус", "Сумма", "Создал"]
        widths = [50, 200, 120, 120, 100, 100, 150]
        
        status_colors = {
            'draft': '#6B7280',
            'sent': '#3B82F6',
            'in_transit': '#F59E0B',
            'delivered': '#22C55E',
            'cancelled': '#EF4444'
        }
        
        for col, header, width in zip(columns, headers, widths):
            self.orders_tree.heading(col, text=header)
            self.orders_tree.column(col, width=width)
        
        self.orders_tree.pack(fill='both', expand=True)
        
        # Кнопки действий
        action_frame = tk.Frame(container, bg=self.colors['bg_main'])
        action_frame.pack(fill='x', pady=10)
        
        StyledButton(action_frame, text="👁️ Просмотреть", 
                    command=self.view_order_details).pack(side='left', padx=5)
        StyledButton(action_frame, text="📝 Изменить статус", 
                    command=self.change_order_status).pack(side='left', padx=5)
        
        self.refresh_orders_table()
    
    def refresh_orders_table(self):
        """Обновление таблицы заказов"""
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        
        status = self.order_status.get()
        status_filter = None if status == 'all' else status
        
        orders = self.db.get_purchase_orders(status_filter)
        
        status_names = {
            'draft': 'Черновик',
            'sent': 'Отправлен',
            'in_transit': 'В пути',
            'delivered': 'Доставлен',
            'cancelled': 'Отменен'
        }
        
        for o in orders:
            status_name = status_names.get(o['status'], o['status'])
            self.orders_tree.insert('', 'end', values=(
                o['id'], o['supplier'], o['order_date'][:10], 
                o['expected_date'] or '-', status_name,
                f"{o['total_cost']:.0f} ₽", o['created_by']
            ))
    
    def new_purchase_order(self):
        """Создание нового заказа"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый заказ поставщику")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'], padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        # Выбор поставщика
        tk.Label(frame, text="Поставщик:", bg=self.colors['bg_card']).pack(anchor='w', pady=(0, 5))
        
        suppliers = self.db.get_suppliers()
        supplier_var = tk.StringVar()
        supplier_combo = ttk.Combobox(frame, textvariable=supplier_var,
                                     values=[s['name'] for s in suppliers], state='readonly')
        supplier_combo.current(0)
        supplier_combo.pack(fill='x', pady=(0, 15))
        
        # Дата ожидания
        tk.Label(frame, text="Ожидаемая дата доставки (ГГГГ-ММ-ДД):", 
                bg=self.colors['bg_card']).pack(anchor='w', pady=(0, 5))
        
        expected_date = StyledEntry(frame)
        expected_date.insert(0, (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
        expected_date.pack(fill='x', pady=(0, 15))
        
        # Примечание
        tk.Label(frame, text="Примечание:", bg=self.colors['bg_card']).pack(anchor='w', pady=(0, 5))
        
        notes = StyledEntry(frame)
        notes.pack(fill='x', pady=(0, 20))
        
        def create_order():
            if not supplier_var.get():
                messagebox.showerror("Ошибка", "Выберите поставщика")
                return
            
            supplier = next((s for s in suppliers if s['name'] == supplier_var.get()), None)
            
            success, order_id, msg = self.db.create_purchase_order(
                supplier_id=supplier['id'],
                expected_date=expected_date.get(),
                notes=notes.get(),
                user_id=self.current_user['id']
            )
            
            if success:
                # Добавление товаров в заказ
                self.add_items_to_order(order_id)
                dialog.destroy()
                self.refresh_orders_table()
            else:
                messagebox.showerror("Ошибка", msg)
        
        StyledButton(frame, text="Создать заказ", command=create_order).pack()
    
    def add_items_to_order(self, order_id: int):
        """Добавление товаров в заказ"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить товары в заказ")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'], padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        # Выбор товара
        tk.Label(frame, text="Товар:", bg=self.colors['bg_card']).pack(anchor='w', pady=(0, 5))
        
        products = self.db.get_products()
        product_var = tk.StringVar()
        product_combo = ttk.Combobox(frame, textvariable=product_var,
                                    values=[f"{p['id']}. {p['name']} ({p['cost']} ₽)" for p in products],
                                    state='readonly')
        product_combo.current(0)
        product_combo.pack(fill='x', pady=(0, 15))
        
        # Количество
        tk.Label(frame, text="Количество:", bg=self.colors['bg_card']).pack(anchor='w', pady=(0, 5))
        
        qty_entry = StyledEntry(frame)
        qty_entry.insert(0, '10')
        qty_entry.pack(fill='x', pady=(0, 20))
        
        def add_item():
            if not product_var.get():
                return
            
            product_str = product_var.get()
            product_id = int(product_str.split('.')[0])
            product = next((p for p in products if p['id'] == product_id), None)
            
            try:
                quantity = int(qty_entry.get())
            except:
                messagebox.showerror("Ошибка", "Неверное количество")
                return
            
            success, msg = self.db.add_order_item(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                cost_price=product['cost']
            )
            
            if success:
                if messagebox.askyesno("Продолжить", "Товар добавлен. Добавить еще?"):
                    pass
                else:
                    dialog.destroy()
            else:
                messagebox.showerror("Ошибка", msg)
        
        StyledButton(frame, text="Добавить товар", command=add_item).pack()
    
    def view_order_details(self):
        """Просмотр деталей заказа"""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите заказ")
            return
        
        item = self.orders_tree.item(selection[0])
        order_id = item['values'][0]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Заказ #{order_id}")
        dialog.geometry("600x400")
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'], padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        # Информация о заказе
        orders = self.db.get_purchase_orders()
        order = next((o for o in orders if o['id'] == order_id), None)
        
        if order:
            info = f"""
            Поставщик: {order['supplier']}
            Дата заказа: {order['order_date']}
            Ожидаемая дата: {order['expected_date'] or '-'}
            Статус: {order['status']}
            Общая сумма: {order['total_cost']:.0f} ₽
            Примечание: {order['notes'] or '-'}
            """
            
            tk.Label(frame, text=info, bg=self.colors['bg_card'],
                    justify='left', font=self.fonts['normal']).pack(anchor='w', pady=(0, 20))
        
        # Товары в заказе
        tk.Label(frame, text="Товары в заказе:", bg=self.colors['bg_card'],
                font=self.fonts['heading']).pack(anchor='w', pady=(0, 10))
        
        columns = ('product', 'quantity', 'price', 'subtotal')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
        
        headers = ["Товар", "Кол-во", "Цена", "Сумма"]
        for col, header in zip(columns, headers):
            tree.heading(col, text=header)
            tree.column(col, width=120)
        
        tree.pack(fill='both', expand=True)
        
        items = self.db.get_order_items(order_id)
        for i in items:
            tree.insert('', 'end', values=(
                i['product_name'], i['quantity'],
                f"{i['cost_price']:.0f} ₽", f"{i['subtotal']:.0f} ₽"
            ))
    
    def change_order_status(self):
        """Изменение статуса заказа"""
        selection = self.orders_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите заказ")
            return
        
        item = self.orders_tree.item(selection[0])
        order_id = item['values'][0]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Изменить статус заказа")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'], padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Выберите новый статус:", 
                bg=self.colors['bg_card'], font=self.fonts['normal']).pack(pady=10)
        
        status_var = tk.StringVar(value='in_transit')
        statuses = [
            ('draft', 'Черновик'),
            ('sent', 'Отправлен'),
            ('in_transit', 'В пути'),
            ('delivered', 'Доставлен'),
            ('cancelled', 'Отменен')
        ]
        
        for value, label in statuses:
            ttk.Radiobutton(frame, text=label, variable=status_var,
                          value=value, bg=self.colors['bg_card']).pack(anchor='w', pady=5)
        
        def save_status():
            success, msg = self.db.update_order_status(order_id, status_var.get())
            
            if success:
                messagebox.showinfo("Успех", msg)
                dialog.destroy()
                self.refresh_orders_table()
            else:
                messagebox.showerror("Ошибка", msg)
        
        StyledButton(frame, text="Сохранить", command=save_status).pack(pady=20)
    
    def show_suppliers_tab(self):
        """Вкладка поставщиков (только для админа)"""
        container = tk.Frame(self.content_area, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(container, text="Управление поставщиками", 
                font=self.fonts['title'], 
                bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(anchor='w', pady=(0, 20))
        
        StyledButton(container, text="+ Добавить поставщика", 
                    command=self.add_supplier_dialog).pack(anchor='w', pady=10)
        
        # Таблица поставщиков
        table_frame = CardFrame(container)
        table_frame.pack(fill='both', expand=True, pady=10)
        
        columns = ('id', 'name', 'contact', 'phone', 'email', 'address')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        headers = ["№", "Название", "Контактное лицо", "Телефон", "Email", "Адрес"]
        widths = [50, 200, 150, 120, 180, 200]
        
        for col, header, width in zip(columns, headers, widths):
            tree.heading(col, text=header)
            tree.column(col, width=width)
        
        tree.pack(fill='both', expand=True)
        
        suppliers = self.db.get_suppliers()
        for s in suppliers:
            tree.insert('', 'end', values=(
                s['id'], s['name'], s['contact_person'] or '-',
                s['phone'] or '-', s['email'] or '-', s['address'] or '-'
            ))
    
    def add_supplier_dialog(self):
        """Диалог добавления поставщика"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить поставщика")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=self.colors['bg_card'], padx=30, pady=20)
        frame.pack(fill='both', expand=True)
        
        fields = {
            'name': ('Название компании', ''),
            'contact_person': ('Контактное лицо', ''),
            'phone': ('Телефон', ''),
            'email': ('Email', ''),
            'address': ('Адрес', ''),
            'notes': ('Примечание', ''),
        }
        
        entries = {}
        for key, (label, default) in fields.items():
            tk.Label(frame, text=label, bg=self.colors['bg_card'],
                    fg=self.colors['text_muted']).pack(anchor='w', pady=(10, 5))
            entry = StyledEntry(frame)
            entry.insert(0, default)
            entry.pack(fill='x')
            entries[key] = entry
        
        def save():
            success, msg = self.db.add_supplier(
                name=entries['name'].get(),
                contact_person=entries['contact_person'].get(),
                phone=entries['phone'].get(),
                email=entries['email'].get(),
                address=entries['address'].get(),
                notes=entries['notes'].get()
            )
            
            if success:
                messagebox.showinfo("Успех", msg)
                dialog.destroy()
                self.show_suppliers_tab()
            else:
                messagebox.showerror("Ошибка", msg)
        
        StyledButton(frame, text="Сохранить", command=save).pack(pady=20)
    
    def show_users_tab(self):
        """Вкладка пользователей (только для админа)"""
        container = tk.Frame(self.content_area, bg=self.colors['bg_main'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(container, text="Управление пользователями", 
                font=self.fonts['title'], 
                bg=self.colors['bg_main'],
                fg=self.colors['text_main']).pack(anchor='w', pady=(0, 20))
        
        # Таблица пользователей
        table_frame = CardFrame(container)
        table_frame.pack(fill='both', expand=True, pady=10)
        
        columns = ('id', 'username', 'full_name', 'role', 'created', 'active')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        headers = ["№", "Логин", "ФИО", "Роль", "Создан", "Активен"]
        widths = [50, 120, 200, 100, 150, 80]
        
        for col, header, width in zip(columns, headers, widths):
            tree.heading(col, text=header)
            tree.column(col, width=width)
        
        tree.pack(fill='both', expand=True)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, full_name, role, created_at, is_active
            FROM users ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        
        for u in users:
            tree.insert('', 'end', values=(
                u[0], u[1], u[2],
                'Админ' if u[3] == 'admin' else 'Продавец',
                u[4][:10], '✓' if u[5] else '✗'
            ))
    
    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            self.current_user = None
            self.show_login_screen()


# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = VetPharmacyApp(root)
    root.mainloop()
