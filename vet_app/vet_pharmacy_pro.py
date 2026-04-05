#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ветеринарная аптека PRO - Система управления запасами и продажами
С базой данных SQLite, регистрацией пользователей и современным дизайном
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import sqlite3
import hashlib
import os
import json


class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_name="vet_pharmacy.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        self.initialize_sample_data()
    
    def connect(self):
        """Подключение к базе данных"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
    
    def create_tables(self):
        """Создание таблиц"""
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'seller',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица товаров
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                unit TEXT NOT NULL,
                manufacturer TEXT,
                expiration_date TEXT,
                min_quantity INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица продаж
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL NOT NULL,
                customer_name TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Таблица элементов продаж
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        self.conn.commit()
    
    def initialize_sample_data(self):
        """Инициализация тестовыми данными"""
        # Проверка наличия пользователей
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            # Создаем администратора по умолчанию
            admin_hash = self.hash_password("admin123")
            self.cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', ("admin", admin_hash, "Администратор", "admin"))
            
            # Создаем продавца
            seller_hash = self.hash_password("seller123")
            self.cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', ("seller", seller_hash, "Продавец", "seller"))
            
            self.conn.commit()
        
        # Проверка наличия товаров
        self.cursor.execute("SELECT COUNT(*) FROM products")
        if self.cursor.fetchone()[0] == 0:
            sample_products = [
                ("Royal Canin Adult Dog", "Корма", 2500, 50, "кг", "Royal Canin", 
                 (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y"), 10),
                ("Whiskas для кошек", "Корма", 450, 100, "шт", "Mars",
                 (datetime.now() + timedelta(days=240)).strftime("%d.%m.%Y"), 20),
                ("Амоксициллин вет.", "Лекарства", 350, 30, "фл", "Нита-Фарм",
                 (datetime.now() + timedelta(days=540)).strftime("%d.%m.%Y"), 5),
                ("Ошейник от блох", "Аксессуары", 890, 25, "шт", "Beaphar",
                 (datetime.now() + timedelta(days=730)).strftime("%d.%m.%Y"), 10),
                ("Шампунь для собак", "Гигиена", 650, 40, "мл", "TropiClean",
                 (datetime.now() + timedelta(days=400)).strftime("%d.%m.%Y"), 15),
                ("Витамины для кошек", "Витамины", 420, 60, "таб", "Canina",
                 (datetime.now() + timedelta(days=500)).strftime("%d.%m.%Y"), 20),
                ("Лакомство для собак", "Корма", 280, 80, "г", "Pedigree",
                 (datetime.now() + timedelta(days=180)).strftime("%d.%m.%Y"), 25),
            ]
            
            self.cursor.executemany('''
                INSERT INTO products (name, category, price, quantity, unit, 
                                     manufacturer, expiration_date, min_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_products)
            
            self.conn.commit()
    
    @staticmethod
    def hash_password(password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username, password):
        """Проверка пользователя"""
        password_hash = self.hash_password(password)
        self.cursor.execute('''
            SELECT id, username, full_name, role FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        return self.cursor.fetchone()
    
    def register_user(self, username, password, full_name, role='seller'):
        """Регистрация нового пользователя"""
        try:
            password_hash = self.hash_password(password)
            self.cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, full_name, role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_products(self):
        """Получение всех товаров"""
        self.cursor.execute('''
            SELECT id, name, category, price, quantity, unit, manufacturer, 
                   expiration_date, min_quantity FROM products ORDER BY name
        ''')
        return self.cursor.fetchall()
    
    def get_product_by_id(self, product_id):
        """Получение товара по ID"""
        self.cursor.execute('''
            SELECT id, name, category, price, quantity, unit, manufacturer, 
                   expiration_date, min_quantity FROM products WHERE id = ?
        ''', (product_id,))
        return self.cursor.fetchone()
    
    def add_product(self, name, category, price, quantity, unit, manufacturer, 
                    expiration_date, min_quantity=10):
        """Добавление товара"""
        self.cursor.execute('''
            INSERT INTO products (name, category, price, quantity, unit, manufacturer,
                                 expiration_date, min_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, category, price, quantity, unit, manufacturer, expiration_date, min_quantity))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def update_product(self, product_id, name, category, price, quantity, unit,
                       manufacturer, expiration_date, min_quantity):
        """Обновление товара"""
        self.cursor.execute('''
            UPDATE products SET name=?, category=?, price=?, quantity=?, unit=?,
                               manufacturer=?, expiration_date=?, min_quantity=?,
                               updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (name, category, price, quantity, unit, manufacturer, expiration_date, 
              min_quantity, product_id))
        self.conn.commit()
    
    def delete_product(self, product_id):
        """Удаление товара"""
        self.cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        self.conn.commit()
    
    def update_product_quantity(self, product_id, quantity_change):
        """Изменение количества товара"""
        self.cursor.execute('''
            UPDATE products SET quantity = quantity + ?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (quantity_change, product_id))
        self.conn.commit()
    
    def get_low_stock_products(self, threshold=10):
        """Получение товаров с низким запасом"""
        self.cursor.execute('''
            SELECT id, name, category, quantity, min_quantity FROM products 
            WHERE quantity <= min_quantity ORDER BY quantity
        ''')
        return self.cursor.fetchall()
    
    def get_expiring_products(self, days=30):
        """Получение товаров с истекающим сроком годности"""
        cutoff_date = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
        self.cursor.execute('''
            SELECT id, name, category, expiration_date, quantity FROM products 
            WHERE expiration_date <= ? ORDER BY expiration_date
        ''', (cutoff_date,))
        return self.cursor.fetchall()
    
    def create_sale(self, items, total_amount, customer_name, user_id):
        """Создание продажи"""
        # Создаем запись о продаже
        self.cursor.execute('''
            INSERT INTO sales (total_amount, customer_name, user_id)
            VALUES (?, ?, ?)
        ''', (total_amount, customer_name, user_id))
        sale_id = self.cursor.lastrowid
        
        # Добавляем элементы продажи
        for item in items:
            product_id, product_name, quantity, price = item
            subtotal = quantity * price
            self.cursor.execute('''
                INSERT INTO sale_items (sale_id, product_id, product_name, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sale_id, product_id, product_name, quantity, price, subtotal))
            
            # Обновляем количество товара на складе
            self.update_product_quantity(product_id, -quantity)
        
        self.conn.commit()
        return sale_id
    
    def get_sales_history(self, start_date=None, end_date=None):
        """Получение истории продаж"""
        if start_date and end_date:
            self.cursor.execute('''
                SELECT s.id, s.sale_date, s.total_amount, s.customer_name, u.full_name,
                       COUNT(si.id) as items_count
                FROM sales s
                LEFT JOIN users u ON s.user_id = u.id
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE date(s.sale_date) BETWEEN date(?) AND date(?)
                GROUP BY s.id
                ORDER BY s.sale_date DESC
            ''', (start_date, end_date))
        else:
            self.cursor.execute('''
                SELECT s.id, s.sale_date, s.total_amount, s.customer_name, u.full_name,
                       COUNT(si.id) as items_count
                FROM sales s
                LEFT JOIN users u ON s.user_id = u.id
                LEFT JOIN sale_items si ON s.id = si.sale_id
                GROUP BY s.id
                ORDER BY s.sale_date DESC
            ''')
        return self.cursor.fetchall()
    
    def get_sale_details(self, sale_id):
        """Получение деталей продажи"""
        self.cursor.execute('''
            SELECT product_name, quantity, price, subtotal FROM sale_items
            WHERE sale_id = ?
        ''', (sale_id,))
        return self.cursor.fetchall()
    
    def get_categories(self):
        """Получение всех категорий"""
        self.cursor.execute('SELECT DISTINCT category FROM products ORDER BY category')
        return [row[0] for row in self.cursor.fetchall()]
    
    def search_products(self, search_term):
        """Поиск товаров"""
        search_pattern = f"%{search_term}%"
        self.cursor.execute('''
            SELECT id, name, category, price, quantity, unit, manufacturer, 
                   expiration_date, min_quantity FROM products 
            WHERE name LIKE ? OR manufacturer LIKE ? OR category LIKE ?
            ORDER BY name
        ''', (search_pattern, search_pattern, search_pattern))
        return self.cursor.fetchall()
    
    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()


class StyleConfig:
    """Конфигурация стилей"""
    
    # Цветовая палитра
    COLORS = {
        'primary': '#2E86AB',
        'primary_dark': '#1A5F7A',
        'secondary': '#56C596',
        'accent': '#F6B93B',
        'danger': '#E74C3C',
        'warning': '#F39C12',
        'success': '#27AE60',
        'background': '#F8F9FA',
        'surface': '#FFFFFF',
        'text_primary': '#2C3E50',
        'text_secondary': '#7F8C8D',
        'border': '#E0E0E0',
        'error': '#FFE6E6',
        'low_stock': '#FFF3CD'
    }
    
    # Шрифты
    FONTS = {
        'title': ('Helvetica', 24, 'bold'),
        'subtitle': ('Helvetica', 16, 'bold'),
        'heading': ('Helvetica', 14, 'bold'),
        'body': ('Helvetica', 11),
        'small': ('Helvetica', 9),
        'button': ('Helvetica', 11, 'bold'),
        'entry': ('Helvetica', 11)
    }


class LoginWindow:
    """Окно входа"""
    
    def __init__(self, root, db_manager, on_login_success):
        self.root = root
        self.db_manager = db_manager
        self.on_login_success = on_login_success
        
        self.root.title("Ветеринарная аптека - Вход")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        self.root.configure(bg=StyleConfig.COLORS['background'])
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg=colors['surface'], padx=40, pady=40)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Логотип/Заголовок
        logo_label = tk.Label(
            main_frame, 
            text="🏥 ВетАптека",
            font=('Helvetica', 32, 'bold'),
            bg=colors['surface'],
            fg=colors['primary']
        )
        logo_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Система управления",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_secondary']
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Форма входа
        form_frame = tk.Frame(main_frame, bg=colors['surface'])
        form_frame.pack(fill='x')
        
        # Username
        tk.Label(
            form_frame, 
            text="Имя пользователя",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_primary'],
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))
        
        self.username_entry = tk.Entry(
            form_frame,
            font=fonts['entry'],
            bg=colors['background'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        self.username_entry.pack(fill='x', pady=(0, 20))
        self.username_entry.insert(0, "admin")
        
        # Password
        tk.Label(
            form_frame,
            text="Пароль",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_primary'],
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))
        
        self.password_entry = tk.Entry(
            form_frame,
            font=fonts['entry'],
            show='•',
            bg=colors['background'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        self.password_entry.pack(fill='x', pady=(0, 30))
        self.password_entry.insert(0, "admin123")
        
        # Кнопка входа
        login_btn = tk.Button(
            form_frame,
            text="Войти",
            font=fonts['button'],
            bg=colors['primary'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.login
        )
        login_btn.pack(fill='x', pady=(0, 10))
        login_btn.bind('<Enter>', lambda e: login_btn.config(bg=colors['primary_dark']))
        login_btn.bind('<Leave>', lambda e: login_btn.config(bg=colors['primary']))
        
        # Кнопка регистрации
        register_btn = tk.Button(
            form_frame,
            text="Зарегистрироваться",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['primary'],
            relief='flat',
            cursor='hand2',
            command=self.open_registration
        )
        register_btn.pack(fill='x')
        register_btn.bind('<Enter>', lambda e: register_btn.config(fg=colors['primary_dark']))
        register_btn.bind('<Leave>', lambda e: register_btn.config(fg=colors['primary']))
        
        # Информация о тестовых учетках
        info_frame = tk.Frame(main_frame, bg=colors['error'], padx=15, pady=10)
        info_frame.pack(fill='x', pady=(30, 0))
        
        tk.Label(
            info_frame,
            text="💡 Тестовые учетки:\nadmin / admin123 или seller / seller123",
            font=fonts['small'],
            bg=colors['error'],
            fg=colors['text_primary'],
            justify='left'
        ).pack()
    
    def login(self):
        """Вход в систему"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите имя пользователя и пароль")
            return
        
        user = self.db_manager.verify_user(username, password)
        
        if user:
            user_data = {
                'id': user[0],
                'username': user[1],
                'full_name': user[2],
                'role': user[3]
            }
            self.on_login_success(user_data)
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")
    
    def open_registration(self):
        """Открытие окна регистрации"""
        RegistrationWindow(self.root, self.db_manager)


class RegistrationWindow:
    """Окно регистрации"""
    
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        
        self.window = tk.Toplevel(parent)
        self.window.title("Регистрация")
        self.window.geometry("500x650")
        self.window.resizable(False, False)
        self.window.configure(bg=StyleConfig.COLORS['background'])
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        # Основной фрейм
        main_frame = tk.Frame(self.window, bg=colors['surface'], padx=40, pady=30)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Заголовок
        tk.Label(
            main_frame,
            text="📝 Регистрация",
            font=fonts['subtitle'],
            bg=colors['surface'],
            fg=colors['primary']
        ).pack(pady=(0, 30))
        
        # Форма
        form_frame = tk.Frame(main_frame, bg=colors['surface'])
        form_frame.pack(fill='both', expand=True)
        
        # Имя пользователя
        tk.Label(
            form_frame,
            text="Имя пользователя *",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_primary'],
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))
        
        self.username_entry = tk.Entry(
            form_frame,
            font=fonts['entry'],
            bg=colors['background'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        self.username_entry.pack(fill='x', pady=(0, 15))
        
        # Полное имя
        tk.Label(
            form_frame,
            text="Полное имя *",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_primary'],
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))
        
        self.fullname_entry = tk.Entry(
            form_frame,
            font=fonts['entry'],
            bg=colors['background'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        self.fullname_entry.pack(fill='x', pady=(0, 15))
        
        # Пароль
        tk.Label(
            form_frame,
            text="Пароль *",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_primary'],
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))
        
        self.password_entry = tk.Entry(
            form_frame,
            font=fonts['entry'],
            show='•',
            bg=colors['background'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        self.password_entry.pack(fill='x', pady=(0, 15))
        
        # Подтверждение пароля
        tk.Label(
            form_frame,
            text="Подтвердите пароль *",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_primary'],
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))
        
        self.confirm_password_entry = tk.Entry(
            form_frame,
            font=fonts['entry'],
            show='•',
            bg=colors['background'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        self.confirm_password_entry.pack(fill='x', pady=(0, 20))
        
        # Роль
        tk.Label(
            form_frame,
            text="Роль",
            font=fonts['body'],
            bg=colors['surface'],
            fg=colors['text_primary'],
            anchor='w'
        ).pack(anchor='w', pady=(0, 5))
        
        self.role_var = tk.StringVar(value="seller")
        role_combo = ttk.Combobox(
            form_frame,
            textvariable=self.role_var,
            values=["seller", "admin"],
            state="readonly",
            font=fonts['entry']
        )
        role_combo.pack(fill='x', pady=(0, 20))
        
        # Кнопки
        btn_frame = tk.Frame(form_frame, bg=colors['surface'])
        btn_frame.pack(fill='x')
        
        register_btn = tk.Button(
            btn_frame,
            text="Зарегистрировать",
            font=fonts['button'],
            bg=colors['primary'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.register
        )
        register_btn.pack(side='left', fill='x', expand=True, padx=(0, 10))
        register_btn.bind('<Enter>', lambda e: register_btn.config(bg=colors['primary_dark']))
        register_btn.bind('<Leave>', lambda e: register_btn.config(bg=colors['primary']))
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Отмена",
            font=fonts['button'],
            bg=colors['border'],
            fg=colors['text_primary'],
            relief='flat',
            cursor='hand2',
            command=self.window.destroy
        )
        cancel_btn.pack(side='left', fill='x', expand=True)
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(bg='#d0d0d0'))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(bg=colors['border']))
    
    def register(self):
        """Регистрация пользователя"""
        username = self.username_entry.get().strip()
        fullname = self.fullname_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        role = self.role_var.get()
        
        # Валидация
        if not username or not fullname or not password:
            messagebox.showerror("Ошибка", "Все обязательные поля должны быть заполнены")
            return
        
        if len(username) < 3:
            messagebox.showerror("Ошибка", "Имя пользователя должно содержать минимум 3 символа")
            return
        
        if len(password) < 6:
            messagebox.showerror("Ошибка", "Пароль должен содержать минимум 6 символов")
            return
        
        if password != confirm_password:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        
        # Регистрация
        success = self.db_manager.register_user(username, password, fullname, role)
        
        if success:
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован!\nТеперь вы можете войти.")
            self.window.destroy()
        else:
            messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует")


class MainApplication:
    """Основное приложение"""
    
    CATEGORIES = ["Корма", "Лекарства", "Аксессуары", "Гигиена", "Витамины"]
    UNITS = ["шт", "кг", "г", "л", "мл", "уп", "фл", "таб"]
    
    def __init__(self, root, db_manager, user_data):
        self.root = root
        self.db_manager = db_manager
        self.user_data = user_data
        
        self.root.title("Ветеринарная аптека - Панель управления")
        self.root.geometry("1400x900")
        self.root.configure(bg=StyleConfig.COLORS['background'])
        
        self.current_view = None
        self.cart = []
        
        self.setup_ui()
        self.show_inventory()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg=colors['primary'], height=80)
        top_frame.pack(fill='x')
        top_frame.pack_propagate(False)
        
        # Логотип
        logo_label = tk.Label(
            top_frame,
            text="🏥 ВетАптека PRO",
            font=('Helvetica', 20, 'bold'),
            bg=colors['primary'],
            fg='white'
        )
        logo_label.pack(side='left', padx=30, pady=20)
        
        # Информация о пользователе
        user_info = f"👤 {self.user_data['full_name']} ({self.user_data['role']})"
        user_label = tk.Label(
            top_frame,
            text=user_info,
            font=fonts['body'],
            bg=colors['primary'],
            fg='white'
        )
        user_label.pack(side='right', padx=30, pady=25)
        
        # Кнопка выхода
        logout_btn = tk.Button(
            top_frame,
            text="Выход",
            font=fonts['small'],
            bg=colors['danger'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.logout
        )
        logout_btn.pack(side='right', padx=10, pady=25)
        
        # Боковая панель навигации
        sidebar = tk.Frame(self.root, bg=colors['surface'], width=200)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        nav_buttons = [
            ("📦 Товары", self.show_inventory),
            ("🛒 Продажа", self.show_pos),
            ("📊 Отчеты", self.show_reports),
            ("⚠️ Низкий запас", self.show_low_stock),
            ("📅 Истекает срок", self.show_expiring),
        ]
        
        for i, (text, command) in enumerate(nav_buttons):
            btn = tk.Button(
                sidebar,
                text=text,
                font=fonts['body'],
                bg=colors['surface'],
                fg=colors['text_primary'],
                relief='flat',
                cursor='hand2',
                command=command,
                anchor='w',
                padx=20,
                pady=15
            )
            btn.pack(fill='x')
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=colors['background'], fg=colors['primary']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=colors['surface'], fg=colors['text_primary']))
        
        # Основная область контента
        self.content_frame = tk.Frame(self.root, bg=colors['background'])
        self.content_frame.pack(side='right', expand=True, fill='both')
    
    def clear_content(self):
        """Очистка контента"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_inventory(self):
        """Отображение управления товарами"""
        self.clear_content()
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        # Заголовок
        header_frame = tk.Frame(self.content_frame, bg=colors['background'])
        header_frame.pack(fill='x', padx=30, pady=20)
        
        tk.Label(
            header_frame,
            text="📦 Управление товарами",
            font=fonts['subtitle'],
            bg=colors['background'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        # Панель инструментов
        toolbar = tk.Frame(header_frame, bg=colors['background'])
        toolbar.pack(side='right')
        
        add_btn = tk.Button(
            toolbar,
            text="+ Добавить товар",
            font=fonts['button'],
            bg=colors['secondary'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.add_product_dialog
        )
        add_btn.pack(side='left', padx=5)
        
        refresh_btn = tk.Button(
            toolbar,
            text="🔄 Обновить",
            font=fonts['button'],
            bg=colors['primary'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.show_inventory
        )
        refresh_btn.pack(side='left', padx=5)
        
        # Поиск и фильтр
        filter_frame = tk.Frame(self.content_frame, bg=colors['background'])
        filter_frame.pack(fill='x', padx=30, pady=(0, 20))
        
        tk.Label(
            filter_frame,
            text="Поиск:",
            font=fonts['body'],
            bg=colors['background'],
            fg=colors['text_primary']
        ).pack(side='left', padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_products())
        
        search_entry = tk.Entry(
            filter_frame,
            textvariable=self.search_var,
            font=fonts['entry'],
            width=30,
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        search_entry.pack(side='left', padx=(0, 20))
        
        tk.Label(
            filter_frame,
            text="Категория:",
            font=fonts['body'],
            bg=colors['background'],
            fg=colors['text_primary']
        ).pack(side='left', padx=(0, 10))
        
        self.category_filter = ttk.Combobox(
            filter_frame,
            values=["Все"] + self.CATEGORIES,
            state="readonly",
            width=15,
            font=fonts['entry']
        )
        self.category_filter.set("Все")
        self.category_filter.bind('<<ComboboxSelected>>', lambda e: self.filter_products())
        self.category_filter.pack(side='left')
        
        # Таблица товаров
        table_frame = tk.Frame(self.content_frame, bg=colors['surface'])
        table_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        columns = ('ID', 'Название', 'Категория', 'Цена', 'Кол-во', 'Ед.', 'Производитель', 'Срок годности')
        
        self.inventory_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=100 if col != 'Название' else 200)
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inventory_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Контекстное меню
        self.inventory_tree.bind('<Double-1>', self.edit_product)
        self.inventory_tree.bind('<Button-3>', self.show_context_menu)
        
        # Загрузка данных
        self.load_products()
    
    def load_products(self, products=None):
        """Загрузка товаров в таблицу"""
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        if products is None:
            products = self.db_manager.get_all_products()
        
        for product in products:
            tags = ()
            if product[4] <= product[8]:  # quantity <= min_quantity
                tags = ('low_stock',)
            
            self.inventory_tree.insert('', 'end', values=product, tags=tags)
        
        self.inventory_tree.tag_configure('low_stock', background=StyleConfig.COLORS['low_stock'])
    
    def filter_products(self):
        """Фильтрация товаров"""
        search_term = self.search_var.get().lower()
        category = self.category_filter.get()
        
        products = self.db_manager.get_all_products()
        filtered = []
        
        for p in products:
            match_search = (search_term in p[1].lower() or 
                          search_term in p[6].lower() if p[6] else True)
            match_category = category == "Все" or p[2] == category
            
            if match_search and match_category:
                filtered.append(p)
        
        self.load_products(filtered)
    
    def add_product_dialog(self):
        """Диалог добавления товара"""
        ProductDialog(self.root, self.db_manager, callback=self.show_inventory)
    
    def edit_product(self, event):
        """Редактирование товара"""
        selection = self.inventory_tree.selection()
        if not selection:
            return
        
        item = self.inventory_tree.item(selection[0])
        product_id = item['values'][0]
        
        product = self.db_manager.get_product_by_id(product_id)
        if product:
            ProductDialog(self.root, self.db_manager, product=product, callback=self.show_inventory)
    
    def show_context_menu(self, event):
        """Показ контекстного меню"""
        selection = self.inventory_tree.selection()
        if not selection:
            return
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="✏️ Редактировать", command=lambda: self.edit_product(event))
        menu.add_command(label="🗑️ Удалить", command=self.delete_selected_product)
        menu.post(event.x_root, event.y_root)
    
    def delete_selected_product(self):
        """Удаление выбранного товара"""
        selection = self.inventory_tree.selection()
        if not selection:
            return
        
        item = self.inventory_tree.item(selection[0])
        product_id = item['values'][0]
        product_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить товар '{product_name}'?"):
            self.db_manager.delete_product(product_id)
            self.show_inventory()
    
    def show_pos(self):
        """Отображение точки продаж"""
        self.clear_content()
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        # Разделение на две панели
        paned = tk.PanedWindow(self.content_frame, orient='horizontal', bg=colors['background'])
        paned.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Левая панель - товары
        left_frame = tk.Frame(paned, bg=colors['surface'])
        paned.add(left_frame, width=700)
        
        tk.Label(
            left_frame,
            text="🛍️ Товары",
            font=fonts['subtitle'],
            bg=colors['surface'],
            fg=colors['text_primary']
        ).pack(padx=20, pady=15)
        
        # Поиск
        search_frame = tk.Frame(left_frame, bg=colors['surface'])
        search_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        self.pos_search_var = tk.StringVar()
        self.pos_search_var.trace('w', lambda *args: self.filter_pos_products())
        
        pos_search = tk.Entry(
            search_frame,
            textvariable=self.pos_search_var,
            font=fonts['entry'],
            relief='flat',
            highlightthickness=2,
            highlightbackground=colors['border'],
            highlightcolor=colors['primary']
        )
        pos_search.pack(fill='x')
        pos_search.insert(0, "Поиск товара...")
        pos_search.bind('<FocusIn>', lambda e: pos_search.delete(0, 'end') if pos_search.get() == "Поиск товара..." else None)
        
        # Список товаров
        products_list_frame = tk.Frame(left_frame, bg=colors['surface'])
        products_list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.pos_products = {}
        products = self.db_manager.get_all_products()
        
        canvas = tk.Canvas(products_list_frame, bg=colors['surface'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(products_list_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors['surface'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        for product in products:
            product_id, name, category, price, quantity, unit, *_ = product
            
            if quantity > 0:
                item_frame = tk.Frame(scrollable_frame, bg=colors['background'], padx=15, pady=10)
                item_frame.pack(fill='x', padx=10, pady=5)
                
                info_frame = tk.Frame(item_frame, bg=colors['background'])
                info_frame.pack(side='left', fill='both', expand=True)
                
                tk.Label(
                    info_frame,
                    text=name,
                    font=fonts['heading'],
                    bg=colors['background'],
                    fg=colors['text_primary'],
                    anchor='w'
                ).pack(anchor='w')
                
                tk.Label(
                    info_frame,
                    text=f"{price} ₽ | В наличии: {quantity} {unit}",
                    font=fonts['body'],
                    bg=colors['background'],
                    fg=colors['text_secondary'],
                    anchor='w'
                ).pack(anchor='w')
                
                qty_frame = tk.Frame(item_frame, bg=colors['background'])
                qty_frame.pack(side='right', padx=10)
                
                qty_spinbox = tk.Spinbox(
                    qty_frame,
                    from_=1,
                    to=quantity,
                    width=5,
                    font=fonts['entry'],
                    justify='center'
                )
                qty_spinbox.pack(side='left', padx=5)
                qty_spinbox.delete(0, 'end')
                qty_spinbox.insert(0, '1')
                
                add_btn = tk.Button(
                    qty_frame,
                    text="➕",
                    font=fonts['button'],
                    bg=colors['secondary'],
                    fg='white',
                    relief='flat',
                    cursor='hand2',
                    width=3,
                    command=lambda pid=product_id, n=name, p=price, qs=qty_spinbox: self.add_to_cart(pid, n, p, qs)
                )
                add_btn.pack(side='left', padx=5)
                
                self.pos_products[product_id] = {
                    'frame': item_frame,
                    'name': name,
                    'price': price,
                    'quantity': quantity
                }
        
        # Правая панель - корзина
        right_frame = tk.Frame(paned, bg=colors['surface'])
        paned.add(right_frame)
        
        tk.Label(
            right_frame,
            text="🛒 Корзина",
            font=fonts['subtitle'],
            bg=colors['surface'],
            fg=colors['text_primary']
        ).pack(padx=20, pady=15)
        
        # Таблица корзины
        cart_columns = ('Товар', 'Цена', 'Кол-во', 'Сумма')
        self.cart_tree = ttk.Treeview(right_frame, columns=cart_columns, show='headings', height=15)
        
        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=100)
        
        self.cart_tree.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Кнопки корзины
        cart_buttons = tk.Frame(right_frame, bg=colors['surface'])
        cart_buttons.pack(fill='x', padx=20, pady=10)
        
        remove_btn = tk.Button(
            cart_buttons,
            text="Удалить",
            font=fonts['button'],
            bg=colors['danger'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.remove_from_cart
        )
        remove_btn.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        clear_btn = tk.Button(
            cart_buttons,
            text="Очистить",
            font=fonts['button'],
            bg=colors['warning'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.clear_cart
        )
        clear_btn.pack(side='left', fill='x', expand=True, padx=5)
        
        # Итого
        total_frame = tk.Frame(right_frame, bg=colors['primary'], padx=20, pady=15)
        total_frame.pack(fill='x', padx=20, pady=10)
        
        self.total_label = tk.Label(
            total_frame,
            text="Итого: 0 ₽",
            font=('Helvetica', 18, 'bold'),
            bg=colors['primary'],
            fg='white'
        )
        self.total_label.pack()
        
        # Оформление продажи
        checkout_btn = tk.Button(
            right_frame,
            text="✅ Оформить продажу",
            font=('Helvetica', 14, 'bold'),
            bg=colors['success'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.checkout
        )
        checkout_btn.pack(fill='x', padx=20, pady=10)
        checkout_btn.bind('<Enter>', lambda e: checkout_btn.config(bg='#1e8449'))
        checkout_btn.bind('<Leave>', lambda e: checkout_btn.config(bg=colors['success']))
    
    def filter_pos_products(self):
        """Фильтрация товаров в POS"""
        search_term = self.pos_search_var.get().lower()
        
        for product_id, data in self.pos_products.items():
            if search_term in data['name'].lower() or search_term == "поиск товара...":
                data['frame'].pack(fill='x', padx=10, pady=5)
            else:
                data['frame'].pack_forget()
    
    def add_to_cart(self, product_id, name, price, qty_spinbox):
        """Добавление в корзину"""
        try:
            quantity = int(qty_spinbox.get())
        except ValueError:
            quantity = 1
        
        product_data = self.pos_products[product_id]
        if quantity > product_data['quantity']:
            messagebox.showwarning("Предупреждение", "Недостаточно товара на складе")
            return
        
        # Проверяем, есть ли уже товар в корзине
        for item in self.cart:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                item['subtotal'] = item['quantity'] * item['price']
                self.update_cart_display()
                return
        
        # Добавляем новый товар
        self.cart.append({
            'product_id': product_id,
            'name': name,
            'price': price,
            'quantity': quantity,
            'subtotal': quantity * price
        })
        
        self.update_cart_display()
    
    def update_cart_display(self):
        """Обновление отображения корзины"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        total = 0
        for item in self.cart:
            self.cart_tree.insert('', 'end', values=(
                item['name'],
                f"{item['price']} ₽",
                item['quantity'],
                f"{item['subtotal']} ₽"
            ))
            total += item['subtotal']
        
        self.total_label.config(text=f"Итого: {total} ₽")
    
    def remove_from_cart(self):
        """Удаление из корзины"""
        selection = self.cart_tree.selection()
        if not selection:
            return
        
        index = self.cart_tree.index(selection[0])
        del self.cart[index]
        self.update_cart_display()
    
    def clear_cart(self):
        """Очистка корзины"""
        self.cart = []
        self.update_cart_display()
    
    def checkout(self):
        """Оформление продажи"""
        if not self.cart:
            messagebox.showwarning("Предупреждение", "Корзина пуста")
            return
        
        customer_name = simpledialog.askstring("Покупатель", "Введите имя покупателя (необязательно):")
        
        if customer_name is None:
            return
        
        total = sum(item['subtotal'] for item in self.cart)
        
        if messagebox.askyesno("Подтверждение", f"Оформить продажу на сумму {total} ₽?"):
            items = [(item['product_id'], item['name'], item['quantity'], item['price']) 
                     for item in self.cart]
            
            self.db_manager.create_sale(items, total, customer_name or "Розничный покупатель", 
                                        self.user_data['id'])
            
            messagebox.showinfo("Успех", "Продажа успешно оформлена!")
            self.cart = []
            self.update_cart_display()
            self.show_pos()  # Обновить доступное количество
    
    def show_reports(self):
        """Отображение отчетов"""
        self.clear_content()
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        # Заголовок
        header_frame = tk.Frame(self.content_frame, bg=colors['background'])
        header_frame.pack(fill='x', padx=30, pady=20)
        
        tk.Label(
            header_frame,
            text="📊 История продаж",
            font=fonts['subtitle'],
            bg=colors['background'],
            fg=colors['text_primary']
        ).pack(side='left')
        
        # Фильтр по датам
        date_frame = tk.Frame(header_frame, bg=colors['background'])
        date_frame.pack(side='right')
        
        tk.Label(date_frame, text="С:", font=fonts['body'], bg=colors['background']).pack(side='left', padx=5)
        start_date = tk.Entry(date_frame, width=12, font=fonts['entry'])
        start_date.pack(side='left', padx=5)
        start_date.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        
        tk.Label(date_frame, text="По:", font=fonts['body'], bg=colors['background']).pack(side='left', padx=5)
        end_date = tk.Entry(date_frame, width=12, font=fonts['entry'])
        end_date.pack(side='left', padx=5)
        end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        filter_btn = tk.Button(
            date_frame,
            text="Применить",
            font=fonts['button'],
            bg=colors['primary'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=lambda: self.load_sales_history(start_date.get(), end_date.get())
        )
        filter_btn.pack(side='left', padx=10)
        
        # Таблица продаж
        table_frame = tk.Frame(self.content_frame, bg=colors['surface'])
        table_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        columns = ('ID', 'Дата', 'Сумма', 'Покупатель', 'Продавец', 'Товаров')
        self.sales_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=100 if col != 'Покупатель' else 150)
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sales_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.sales_tree.bind('<Double-1>', self.show_sale_details)
        
        self.load_sales_history()
    
    def load_sales_history(self, start_date=None, end_date=None):
        """Загрузка истории продаж"""
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
        
        sales = self.db_manager.get_sales_history(start_date, end_date)
        
        for sale in sales:
            self.sales_tree.insert('', 'end', values=sale)
    
    def show_sale_details(self, event):
        """Показ деталей продажи"""
        selection = self.sales_tree.selection()
        if not selection:
            return
        
        item = self.sales_tree.item(selection[0])
        sale_id = item['values'][0]
        
        details = self.db_manager.get_sale_details(sale_id)
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Детали продажи #{sale_id}")
        detail_window.geometry("500x400")
        detail_window.configure(bg=StyleConfig.COLORS['surface'])
        
        text_widget = tk.Text(detail_window, font=StyleConfig.FONTS['body'])
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        
        text_widget.insert('1.0', f"Детали продажи #{sale_id}\n\n")
        text_widget.insert('2.0', f"{'Товар':<30} {'Кол-во':>8} {'Цена':>10} {'Сумма':>10}\n")
        text_widget.insert('3.0', "-" * 60 + "\n")
        
        for i, detail in enumerate(details, 4):
            text_widget.insert(f'{i}.0', f"{detail[0]:<30} {detail[1]:>8} {detail[2]:>9.2f} {detail[3]:>9.2f}\n")
        
        text_widget.config(state='disabled')
    
    def show_low_stock(self):
        """Отображение товаров с низким запасом"""
        self.clear_content()
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        tk.Label(
            self.content_frame,
            text="⚠️ Товары с низким запасом",
            font=fonts['subtitle'],
            bg=colors['background'],
            fg=colors['warning']
        ).pack(padx=30, pady=20)
        
        table_frame = tk.Frame(self.content_frame, bg=colors['surface'])
        table_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        columns = ('ID', 'Название', 'Категория', 'Остаток', 'Минимум')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        products = self.db_manager.get_low_stock_products()
        for product in products:
            tree.insert('', 'end', values=product)
    
    def show_expiring(self):
        """Отображение товаров с истекающим сроком"""
        self.clear_content()
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        tk.Label(
            self.content_frame,
            text="📅 Товары с истекающим сроком годности",
            font=fonts['subtitle'],
            bg=colors['background'],
            fg=colors['danger']
        ).pack(padx=30, pady=20)
        
        table_frame = tk.Frame(self.content_frame, bg=colors['surface'])
        table_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        columns = ('ID', 'Название', 'Категория', 'Срок годности', 'Остаток')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        products = self.db_manager.get_expiring_products()
        for product in products:
            tree.insert('', 'end', values=product)
    
    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.db_manager.close()
            self.root.destroy()
            root = tk.Tk()
            start_application(root)


class ProductDialog:
    """Диалог добавления/редактирования товара"""
    
    def __init__(self, parent, db_manager, product=None, callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.product = product
        self.callback = callback
        
        self.is_edit = product is not None
        
        self.window = tk.Toplevel(parent)
        self.window.title("Добавить товар" if not self.is_edit else "Редактировать товар")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        self.window.configure(bg=StyleConfig.COLORS['background'])
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        colors = StyleConfig.COLORS
        fonts = StyleConfig.FONTS
        
        main_frame = tk.Frame(self.window, bg=colors['surface'], padx=40, pady=30)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        title = "✏️ Редактирование товара" if self.is_edit else "📦 Новый товар"
        tk.Label(
            main_frame,
            text=title,
            font=fonts['subtitle'],
            bg=colors['surface'],
            fg=colors['primary']
        ).pack(pady=(0, 30))
        
        form_frame = tk.Frame(main_frame, bg=colors['surface'])
        form_frame.pack(fill='both', expand=True)
        
        fields = [
            ("Название*", "name"),
            ("Категория*", "category", MainApplication.CATEGORIES),
            ("Цена (₽)*", "price"),
            ("Количество*", "quantity"),
            ("Единица измерения*", "unit", MainApplication.UNITS),
            ("Производитель", "manufacturer"),
            ("Срок годности (ДД.ММ.ГГГГ)*", "expiration_date"),
            ("Мин. запас", "min_quantity")
        ]
        
        self.entries = {}
        
        for i, field in enumerate(fields):
            label_text = field[0]
            field_name = field[1]
            
            tk.Label(
                form_frame,
                text=label_text,
                font=fonts['body'],
                bg=colors['surface'],
                fg=colors['text_primary'],
                anchor='w'
            ).pack(anchor='w', pady=(10 if i > 0 else 0, 5))
            
            if len(field) == 3:
                # Combobox
                var = tk.StringVar()
                combo = ttk.Combobox(form_frame, textvariable=var, values=field[2], 
                                    state="readonly", font=fonts['entry'])
                combo.pack(fill='x')
                self.entries[field_name] = var
            else:
                # Entry
                entry = tk.Entry(
                    form_frame,
                    font=fonts['entry'],
                    bg=colors['background'],
                    relief='flat',
                    highlightthickness=2,
                    highlightbackground=colors['border'],
                    highlightcolor=colors['primary']
                )
                entry.pack(fill='x')
                self.entries[field_name] = entry
        
        # Заполнение данными при редактировании
        if self.is_edit and self.product:
            self.entries['name'].insert(0, self.product[1])
            self.entries['category'].set(self.product[2])
            self.entries['price'].insert(0, str(self.product[3]))
            self.entries['quantity'].insert(0, str(self.product[4]))
            self.entries['unit'].set(self.product[5])
            self.entries['manufacturer'].insert(0, self.product[6] or '')
            self.entries['expiration_date'].insert(0, self.product[7])
            self.entries['min_quantity'].insert(0, str(self.product[8]))
        
        # Кнопки
        btn_frame = tk.Frame(main_frame, bg=colors['surface'])
        btn_frame.pack(fill='x', pady=(30, 0))
        
        save_btn = tk.Button(
            btn_frame,
            text="Сохранить",
            font=fonts['button'],
            bg=colors['success'],
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.save
        )
        save_btn.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Отмена",
            font=fonts['button'],
            bg=colors['border'],
            fg=colors['text_primary'],
            relief='flat',
            cursor='hand2',
            command=self.window.destroy
        )
        cancel_btn.pack(side='left', fill='x', expand=True)
    
    def save(self):
        """Сохранение товара"""
        try:
            data = {
                'name': self.entries['name'].get().strip(),
                'category': self.entries['category'].get(),
                'price': float(self.entries['price'].get()),
                'quantity': int(self.entries['quantity'].get()),
                'unit': self.entries['unit'].get(),
                'manufacturer': self.entries['manufacturer'].get().strip(),
                'expiration_date': self.entries['expiration_date'].get().strip(),
                'min_quantity': int(self.entries['min_quantity'].get() or 10)
            }
            
            # Валидация
            if not data['name'] or not data['category'] or not data['expiration_date']:
                messagebox.showerror("Ошибка", "Заполните все обязательные поля")
                return
            
            if data['price'] <= 0 or data['quantity'] < 0:
                messagebox.showerror("Ошибка", "Цена и количество должны быть положительными")
                return
            
            if self.is_edit:
                self.db_manager.update_product(
                    self.product[0], data['name'], data['category'], data['price'],
                    data['quantity'], data['unit'], data['manufacturer'],
                    data['expiration_date'], data['min_quantity']
                )
            else:
                self.db_manager.add_product(
                    data['name'], data['category'], data['price'], data['quantity'],
                    data['unit'], data['manufacturer'], data['expiration_date'],
                    data['min_quantity']
                )
            
            messagebox.showinfo("Успех", "Товар успешно сохранен!")
            self.window.destroy()
            
            if self.callback:
                self.callback()
                
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат данных: {e}")


def start_application(root):
    """Запуск приложения"""
    db_manager = DatabaseManager()
    
    def on_login_success(user_data):
        root.destroy()
        new_root = tk.Tk()
        MainApplication(new_root, db_manager, user_data)
        new_root.mainloop()
    
    LoginWindow(root, db_manager, on_login_success)


if __name__ == "__main__":
    root = tk.Tk()
    
    # Настройка стиля
    style = ttk.Style()
    style.theme_use('clam')
    
    # Конфигурация цветов для виджетов
    style.configure('Treeview', 
                    background='#FFFFFF',
                    foreground='#2C3E50',
                    fieldbackground='#FFFFFF',
                    rowheight=28,
                    font=('Helvetica', 10))
    style.configure('Treeview.Heading', 
                    font=('Helvetica', 11, 'bold'),
                    background='#2E86AB',
                    foreground='white')
    style.map('Treeview', background=[('selected', '#56C596')])
    
    style.configure('TCombobox', 
                    fieldbackground='#FFFFFF',
                    background='#FFFFFF',
                    arrowcolor='#2E86AB')
    
    start_application(root)
    root.mainloop()
