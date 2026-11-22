from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
import sqlite3
import random
from datetime import datetime

DB_NAME = "saveup.db"

JOKES = {
    "deposit": [
        "Ого. Кажется, у тебя появился план",
        "Деньги на месте. Можете расходиться",
        "Пахнет богатством. Или это просто новый перевод",
        "Поздравляю, ты только что обманул маркетологов"
    ],
    "withdraw": [
        "Финансовый план попросил выйти из комнаты",
        "Твои деньги только что получили свободу передвижения",
        "Я ничего не видел. Камеры тоже",
        "Минус деньги. Надеюсь, хоть товар был с бонусами"
    ]
}

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                target REAL,
                current REAL DEFAULT 0,
                deadline TEXT
            )
        """)
        self.conn.commit()

    def get_goals(self):
        return self.cursor.execute("SELECT * FROM goals").fetchall()

    def add_goal(self, title, target, deadline):
        self.cursor.execute("INSERT INTO goals (title, target, deadline) VALUES (?, ?, ?)", (title, target, deadline))
        self.conn.commit()

    def add_money(self, goal_id, amount, is_deposit=True):
        if is_deposit:
            self.cursor.execute("UPDATE goals SET current = current + ? WHERE id = ?", (amount, goal_id))
        else:
            self.cursor.execute("UPDATE goals SET current = max(0, current - ?) WHERE id = ?", (amount, goal_id))
        self.conn.commit()

    def delete_goal(self, goal_id):
        self.cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        self.conn.commit()

class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = Database()
        
        self.layout = MDBoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Заголовок
        header = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(60))
        header.add_widget(MDLabel(text="[b]ОБЩИЙ БАЛАНС[/b]", markup=True, theme_text_color="Custom", text_color=get_color_from_hex("#A29BFE"), font_style="Caption"))
        self.balance_label = MDLabel(text="0 ₽", theme_text_color="Custom", text_color=(1,1,1,1), font_style="H4")
        header.add_widget(self.balance_label)
        self.layout.add_widget(header)
        
        # Список целей
        self.goals_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.goals_layout.bind(minimum_height=self.goals_layout.setter('height'))
        self.layout.add_widget(self.goals_layout)
        
        # Кнопка добавления
        self.fab = MDFloatingActionButton(
            icon="plus",
            md_bg_color=get_color_from_hex("#6C5CE7"),
            pos_hint={"center_x": 0.5, "y": 0.05},
            on_release=self.show_add_dialog
        )
        self.layout.add_widget(self.fab)
        
        self.add_widget(self.layout)
        self.load_goals()

    def show_snack(self, text, is_positive=True):
        color = "#00B894" if is_positive else "#FF7675"
        MDSnackbar(MDSnackbarText(text=text, theme_text_color="Custom", text_color=(1,1,1,1)), 
                   md_bg_color=get_color_from_hex(color), y=dp(100)).open()

    def load_goals(self):
        self.goals_layout.clear_widgets()
        goals = self.db.get_goals()
        
        total = sum(g[3] for g in goals)
        self.balance_label.text = f"{total:,.0f} ₽".replace(",", " ")

        if not goals:
            self.goals_layout.add_widget(MDLabel(
                text="Пока пусто. Нажми +",
                halign="center",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(50)
            ))
            return

        for g in goals:
            gid, title, target, current, deadline = g
            prog = min(current / target, 1.0) if target > 0 else 0
            
            card = MDCard(
                orientation='vertical',
                padding=dp(15),
                size_hint=(1, None),
                height=dp(140),
                md_bg_color=get_color_from_hex("#161922"),
                radius=[dp(15)],
            )
            
            top_row = MDBoxLayout(size_hint_y=None, height=dp(30))
            top_row.add_widget(MDLabel(text=f"[b]{title}[/b]", markup=True, theme_text_color="Custom", text_color=(1,1,1,1)))
            
            del_btn = MDIconButton(icon="delete", theme_icon_color="Custom", icon_color=get_color_from_hex("#FF7675"), on_release=lambda x, i=gid: self.confirm_delete(i))
            top_row.add_widget(del_btn)
            card.add_widget(top_row)
            
            card.add_widget(MDLabel(text=f"{current:.0f} ₽ / {target:.0f} ₽  ({int(prog*100)}%)", theme_text_color="Custom", text_color=get_color_from_hex("#A29BFE")))
            
            # Кнопки пополнения/снятия
            btns = MDBoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
            add_btn = MDFlatButton(text="+ Добавить", on_release=lambda x, i=gid: self.show_add_money(i, True))
            wit_btn = MDFlatButton(text="- Снять", on_release=lambda x, i=gid: self.show_add_money(i, False))
            btns.add_widget(add_btn)
            btns.add_widget(wit_btn)
            card.add_widget(btns)
            
            self.goals_layout.add_widget(card)
            
    def show_add_dialog(self, instance):
        self.title_input = MDTextField(hint_text="Название (например, Наушники)")
        self.target_input = MDTextField(hint_text="Сумма (₽)", input_filter="float")
        self.deadline_input = MDTextField(hint_text="Дедлайн (ГГГГ-ММ-ДД)", text=f"{datetime.now().year}-12-31")
        
        content = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(220))
        content.add_widget(self.title_input)
        content.add_widget(self.target_input)
        content.add_widget(self.deadline_input)
        
        self.dialog = MDDialog(
            title="Новая цель",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="СОЗДАТЬ", on_release=self.save_goal)
            ]
        )
        self.dialog.open()
        
    def save_goal(self, instance):
        t = self.title_input.text
        try:
            amt = float(self.target_input.text.replace(",", "."))
            d = self.deadline_input.text
        except:
            return
            
        if not t or amt <= 0:
            return
            
        self.db.add_goal(t, amt, d)
        self.dialog.dismiss()
        self.load_goals()
        self.show_snack("Цель добавлена! Погнали копить.")

    def show_add_money(self, goal_id, is_deposit):
        self.money_input = MDTextField(hint_text="Сумма (₽)", input_filter="float")
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        content.add_widget(self.money_input)
        
        self.money_dialog = MDDialog(
            title="Пополнить" if is_deposit else "Снять",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.money_dialog.dismiss()),
                MDFlatButton(text="ОК", on_release=lambda x: self.do_add_money(goal_id, is_deposit))
            ]
        )
        self.money_dialog.open()

    def do_add_money(self, goal_id, is_deposit):
        try:
            amt = float(self.money_input.text.replace(",", "."))
            if amt <= 0: return
            self.db.add_money(goal_id, amt, is_deposit)
            self.money_dialog.dismiss()
            self.load_goals()
            joke = random.choice(JOKES["deposit"] if is_deposit else JOKES["withdraw"])
            self.show_snack(joke, is_positive=is_deposit)
        except:
            pass

    def confirm_delete(self, goal_id):
        self.db.delete_goal(goal_id)
        self.load_goals()
        self.show_snack("Цель удалена. Минус одна хотелка.", is_positive=False)

class SaveUpApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.title = "SaveUp"
        return MainScreen()

if __name__ == "__main__":
    SaveUpApp().run()