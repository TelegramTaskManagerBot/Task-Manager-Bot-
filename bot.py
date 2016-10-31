from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, Job, ConversationHandler, RegexHandler, MessageHandler, Filters

import logging
import datetime

# our files
import config 
from classes import *



# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

CHOOSING, GETTING_DATE_AND_TIME, GETTING_TASK_TEXT, GETTING_TARGET = range(4)

reply_keyboard = [['Task', 'Target'], ['Cancel']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

users = dict()
# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hi! Use /help to get help')


def help(bot, update):
    update.message.reply_text('---Help---\n /add - to add new Task or \n ')


def alarm(bot, job):
    bot.sendMessage(job.context[0], text=job.context[2] + ", remind you about your task:\n" + job.context[1])


def add(bot, update):
    update.message.reply_text(
        "What do you want to add?",
        reply_markup=markup)

    return CHOOSING


def add_task(bot, update):
    update.message.reply_text(
        "Write date and time of Task in form DD.MM.YY HH:MM\n"
        "for example 12.12.16 4:20")

    return GETTING_DATE_AND_TIME    


def get_date_and_time(bot, update, user_data):
    task = Task()
    print('\n'+update.message.text+'\n')
    print(type(update.message.text))
    try:
        task.set_date_and_time(update.message.text)
    except NameError:
        update.message.reply_text(
            "You made a mistake, please try again\n\n"
            "Write date and time of Task in form DD.MM.YY HH:MM\n"
            "for example 12.12.16 4:20")
        del(task)
        return GETTING_DATE_AND_TIME
    if (task.datetime - datetime.datetime.now()).days < 0:
         update.message.reply_text(
         'Sorry we can not go back to future!\n\n'
         'Write date and time of Task in form DD.MM.YY HH:MM\n'
         'for example 12.12.16 4:20')
         del(task)
         return GETTING_DATE_AND_TIME
    user_data['task'] = task
    update.message.reply_text("Write your task:")
    del(task)
    return GETTING_TASK_TEXT
  
    
def get_task_text(bot, update, user_data, job_queue):
    task = user_data['task']
    task.set_text(update.message.text)  
    
    user_id = update.message.from_user.id
    
    if user_id not in users:
        user = User(update.message.from_user.first_name, update.message.chat_id)
        users[user_id] = user
    else: 
        user = users[user_id]
    user.add_task(task)
    user_data.clear()
    try:
        dt = (task.datetime - datetime.datetime.now())
        delta = dt.days*24*60*60 + dt.seconds
        job = Job(alarm, delta, repeat = False, context = (user.chat_id, task.text, user.name))
        job_queue.put(job)
        update.message.reply_text("OK, i will remind you to do this task!")
    except (IndexError, ValueError):
        update.message.reply_text('Sorry, we have an error')
            
    return ConversationHandler.END


def add_target(bot, update):
    update.message.reply_text(
        "Give me yout Target")   
    return GETTING_TARGET


def get_target_text(bot, update, user_data):
    
    user_id = update.message.from_user.id
    
    if user_id not in users:
        user = User(update.message.from_user.first_name, update.message.chat_id)
    else: 
        user = users[user_id]
    target = Target(update.message.text)
    user.add_target(target)
    update.message.reply_text("OK, I will memorise it")
    return ConversationHandler.END

    
def cancel(bot, update):
    #some text for user 
    return ConversationHandler.END


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(config.TOKEN)
    
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],

        states={
            CHOOSING: [RegexHandler('^Task$',
                                    add_task, pass_user_data=False),
                       RegexHandler('^Target$',
                                    add_target, pass_user_data=False),
                       ],

            GETTING_DATE_AND_TIME: [MessageHandler(Filters.text,
                                           get_date_and_time,
                                           pass_user_data=True),
                            ],
                            
            GETTING_TASK_TEXT: [MessageHandler(Filters.text,
                                           get_task_text,
                                           pass_user_data=True, pass_job_queue=True),
                            ],
           

            GETTING_TARGET: [MessageHandler(Filters.text,
                                          get_target_text,
                                          pass_user_data=True),
                           ],
        },

        fallbacks=[RegexHandler('^Cancel$', cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("start", start))  
    dp.add_handler(CommandHandler("help", help))


    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()