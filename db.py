import sqlite3
from sqlite3 import Error
import time

def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class Db_handler:
    def __init__(self, db):
        self.connection = None
        try:
            self.connection = sqlite3.connect(db)
            print("SQLite connected succesfully")
        except Error as e:
            print(f"Error: '{e}'")
    
    def select_classes(self, source_id):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(f"SELECT class_type, class_value FROM sources_classes WHERE source_id = {source_id}")
            result = cursor.fetchall()
            return dict(result)
        except Error as e:
            print(f"Error: '{e}'")
            
    def select_sources(self):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute("SELECT * FROM sources")
            result = cursor.fetchall()
            return list(result)
        except Error as e:
            print(f"Error: '{e}'")
    
    def select_products(self):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(f"SELECT * FROM products")
            result = cursor.fetchall()
            return list(result)
        except Error as e:
            print(f"Error: '{e}'")
    
    def select_aspects(self, prod_id):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(f"SELECT * FROM aspects WHERE product_id = {prod_id}")
            result = cursor.fetchall()
            return list(result)
        except Error as e:
            print(f"Error: '{e}'")
            
    def select_aspects_count(self, fb_id):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(f"SELECT count(*) FROM aspects_feedback WHERE fb_id = {fb_id}")
            result = cursor.fetchone()
            return int(result[0])
        except Error as e:
            print(f"Error: '{e}'")
            
            
    def select_feedback(self, prod_id):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(f"SELECT * FROM feedback WHERE product_id = {prod_id}")
            result = cursor.fetchall()
            return list(result)
        except Error as e:
            print(f"Error: '{e}'")
            
    def select_categories(self):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute("SELECT * FROM categories")
            result = cursor.fetchall()
            return list(result)
        except Error as e:
            print(f"Error: '{e}'")
            
    def select_tonality_category(self, category_id):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(f"SELECT value, tonality FROM aspects_feedback WHERE aspect_id IN (SELECT aspect_id FROM aspects WHERE product_id in (SELECT product_id FROM products WHERE category_id = {category_id}))")
            result = cursor.fetchall()
            return list(result)
        except Error as e:
            print(f"Error: '{e}'")
        
    def select_result(self, prod_id, aspect_id):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(f"SELECT distinct f.date, f.stars, f.text, f.likes, f.disslikes, f.helpfullness, af.tonality FROM feedback f LEFT JOIN aspects_feedback af USING(fb_id) WHERE f.product_id = {prod_id} and af.aspect_id = {aspect_id} ORDER BY f.helpfullness DESC")
            result = cursor.fetchall()
            return list(result)
        except Error as e:
            print(f"Error: '{e}'")
            
    def insert_feedback(self, prod_id, feedback):
        cursor = self.connection.cursor()
        try: 
            for review in feedback:
                cursor.execute(f"INSERT INTO feedback(product_id, date, stars, text, likes, disslikes) VALUES({prod_id}, '" + review['date'] + f"', {review['stars']}, '"+ review['text'] + f"', {review['likes']}, {review['disslikes']})")
            print("Запрос успешно выполнен")
            self.connection.commit()     
        except Error as e:
                print(f"Error: '{e}'")
        
    def insert_product(self, title, url, source_id, category_id):
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"INSERT INTO products(title, url, source_id, category_id) VALUES (\'{title}\', '{url}', {source_id}, {category_id})")
            self.connection.commit()
            print("Запрос успешно выполнен")
        except Error as e:
            print(f"Error: '{e}'")
            raise e
            
    def insert_aspects(self, prod_id, aspects):
        cursor = self.connection.cursor()
        try:
            for aspect in aspects:
                cursor.execute(f"INSERT INTO aspects(product_id, value) VALUES ({prod_id}, \'{aspect['aspect']}\')")
            self.connection.commit()
            print("Запрос успешно выполнен")
        except Error as e:
            print(f"Error: '{e}'")
            raise e
        
    
    def insert_tonality(self, tonal):
        cursor = self.connection.cursor()
        try:
            for ton in tonal:
                cursor.execute(f"INSERT INTO aspects_feedback(aspect_id, fb_id, value, tonality) VALUES ({ton[1]}, {ton[0]}, \'{ton[2]}\', {ton[3]})")
            self.connection.commit()
            print("Запрос успешно выполнен")
        except Error as e:
            print(f"Error: '{e}'")
            raise e
    
        
    def set_collecting_time(self, product_id): 
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"UPDATE products SET last_collecting_time = {time.time()} WHERE product_id = {product_id}")
            self.connection.commit()
            print("Запрос успешно выполнен")
        except Error as e:
            print(f"Error: '{e}'")
            raise e
        
    def update_helpfullness(self, feedback, helpfullness): 
        cursor = self.connection.cursor()
        try:
            for i in range(len(helpfullness)):
                cursor.execute(f"UPDATE feedback SET helpfullness = {helpfullness[i]} WHERE fb_id = {feedback[i][0]}")
            self.connection.commit()
            print("Запрос успешно выполнен")
        except Error as e:
            print(f"Error: '{e}'")
            raise e
        
    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            print("Соединение с MySQL закрыто")
    
db = Db_handler('database.db')