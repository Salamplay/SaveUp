from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
import sqlite3
import random

Window.clearcolor = (0.05, 0.06, 0.08, 1) # Темный фон

JOKES = {
    "deposit": ["Ого, план?", "Деньги на месте", "Пахнет богатством", "Обманул маркетологов"],
    "withdraw": ["Бюджет вышел", "Камеры не видели", "Свободу деньгам", "Минус деньги"]
}

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("saveup.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, title TEXT, target REAL, current REAL DEFAULT 0)")
        self.conn.commit()

    def get_goals(self):
        return self.cursor.execute("SELECT * FROM goals").fetchall()

    def add_goal(self, title, target):
        self.cursor.execute("INSERT INTO goals (title, target) VALUES (?, ?)", (title, target))
        self.conn.commit()

    def add_money(self, goal_id, amount, is_deposit=True):
        if is_deposit:
            self.cursor.execute("UPDATE goals SET current = current + ? WHERE id = ?", (amount, goal_id))
        else:
            self.cursor.execute("UPDATE goals SET current = max(0, current - ?) WHERE id = ?", (amount, goal_id))
        self.conn.commit()

class SaveUpApp(App):
    def build(self):
        self.db = Database()
        self.root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.balance_label = Label(text="Баланс: 0 ₽", size_hint_y=None, height=40, font_size='20sp', color=(0.6, 0.6, 1, 1))
        self.root.add_widget(self.balance_label)
        
        self.scroll = ScrollView()
        self.goals_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.goals_list.bind(minimum_height=self.goals_list.setter('height'))
        self.scroll.add_widget(self.goals_list)
        self.root.add_widget(self.scroll)
        
        add_btn = Button(text="+ Новая цель", size_hint_y=None, height=50, background_color=(0.4, 0.3, 0.8, 1))
        add_btn.bind(on_release=self.show_add_popup)
        self.root.add_widget(add_btn)
        
        self.load_goals()
        return self.root

    def load_goals(self):
        self.goals_list.clear_widgets()
        goals = self.db.get_goals()
        total = sum(g[3] for g in goals)
        self.balance_label.text = f"Баланс: {total:.0f} ₽"

        if not goals:
            self.goals_list.add_widget(Label(text="Пока пусто. Нажми +", size_hint_y=None, height=50, color=(0.5, 0.5, 0.5, 1)))

        for g in goals:
            gid, title, target, current = g
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=120, padding=10)
            
            box.add_widget(Label(text=f"{title}", size_hint_y=None, height=30, bold=True, color=(1,1,1,1)))
            box.add_widget(Label(text=f"{current:.0f} ₽ / {target:.0f} ₽", size_hint_y=None, height=30, color=(0.6, 0.6, 1, 1)))
            
            btn_box = BoxLayout(spacing=10)
            b_add = Button(text="+", background_color=(0, 0.7, 0.5, 1), on_release=lambda x, i=gid: self.show_money_popup(i, True))
            b_sub = Button(text="-", background_color=(0.8, 0.3, 0.3, 1), on_release=lambda x, i=gid: self.show_money_popup(i, False))
            btn_box.add_widget(b_add)
            btn_box.add_widget(b_sub)
            box.add_widget(btn_box)
            
            self.goals_list.add_widget(box)

    def show_add_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10)
        self.title_input = TextInput(hint_text="Название", multiline=False)
        self.target_input = TextInput(hint_text="Сумма", input_filter='float', multiline=False)
        
        content.add_widget(self.title_input)
        content.add_widget(self.target_input)
        
        btn_box = BoxLayout(spacing=10)
        btn_ok = Button(text="Создать")
        btn_cancel = Button(text="Отмена")
        btn_box.add_widget(btn_ok)
        btn_box.add_widget(btn_cancel)
        content.add_widget(btn_box)
        
        self.popup = Popup(title="Новая цель", content=content, size_hint=(0.8, 0.4))
        btn_ok.bind(on_release=self.save_goal)
        btn_cancel.bind(on_release=self.popup.dismiss)
        self.popup.open()

    def save_goal(self, instance):
        t = self.title_input.text
        try:
            amt = float(self.target_input.text)
            if not t or amt <= 0: return
            self.db.add_goal(t, amt)
            self.popup.dismiss()
            self.load_goals()
        except:
            pass

    def show_money_popup(self, goal_id, is_deposit):
        content = BoxLayout(orientation='vertical', spacing=10)
        self.money_input = TextInput(hint_text="Сумма", input_filter='float', multiline=False)
        content.add_widget(self.money_input)
        
        btn_box = BoxLayout(spacing=10)
        btn_ok = Button(text="ОК")
        btn_cancel = Button(text="Отмена")
        btn_box.add_widget(btn_ok)
        btn_box.add_widget(btn_cancel)
        content.add_widget(btn_box)
        
        self.money_popup = Popup(title="Пополнить" if is_deposit else "Снять", content=content, size_hint=(0.8, 0.3))
        btn_ok.bind(on_release=lambda x: self.do_money(goal_id, is_deposit))
        btn_cancel.bind(on_release=self.money_popup.dismiss)
        self.money_popup.open()

    def do_money(self, goal_id, is_deposit):
        try:
            amt = float(self.money_input.text)
            if amt <= 0: return
            self.db.add_money(goal_id, amt, is_deposit)
            self.money_popup.dismiss()
            self.load_goals()
        except:
            pass

if __name__ == "__main__":
    SaveUpApp().run()