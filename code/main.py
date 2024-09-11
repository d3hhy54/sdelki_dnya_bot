import asyncio
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import database, keyboard, payment, config
from datetime import datetime

bot = Bot(token=config.TOKEN_BOT, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
db = database.Database("/data/database.db")

class post_setting(StatesGroup):
	file = State()
	description = State()
	date = State()
	time = State()
	confirm_sending = State()
	additionally = State()
	
class interaction_posts(StatesGroup):
	action = State()
	action_post = State()
	
class tariff(StatesGroup):
	chosen_tariff = State()
	check_payment = State()
	
class support(StatesGroup):
	action = State()
	request = State()
	answer = State()

class giving_posts(StatesGroup):
	id = State()
	number_posts = State()

class mailing_setting(StatesGroup):
	message = State()
	confirm = State()

class checking_menu(StatesGroup):
	action = State()
	action_for_post = State()
	confirm_input_cause = State()
	cause = State()
	
	
@dp.message_handler(commands=["start"], state="*")
async def cmd_start_handler(message: Message, state: FSMContext) -> None:
	await state.finish()
	menu_message = await message.answer('Приветствую, это ваш <b>личный кабинет</b> 📂\n\nЧерез кнопки, <b>прикрепленные к этому сообщению</b> обращайтесь к функционалу бота 🛠\n\n<b>Выберите действие</b> ⚙', reply_markup=keyboard.main_menu())
	have_user = await db.have_user(message.from_user.id)
	if have_user:
		# await db.change_value_posts_user(message.from_user.id, 10)
		await db.change_value_menu_id_user(message.from_user.id, menu_message.message_id)
	else:
		await db.add_user(message.from_user.id, menu_message.message_id, posts=1)

@dp.message_handler(commands=['get_admin_menu'], state='*')
async def get_admin_menu(message: Message, state: FSMContext):
	if message.from_user.id == config.ADMIN_ID:
		await state.finish()
		await message.answer(
			text='Админская панель <b>выдана!</b>',
			reply_markup=keyboard.admin_menu()
		)
		return
	await message.delete()

@dp.callback_query_handler(text='checking_posts')
async def checking_posts(call: CallbackQuery, state: FSMContext):
	posts = await db.all_posts_check()
	if not posts:
		await call.answer('На данный момент постов на проверку нет!', show_alert=True)
		return
	await call.message.edit_text(
		'Посты:',
		reply_markup=keyboard.check_posts_menu(posts, 2)
	)
	await state.set_state(checking_menu.action)

@dp.callback_query_handler(text='delete_message', state='*')
async def delete_message(call: CallbackQuery):
	await call.message.delete()

@dp.callback_query_handler(state=checking_menu.action)
async def action_for_checking_menu(call: CallbackQuery, state: FSMContext):
	posts = await db.all_posts_check()
	if call.data.startswith('post_id'):
		await call.message.delete()
		id = int(call.data[8:])
		for post in posts:
			if post[0] == id:
				user_post = post
				break

		text = f"Это <b>предложение <a href=\"tg://user?id={user_post[1]}\">пользователя</a></b> 📃\n\nДополнительная информация ❗️\nДата публикации:<b>{user_post[5]}</b> 🗓\nВремя публикации: <b>{user_post[6]}</b> ⏰"
		if user_post[3] == 'photo':
			post = await bot.send_photo(
				chat_id=call.from_user.id,
				photo=user_post[2],
				caption=user_post[4]
			)
		elif user_post[3] == 'video':
			post = await bot.send_video(
				chat_id=call.from_user.id,
				video=user_post[2],
				caption=user_post[4]
			)
		await state.update_data(id=user_post[0])
		await state.update_data(message_id=post.message_id)
		await state.update_data(user_id=user_post[1])
		await call.message.answer(
			text,
			reply_markup=keyboard.action_for_post_menu()
		)
		await state.set_state(checking_menu.action_for_post)
	elif call.data.startswith('post_previous') or call.data.startswith('post_next'):
		count = int(call.data.split('_')[3])
		index = 6 * count
		if index < 0:
			await call.answer("Это первый слайд! Там ничего нет ❌")
			return
		if not posts[index:]:
			await call.answer("Предложения закончились 😢")
			return

		if call.data.startswith('post_previous'):
			change = 1
		else:
			change = 0

		await call.message.edit_text('Посты:', reply_markup=keyboard.check_posts_menu(posts[index:], change))

@dp.callback_query_handler(state=checking_menu.action_for_post)
async def action_for_post(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	await bot.delete_message(call.from_user.id, data.get('message_id'))
	if call.data == 'true':
		await db.change_status_post(data.get('id'), 'send')
		text = 'Заявка одобрена!'
		kb = keyboard.admin_menu()
		await bot.send_message(
			chat_id=data.get('user_id'),
			text='Ваше предложение было <b><u>принято администрацией!</u></b> ✅',
			reply_markup=keyboard.delete_message_menu()
		)
		await state.finish()
	elif call.data == 'false':
		await db.change_value_posts_user(data.get('user_id'), 1)
		await db.change_status_post(data.get('id'))
		text = 'Заявка была отменена!\n\nХотите ввести причину?'
		kb = keyboard.cause_menu()
		await state.set_state(checking_menu.confirm_input_cause)


	await call.message.edit_text(
		text=text,
		reply_markup=kb
	)


@dp.callback_query_handler(state=checking_menu.confirm_input_cause)
async def confirm_input_cause(call: CallbackQuery, state: FSMContext):
	if call.data == 'input_cause':
		await call.message.edit_text('Введите причину отмены публикации:')
		await state.set_state(checking_menu.cause)
	elif call.data == 'no_cause':
		data = await state.get_data()
		text = 'Ваше предложение было <b><u>отменено администрацией!</u></b> ❌\n\nПричина: <i>Не указана</i> 🤔'
		await bot.send_message(
			chat_id=data.get('user_id'),
			text=text,
			reply_markup=keyboard.delete_message_menu()
		)
		await call.message.edit_text(
			'Уведомление было отправлено пользователю!\n\nАдминская панель <b>выдана!</b>',
			reply_markup=keyboard.admin_menu()
		)

@dp.message_handler(state=checking_menu.cause)
async def cause_chosen(message: Message, state: FSMContext):
	data = await state.get_data()
	text = f'Ваше предложение было <b><u>отменено администрацией!</u></b> ❌\n\nПричина: <i>{message.text}</i> 🤔'
	await bot.send_message(
		chat_id=data.get('user_id'),
		text=text,
		reply_markup=keyboard.delete_message_menu()
	)
	await message.answer(
		'Уведомление было отправлено пользователю!\n\nАдминская панель <b>выдана!</b>',
		reply_markup=keyboard.admin_menu()
	)
	await state.finish()

@dp.callback_query_handler(text='give_posts')
async def give_posts(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text(
		'Введите ID пользователя:',
		reply_markup=keyboard.return_admin_menu()
	)
	await state.set_state(giving_posts.id)

@dp.message_handler(state=giving_posts.id)
async def id_chosen(message: Message, state: FSMContext):
	if message.text.isdigit():
		await state.update_data(id=int(message.text))
		await message.answer(
			'Введите количество постов для выдачи:',
			reply_markup=keyboard.return_admin_menu()
		)
		await state.set_state(giving_posts.number_posts)
	else:
		await message.answer('Введите только число!', reply_markup=keyboard.return_admin_menu())


@dp.message_handler(state=giving_posts.number_posts)
async def number_posts_chosen(message: Message, state: FSMContext):
	if message.text.isdigit():
		await state.update_data(posts=int(message.text))
		data = await state.get_data()
		user = await db.info_user(data.get('id'))
		await state.finish()
		if user:
			await db.change_value_posts_user(data.get('id'), data.get('posts'))
			await message.answer('Посты успешно добавлены')
		else:
			await message.answer('Пользователь не найден')
		await message.answer(
			text='Админская панель <b>выдана!</b>',
			reply_markup=keyboard.admin_menu()
		)
	else:
		await message.answer('Введите только число!', reply_markup=keyboard.return_admin_menu())

@dp.callback_query_handler(text='cancel', state='*')
async def cancel_for_admin(call: CallbackQuery, state: FSMContext):
	await state.finish()
	await call.message.edit_text(
		text='Админская панель <b>выдана!</b>',
		reply_markup=keyboard.admin_menu()
	)

@dp.callback_query_handler(text='mailing', state='*')
async def mailing(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text(
		'Введите сообщение для рассылки, оно может содержать фото или видео, или просто текст:',
		reply_markup=keyboard.return_admin_menu()
	)
	await state.set_state(mailing_setting.message)

@dp.message_handler(state=mailing_setting.message, content_types=['any'])
async def message_chosen(message: Message, state: FSMContext):
	if message.content_type in [types.ContentType.TEXT, types.ContentType.PHOTO, types.ContentType.VIDEO]:
		file = None
		type = 'text'
		if message.photo:
			file = message.photo[-1].file_id
			type = 'photo'
		elif message.video:
			file = message.video.file_id
			type = 'video'
		caption = message.html_text
		await state.update_data(file=file, type=type, caption=caption)
		await message.answer('Вы уверены что хотите начать рассылку?', reply_markup=keyboard.confirm_mailing_menu())
		await state.set_state(mailing_setting.confirm)
	else:
		await message.answer('Пост должен содержать только фото, видео или текст!', reply_markup=keyboard.return_admin_menu())

@dp.callback_query_handler(state=mailing_setting.confirm)
async def confirm_mailing(call: CallbackQuery, state: FSMContext):
	if call.data == 'confirm_mailing':
		data = await state.get_data()
		await call.message.edit_text('Рассылка началась!')
		async for user in db.id_all_users():
			try:
				if data.get('type') == 'photo':
					await bot.send_photo(
						chat_id=user,
						photo=data.get('file'),
						caption=data.get('caption')
					)
				elif data.get('type') == 'video':
					await bot.send_video(
						chat_id=user,
						video=data.get('file'),
						caption=data.get('caption')
					)
				elif data.get('type') == 'text':
					await bot.send_message(
						chat_id=user,
						text=data.get('caption')
					)
			except:
				pass
		await state.finish()
	else:
		await call.message.edit_text('Рассылка отменена')


@dp.callback_query_handler(text="get_main_menu", state="*")
async def main_menu(call: CallbackQuery, state: FSMContext) -> None:
	await state.finish()
	await call.answer()
	await call.message.edit_text('Приветствую, это ваш <b>личный кабинет</b> 📂\n\nЧерез кнопки, <b>прикрепленные к этому сообщению</b> обращайтесь к функционалу бота 🛠\n\n<b>Выберите действие</b> ⚙', reply_markup=keyboard.main_menu())
	
@dp.callback_query_handler(text="posts_user")
async def posts_user_handler(call: CallbackQuery, state: FSMContext):
	posts_user = await db.all_posts_user(call.from_user.id)
	if posts_user:
		await call.message.edit_text('Это ваши <b>предложения</b> 📄\n\nСтатусы предложений:\n📩 - Предложение <b>готовиться к отправке</b>\n❌ - Публикация <b>отменена</b>\n✅ - Предложение <b>успешно отправлено</b>\n🕵‍♂️ - Предложение находится <b>в проверке</b>\n\nИщите интересующее вас предложение с помощью <b>меню к сообщению</b> 🗒', reply_markup=keyboard.posts_user_menu(posts_user, 2))
		await state.set_state(interaction_posts.action)
	else:
		await call.answer('У вас нет предложений❌ Что бы создать его нажмите на "Создать предложение 📨"', show_alert=True)
		
@dp.callback_query_handler(text="support")
async def support_handler(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text("Как пользоваться ❓\n\n<b><u>Как опубликовать объявление?</u></b>\nДля того, чтобы создать публикацию, зайдите в бота, введите команду /start , дальше появится интерактивное меню у приветственного сообщения. Зайдите в \"Оплатить тариф 🏦\", выберите количество предложений, которые хотите купить. Оплатите счёт, и приступайте к настройке вашего предложения. \n\n❗️ Важно: \n1) Бот видит только 1 фотографию/видео. \n2) Воспользуйтесь при необходимости кнопкой «Отредактировать» перед сохранением предложения. После того, как Вы нажали кнопку «Сохранить» в случае обнаружения ошибки пост  можно удалить через \"Мои предложения 📑\". \n3) Бот автоматически удаляет сообщения, но он их сохраняет! Поэтому не переживайте, бот вас понимает.\n\n❗️ Обращайтесь в поддержку только по важным вопросам ❗️", reply_markup=keyboard.support_menu())
	await state.set_state(support.action)
	
@dp.callback_query_handler(state=support.action)
async def support_action(call: CallbackQuery, state: FSMContext):
	await call.message.edit_text("Введите <b>ваш вопрос</b> 🧐", reply_markup=keyboard.back_menu())
	await state.set_state(support.request)
	
@dp.message_handler(content_types=["any"], state=support.request)
async def request_for_support(message: Message, state: FSMContext):
	user = await db.info_user(message.from_user.id)
	message_request = message
	await message.delete()
	if message_request.content_type == types.ContentType.TEXT:
		await message.bot.edit_message_text(chat_id=message.from_user.id, message_id=user[3], text="Вопрос был успешно отправлен поддерже! Ожидайте ответа в боте в течении <b>следующих 24 часов</b> ⌛️", reply_markup=keyboard.back_menu())
		await message.bot.send_message(chat_id=config.ADMIN_ID, text=f"Новый вопрос!\n\n{message_request.from_user.first_name}, ID: <code>{message_request.from_user.id}</code>: {message_request.text}", reply_markup=keyboard.supported_menu(message.from_user.id))
		
@dp.callback_query_handler(lambda call: call.data.startswith('answer_') and call.from_user.id == config.ADMIN_ID, state="*")
async def answer_for_request(call: CallbackQuery, state: FSMContext):
	await state.update_data(id=call.message.message_id)
	await state.update_data(user_id=call.data.split('_')[1])
	text = call.message.text.split('\n\n')[1]
	await call.message.edit_text(f"Ответьте на <b>данный вопрос ❓\n\n</b>{text}")
	await state.set_state(support.answer)
	
@dp.message_handler(state=support.answer)
async def sending_answer(message: Message, state: FSMContext):
	data = await state.get_data()
	await state.finish()
	await message.delete()
	await message.bot.edit_message_text(chat_id=message.from_user.id, message_id=data.get('id'), text="Ответ был <b>успешно отправлен</b> пользователю!")
	await message.bot.send_message(chat_id=data.get('user_id'), text=f"Ответ на <b>ваш вопрос</b> 🧐\n\n<b>Администрация:</b> <i>\"{message.text}\"</i>", reply_markup=keyboard.delete_message_menu())
	
@dp.callback_query_handler(text="payment_tariff")
async def payment_tariff_handler(call: CallbackQuery, state: FSMContext):
	await call.answer('Данная функция сейчас закрыта. Попросите выдать публикации в отделе "Как пользоваться ❓" -> "Поддержка 👩‍💻"', show_alert=True)
	#await call.message.edit_text("Выберите интересующий вас <b>тариф</b> 💳", reply_markup=keyboard.tariffs_menu())
	#await state.set_state(tariff.chosen_tariff)
	
@dp.callback_query_handler(state=tariff.chosen_tariff)
async def chosen_tariff_handler(call: CallbackQuery, state: FSMContext):
	info = call.data.split('_')
	price = int(info[1][8:])
	await state.update_data(info=info)
	await call.message.edit_text(f"Сумма оплаты <b>{price}₽💸\n\n</b>Нажмите на кнопку  <b>\"Оплатить ✅\"</b>, и оплатите счет. А после, нажмите на кнопку <b>\"Проверить ☑️\"</b> для проверки оплаты.\n\n❗️ Время за которое нужно выполнить оплату <b>10 минут</b> ❗️", reply_markup=keyboard.payment_menu(
		payment.create(price, call.from_user.id)))
	await state.set_state(tariff.check_payment)
	
@dp.callback_query_handler(state=tariff.check_payment)
async def check_payment_handler(call: CallbackQuery, state: FSMContext):
	await call.answer()
	data = await state.get_data()
	if call.data.startswith("check_"):
		payment_id = call.data[6:]
		info = data.get('info')
		price = int(info[1][8:])
		check_payment = payment.check(payment_id)
		if check_payment:
			await call.message.edit_text(f"Вы <b>успешно оплатили</b> счет ❗️\n\nВы получили <b>{info[0][5:]}</b> 📄\n\nВозвращайтесь в <b>личный кабинет</b> 🏠", reply_markup=keyboard.back_menu())
			await db.change_value_posts_user(check_payment.get('chat_id'), int(info[0][5:]))
			print(f"True payment {check_payment.get('chat_id')}")
		else:
			await call.message.edit_text(f"Вы <b>не оплатили</b> счет 😢\n\nСумма оплаты <b>{price}₽💸\n\n</b>Нажмите на кнопку  <b>\"Оплатить ✅\"</b>, и оплатите счет. А после, нажмите на кнопку <b>\"Проверить ☑️\"</b> для проверки оплаты.\n\n❗️ Время за которое нужно выполнить оплату <b>10 минут</b> ❗️", reply_markup=keyboard.payment_menu(
				payment.create(price, call.from_user.id)))

@dp.callback_query_handler(state=interaction_posts.action)
async def action_menu_posts(call: CallbackQuery, state: FSMContext) -> None:
	posts_user = await db.all_posts_user(call.from_user.id)
	if call.data.startswith('post_id'):
		id = int(call.data[8:])
		for post in posts_user:
			if post[0] == id:
				post_user = post
				break
		
		text = f"Это <b>твое предложение</b>📃\n\nДополнительная информация ❗️\nДата публикации:<b>{post_user[5]}</b> 🗓\nВремя публикации: <b>{post_user[6]}</b> ⏰"
		kb = keyboard.action_post_menu(post_user[7])
		if post_user[7] == "send":
			text += "\n\nЧто делаем с предложением ❓"
		await call.message.delete()	
		if post_user[3] == 'photo':
			post_message = await bot.send_photo(chat_id=call.from_user.id, photo=post_user[2], caption=post_user[4])
		else:
			post_message = await bot.send_video(chat_id=call.from_user.id, video=post_user[2], caption=post_user[4])
		menu = await call.message.answer(text, reply_markup=kb)
		await state.update_data(message_id=post_message.message_id)
		await state.update_data(id=id)
		await state.set_state(interaction_posts.action_post)
		await db.change_value_menu_id_user(call.from_user.id, menu.message_id)
	elif call.data.startswith('post_next') or call.data.startswith('post_previous'):
		count = int(call.data.split('_')[3])
		index = 6*count
		if index < 0:
			await call.answer("Это первый слайд! Там ничего нет ❌")
			return
		if not posts_user[index:]:
			await call.answer("Предложения закончились 😢")
			return
		
		if call.data.startswith('post_previous'):
			change = 1
		else:
			change = 0
		await call.message.edit_text('Это ваши <b>предложения</b> 📄\n\nСтатусы предложений:\n📩 - Предложение <b>готовиться к отправке</b>\n❌ - Публикация <b>отменена</b>\n✅ - Предложение <b>успешно отправлено</b>\n🕵‍♂️ - Предложение находится <b>в проверке</b>\n\nИщите интересующее вас предложение с помощью <b>меню к сообщению</b> 🗒', reply_markup=keyboard.posts_user_menu(posts_user[index:], change))
		
@dp.callback_query_handler(state=interaction_posts.action_post)
async def action_post_handler(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	await bot.delete_message(chat_id=call.from_user.id, message_id=int(data.get('message_id')))
	id = data.get('id')
	await state.finish()
	if call.data.startswith("cancelled"):
		await db.change_status_post(id)
		await db.change_value_posts_user(call.from_user.id, 1)
		await call.message.edit_text('Публикация успешно <b>отменена</b>\n\nВозвращайтесь в кабинет 🏠', reply_markup=keyboard.back_menu())
	else:
		await call.message.edit_text('Приветствую, это ваш <b>личный кабинет</b> 📂\n\nЧерез кнопки, <b>прикрепленные к этому сообщению</b> обращайтесь к функционалу бота 🛠\n\n<b>Выберите действие</b> ⚙', reply_markup=keyboard.main_menu())
		
@dp.callback_query_handler(text="new_post")
async def new_post_handler(call: CallbackQuery,state: FSMContext) -> None:
	user = await db.info_user(call.from_user.id)
	if user[2] == 0:
		await call.answer('У вас нет возможности разместить предложения! ❌ Что бы выложить предложение, ознакомьтесь с кнопкой "Оплатить тариф 🏦"', show_alert=True)
	else:
		await call.message.edit_text(f"Количество предложений на данный момент <b>{user[2]}</b> 📂\n\nПришлите <b>фотографию</b> или <b>видео</b> вашего товара 👜", reply_markup=keyboard.back_menu())
		await state.set_state(post_setting.file)
		
@dp.message_handler(content_types=["any"], state=post_setting.file)
async def file_for_post_chosen(message: Message, state: FSMContext) -> None:
	user = await db.info_user(message.from_user.id)
	data = await state.get_data()
	if message.content_type in ["photo", "video"]:
		if message.photo:
			file_id = message.photo[-1].file_id
			type = "photo"
		else:
			file_id = message.video.file_id
			type = "video"
		
		await state.update_data(file_id=file_id)
		await state.update_data(type=type)
		await message.delete()
		if data.get('post_id'):
			if data.get('type') == "photo":
				post = await bot.send_photo(chat_id=message.from_user.id, photo=file_id, caption=data.get('description'))
			else:
				post = await bot.send_video(chat_id=message.from_user.id, video=file_id, caption=data.get('description'))
			await state.update_data(post_id=post.message_id)
			await message.bot.delete_message(chat_id=message.from_user.id, message_id=user[3])
			menu_message = await message.answer(f"Сверху находится <b>твой пост</b> 📋 \n\nДополнительная информация ❗️\nДата публикации:<b>{data.get('date')}</b> 🗓\nВремя публикации: <b>{data.get('time_post')}</b> ⏰\n\nЧто делаем <b>с предложением</b> ❓", reply_markup=keyboard.confirm_sending_and_past_menu("Редактировать ⚙"))
			await db.change_value_menu_id_user(message.from_user.id, menu_message.message_id)
			await state.set_state(post_setting.confirm_sending)
			return
		await message.bot.edit_message_text(chat_id=message.from_user.id, message_id=user[3], text="Отлично, первый шаг <b>позади</b> 📷\n\nТеперь введи <b>описание товара</b>, не забывай о том, что можно сделать <b>жирный текст</b>, <i>под наклоном</i> и так далее 😮‍💨", reply_markup=keyboard.back_and_past_menu("Вернуться к фото/видео 📸"))
		await state.set_state(post_setting.description)
	else:
		await message.delete()
		await message.bot.edit_message_text(chat_id=message.from_user.id, message_id=user[3], text="Похоже, вы <b>не поняли</b> 😢\n\nЭто <b>не то</b>, что мне нужно. Отправьте <b>фотографию</b> или <b>видео</b> вашего товара 👜", reply_markup=keyboard.back_menu())
		
@dp.callback_query_handler(state=post_setting.description)
async def past_step_file_handler(call: CallbackQuery, state: FSMContext):
	user = await db.info_user(call.from_user.id)
	if call.data == "past_step":
		await call.message.edit_text(f"Количество предложений на данный момент <b>{user[2]}</b> 📂\n\nПришлите <b>фотографию</b> или <b>видео</b> вашего товара 👜", reply_markup=keyboard.back_menu())
		await state.set_state(post_setting.file)
		
@dp.message_handler(state=post_setting.description)
async def description_chosen(message: Message, state: FSMContext) -> None:
	user = await db.info_user(message.from_user.id)
	text = message.html_text
	await state.update_data(description=text)
	data = await state.get_data()
	await message.delete()
	if data.get('post_id'):
		if data.get('type') == "photo":
			post = await bot.send_photo(chat_id=message.from_user.id, photo=data.get('file_id'), caption=data.get('description'))
		else:
			post = await bot.send_video(chat_id=message.from_user.id, video=data.get('file_id'), caption=data.get('description'))
		await state.update_data(post_id=post.message_id)
		await message.bot.delete_message(chat_id=message.from_user.id, message_id=user[3])
		menu_message = await message.answer(f"Сверху находится <b>твой пост</b> 📋 \n\nДополнительная информация ❗️\nДата публикации:<b>{data.get('date')}</b> 🗓\nВремя публикации: <b>{data.get('time_post')}</b> ⏰\n\nЧто делаем <b>с предложением</b> ❓", reply_markup=keyboard.confirm_sending_and_past_menu("Редактировать ⚙"))
		await db.change_value_menu_id_user(message.from_user.id, menu_message.message_id)
		await state.set_state(post_setting.confirm_sending)
		return
	await message.bot.edit_message_text(chat_id=message.from_user.id, message_id=user[3], text="Окей, выберите <b>дату публикации предложения</b> 🗓", reply_markup=keyboard.calendar_and_past_menu("Вернуться к описанию 📝"))
	await state.set_state(post_setting.date)
	
@dp.callback_query_handler(state=post_setting.date)
async def date_chosen(call: CallbackQuery, state: FSMContext) -> None:
	user = await db.info_user(call.from_user.id)
	if call.data == "past_step":
		await call.message.bot.edit_message_text(chat_id=call.from_user.id, message_id=user[3], text="Отлично, первый шаг <b>позади</b> 📷\n\nТеперь введи <b>описание товара</b>, не забывай о том, что можно сделать <b>жирный текст</b>, <i>под наклоном</i> и так далее 😮‍💨", reply_markup=keyboard.back_and_past_menu("Вернуться к фото/видео 📸"))
		await state.set_state(post_setting.description)
		return
	date = call.data.split('_')[1]
	await state.update_data(date=date)
	data = await state.get_data()
	if data.get('post_id'):
		file_id = data.get('file_id')
		if data.get('type') == "photo":
			post = await bot.send_photo(chat_id=call.from_user.id, photo=file_id, caption=data.get('description'))
		else:
			post = await bot.send_video(chat_id=call.from_user.id, video=file_id, caption=data.get('description'))
		await state.update_data(post_id=post.message_id)
		await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=user[3])
		menu_message = await call.message.answer(f"Сверху находится <b>твой пост</b> 📋 \n\nДополнительная информация ❗️\nДата публикации:<b>{data.get('date')}</b> 🗓\nВремя публикации: <b>{data.get('time_post')}</b> ⏰\n\nЧто делаем <b>с предложением</b> ❓", reply_markup=keyboard.confirm_sending_and_past_menu("Редактировать ⚙"))
		await db.change_value_menu_id_user(call.from_user.id, menu_message.message_id)
		await state.set_state(post_setting.confirm_sending)
		return
	await call.message.bot.edit_message_text(chat_id=call.from_user.id, message_id=user[3], text="Я понял, теперь введите <b>время публикации предложения</b> ⏰\n\nВажно! <b>Требуется некое время для подверждения публикации поста.</b>", reply_markup=keyboard.back_and_past_menu("Вернуться к дате 🗓"))
	await state.set_state(post_setting.time)
	
@dp.callback_query_handler(state=post_setting.time)
async def past_step_calendar_handler(call: CallbackQuery, state: FSMContext):
	if call.data == "past_step":
		await call.message.edit_text("Окей, выберите <b>дату публикации предложения</b> 🗓", reply_markup=keyboard.calendar_and_past_menu("Вернуться к описанию 📝"))
		await state.set_state(post_setting.date)
	
@dp.message_handler(state=post_setting.time)
async def time_chosen(message: Message, state: FSMContext) -> None:
	user = await db.info_user(message.from_user.id)
	time_is_message = message.text.strip()
	await message.delete()
	try:
		time_post = datetime.strptime(time_is_message, "%H:%M").time()
		
		info = await state.get_data()
		if not time_no_past(info.get('date'), time_is_message):
			await message.bot.edit_message_text(chat_id=message.from_user.id, message_id=user[3], text="Нельзя заготавливать предложения <b>в прошлом!</b>\n\nЕще раз введите <b>время публикации предложения</b> ⏰", reply_markup=keyboard.back_and_past_menu("Вернуться к дате 🗓"))
			return
		await state.update_data(time_post=time_is_message)
		await message.bot.delete_message(chat_id=message.from_user.id, message_id=user[3])
		if info.get('type') == "photo":
			post = await message.bot.send_photo(chat_id=message.from_user.id, photo=info.get('file_id'), caption=info.get('description'))
		elif info.get('type') == "video":
			post = await message.bot.send_video(chat_id=message.from_user.id, video=info.get('file_id'), caption=info.get('description'))
		await state.update_data(post_id=post.message_id)
		menu_message = await message.answer(f"Сверху находится <b>твой пост</b> 📋 \n\nДополнительная информация ❗️\nДата публикации:<b>{info.get('date')}</b> 🗓\nВремя публикации: <b>{time_is_message}</b> ⏰\n\nЧто делаем <b>с предложением</b> ❓", reply_markup=keyboard.confirm_sending_and_past_menu("Редактировать ⚙"))
		await state.set_state(post_setting.confirm_sending)
		await db.change_value_menu_id_user(message.from_user.id, menu_message.message_id)
		return
	except ValueError:
		await message.bot.edit_message_text(chat_id=message.from_user.id, message_id=user[3], text="Вы не правильно ввели время! <b>Формат ввода: ЧЧ:ММ</b>\nЕще раз введите <b>время публикации предложения</b> ⏰", reply_markup=keyboard.back_and_past_menu("Вернуться к дате 🗓"))
		return

@dp.callback_query_handler(state=post_setting.confirm_sending)
async def confirm_sending_handler(call: CallbackQuery, state: FSMContext):
	data = await state.get_data()
	user = await db.info_user(call.from_user.id)
	if call.data == "past_step":
		await call.message.edit_text("Выберите то <b>что хотите изменить</b> 📌", reply_markup=keyboard.dops_menu())
		await state.set_state(post_setting.additionally)
	if call.data.endswith('true'):
		file_id = data.get('file_id')
		type = data.get('type')
		description = data.get('description')
		date = data.get('date')
		time_post = data.get('time_post')
		await db.add_post(call.from_user.id, file_id, type, description, date, time_post)
		await db.change_value_posts_user(call.from_user.id, -1)
		await call.answer()
		await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=data.get('post_id'))
		await call.message.bot.edit_message_text(chat_id=call.from_user.id, message_id=user[3], text="Предложение <b>успешно создано</b>📝\n\nОтправляйтесь в <b>личный кабинет</b> 🏠", reply_markup=keyboard.back_menu())
		await state.finish()
		await bot.send_message(
			chat_id=config.ADMIN_ID,
			text='Новое предложение! Проверьте его через админскую панель.',
			reply_markup=keyboard.delete_message_menu()
		)
	elif call.data.endswith('delete_post'):
		data = await state.get_data()
		await call.answer()
		await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=data.get('post_id'))
		await state.finish()
		await call.message.edit_text('Приветствую, это ваш <b>личный кабинет</b> 📂\n\nЧерез кнопки, <b>прикрепленные к этому сообщению</b> обращайтесь к функционалу бота 🛠\n\n<b>Выберите действие</b> ⚙', reply_markup=keyboard.main_menu())
		
@dp.callback_query_handler(state=post_setting.additionally)
async def additionally_handler(call: CallbackQuery, state: FSMContext):
	info = await state.get_data()
	user = await db.info_user(call.from_user.id)
	if call.data == "back":
		await call.message.edit_text(f"Сверху находится <b>твой пост</b> 📋 \n\nДополнительная информация ❗️\nДата публикации:<b>{info.get('date')}</b> 🗓\nВремя публикации: <b>{info.get('time_post')}</b> ⏰\n\nЧто делаем <b>с предложением</b> ❓", reply_markup=keyboard.confirm_sending_and_past_menu("Редактировать ⚙"))
		await state.set_state(post_setting.confirm_sending)
	else:
		await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=info.get('post_id'))
		if call.data.endswith('file'):
			await call.message.edit_text(f"Количество предложений на данный момент <b>{user[2]}</b> 📂\n\nПришлите <b>фотографию</b> или <b>видео</b> вашего товара 👜", reply_markup=keyboard.back_menu())
			await state.set_state(post_setting.file)
		elif call.data.endswith('text'):
			await call.message.edit_text("Отлично, первый шаг <b>позади</b> 📷\n\nТеперь введи <b>описание товара</b>, не забывай о том, что можно сделать <b>жирный текст</b>, <i>под наклоном</i> и так далее 😮‍💨", reply_markup=keyboard.back_and_past_menu("Вернуться к фото/видео 📸"))
			await state.set_state(post_setting.description)
		elif call.data.endswith('date'):
			await call.message.edit_text("Окей, выберите <b>дату публикации предложения</b> 🗓", reply_markup=keyboard.calendar_and_past_menu("Вернуться к описанию 📝"))
			await state.set_state(post_setting.date)
		elif call.data.endswith('time'):
			await call.message.edit_text("Я понял, теперь введите <b>время публикации предложения</b> ⏰", reply_markup=keyboard.back_and_past_menu("Вернуться к дате 🗓"))
			await state.set_state(post_setting.time)
		
		
def time_no_past(date_str, time_str):
	date_obj = datetime.strptime(str(datetime.now().year) + date_str, "%Y%d.%m").date()
	time_obj = datetime.strptime(time_str, "%H:%M").time()
	past_datetime = datetime.combine(date_obj, time_obj)
	return past_datetime > datetime.now()
	
async def check_posts() -> None:
	while True:
		posts = await db.all_posts_sending()
		date_str = datetime.now().strftime("%d.%m")
		time_str = datetime.now().strftime("%H:%M")
		
		for post in posts:
			await sending_post(post)
		await asyncio.sleep(60)
		
async def sending_post(post: tuple):
	if post[3] == 'photo':
		await bot.send_photo(chat_id=config.USERNAME_CHANNEL, photo=post[2], caption=post[4])
	else:
		await bot.send_video(chat_id=config.USERNAME_CHANNEL, video=post[2], caption=post[4])
	await db.change_status_post(post[0], "successfully")
	
def main() -> None:
	print(datetime.now().strftime("%H:%M"))
	executor.start_polling(dp, skip_updates=True)
	
if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.create_task(db.create_table_users())
	loop.create_task(db.create_table_posts())
	loop.create_task(check_posts())
	main()