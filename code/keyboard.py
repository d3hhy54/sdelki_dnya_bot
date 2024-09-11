from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

count = -1
admin_count = -1

def main_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text="Создать предложение 📨", callback_data="new_post"), InlineKeyboardButton(text="Мои предложения 📑", callback_data="posts_user"), InlineKeyboardButton(text="Оплатить тариф 🏦", callback_data="payment_tariff"), InlineKeyboardButton(text="Как пользоваться ❓", callback_data="support"))
	
def back_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup().add(InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def calendar_menu() -> InlineKeyboardMarkup:
	buttons = []
	for i in range(7):
		date = datetime.now() + timedelta(days=i)
		button_text = date.strftime("%d.%m")
		buttons.append(InlineKeyboardButton(text=button_text, callback_data=f"date_{button_text}"))
	return InlineKeyboardMarkup(row_width=4).add(*buttons).add(InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def confirm_sending_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text="Сохранить ✅", callback_data="sending_true"), InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu_delete_post"))
	
def posts_user_menu(users_post: list, change=0) -> InlineKeyboardMarkup:
	global count
	if change == 0:
		count += 1
	elif change == 1:
		count -= 1
	else:
		count = 0
		
	if count < 0:
		count = 0
		
	buttons_post = []
	smailes = {"send": "📩", "cancelled": "❌", "successfully": "✅", "check": "🕵‍♂️"}
	for index, post in enumerate(users_post):
		buttons_post.append(InlineKeyboardButton(text=f"\"{post[4][:10]}...\" {smailes.get(f'{post[7]}')}", callback_data=f"post_id={post[0]}"))
		if len(buttons_post) == 6:
			break
			
	if not buttons_post:
		count -= 1
		
	return InlineKeyboardMarkup(row_width=2).add(*buttons_post).add(InlineKeyboardButton(text='⬅️️', callback_data=f"post_previous_slide_{count-1}"), InlineKeyboardButton(text='➡️', callback_data=f'post_next_slide_{count+1}')).add(InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def action_post_menu(status: str) -> InlineKeyboardMarkup():
	if status == "send" or status == 'check':
		return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text='Отменить публикацию ❌', callback_data='cancelled_post'), InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu_delete_post"))
	else:
		return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu_delete_post"))
		

def back_and_past_menu(text: str) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text=text, callback_data="past_step"), InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def calendar_and_past_menu(text: str) -> InlineKeyboardMarkup:
	buttons = []
	for i in range(7):
		date = datetime.now() + timedelta(days=i)
		button_text = date.strftime("%d.%m")
		buttons.append(InlineKeyboardButton(text=button_text, callback_data=f"date_{button_text}"))
	return InlineKeyboardMarkup(row_width=4).add(InlineKeyboardButton(text=text, callback_data="past_step")).add(*buttons).add(InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def confirm_sending_and_past_menu(text: str) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text=text, callback_data="past_step")).add(InlineKeyboardButton(text="Сохранить ✅", callback_data="sending_true"), InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu_delete_post"))
	
def tariffs_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text="1 Предложение 🧾 100₽", callback_data="post=1_payment=100")).add(InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def payment_menu(payment: tuple) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton(text="Оплатить ✅", url=f"{payment[0]}"), InlineKeyboardButton(text="Проверить ☑️", callback_data=f"check_{payment[1]}")).add(InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def dops_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text="Вернуться к фото/видео 📸", callback_data="past_step_file"), InlineKeyboardButton(text="Вернуться к описанию 📝", callback_data="past_step_text"), InlineKeyboardButton(text="Вернуться к дате 🗓", callback_data="past_step_date"), InlineKeyboardButton(text="Вернуться ко времени ⏰", callback_data="past_step_time")).add(InlineKeyboardButton(text="Обратно ↩️", callback_data="back"))
	
def support_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text='Поддержка 👩‍💻', callback_data="support_request"), InlineKeyboardButton(text="Вернуться в кабинет 🏠", callback_data="get_main_menu"))
	
def supported_menu(user_id: int) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup().add(InlineKeyboardButton(text="Ответить ✅", callback_data=f"answer_{user_id}"))

def admin_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text='Выдать посты', callback_data='give_posts'), InlineKeyboardButton(text='Рассылка', callback_data='mailing'), InlineKeyboardButton(text='Посты на проверку', callback_data='checking_posts'))

def return_admin_menu(text: str = 'Отмена') -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup().add(InlineKeyboardButton(text=text, callback_data='cancel'))

def confirm_mailing_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup().add(InlineKeyboardButton(text='Подтверждаю', callback_data='confirm_mailing'), InlineKeyboardButton(text='Отменить', callback_data='cancelled_mailing'))

def check_posts_menu(posts: list, change: int = 0) -> InlineKeyboardMarkup:
	global admin_count
	if change == 0:
		admin_count += 1
	elif change == 1:
		admin_count -= 1
	else:
		admin_count = 0

	if admin_count < 0:
		admin_count = 0

	buttons_post = []
	for index, post in enumerate(posts):
		buttons_post.append(InlineKeyboardButton(text=f"\"{post[4][:10]}...\"", callback_data=f"post_id={post[0]}"))
		if len(buttons_post) == 6:
			break

	if not buttons_post:
		admin_count -= 1

	return InlineKeyboardMarkup(row_width=2).add(*buttons_post).add(
		InlineKeyboardButton(text='⬅️️', callback_data=f"post_previous_slide_{admin_count - 1}"),
		InlineKeyboardButton(text='➡️', callback_data=f'post_next_slide_{admin_count + 1}')).add(
		InlineKeyboardButton(text='Отмена', callback_data='cancel'))

def action_for_post_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text='Разрешить публикацию', callback_data='true'), InlineKeyboardButton(text='Отменить публикацию', callback_data='false'))

def cause_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text='Ввести причину', callback_data='input_cause'), InlineKeyboardButton(text='Без причины', callback_data='no_cause'))

def delete_message_menu() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup().add(InlineKeyboardButton('Удалить сообщение ❌', callback_data='delete_message'))