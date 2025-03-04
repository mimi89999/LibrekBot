# Python libraries that we need to import for our bot
import config

import asyncio
import random
import string
import threading
from hashlib import sha1

from flask import request
from pymessenger.bot import Bot

from librus_tricks import create_session

from librekbot import app, db
from librekbot.models import Recipient, SentAnnouncement


ACCESS_TOKEN = 'JGSIDFJGOSFGUHFSUGHIFUSDHGIUFHIUHDGIUHFIDUHGDIUHFDIUGHDIFUHGIUDHFGIUHDGFIFDGHIUFDGH'
VERIFY_TOKEN = 'SDFJOIUDSJUDIFHUIHSDIFUHIUDSHFIUFDHSIH'
bot = Bot(ACCESS_TOKEN)
# When Librus and Synergia accounts have diffrent passwords
# session = SynergiaClient(authorizer('MAIL', 'HASLOLIBRUS')[0], synergia_user_passwd='HASLOSYNERGIA')
session = create_session(config.login, config.password)


# We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook."""
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    # if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
        output = request.get_json()
        # if(not session.user.is_valid):
        # session.user.revalidate_user()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                # print("wiadomosc")
                # print(repr(message))
                if message.get('message'):
                    # print("istnieje")
                    # Facebook Messenger ID for user so we know where to send response back to
                    recipient_id = message['sender']['id']
                    if message['message'].get('text'):
                        msg = message['message']['text']
                        if msg.lower() == "subskrybuj":
                            if not Recipient.query.filter_by(fb_id=recipient_id).first():
                                db.session.add(Recipient(fb_id=recipient_id, student_class=''))
                                db.session.commit()
                            else:
                                send_message(recipient_id, "Jestes juz dodany do listy!")
                            print("wyslalem")
                        # elif(msg.lower() == "wszystkie_zmiany"):
                        # for news in session.news_feed():
                        # send_message(recipient_id, f'{news.content}')
                        elif (msg.lower().replace('!', '').replace('.', '') in ['ostatnie zmiany', 'zmiany',
                                                                                'last changes',
                                                                                'changes'] or "zmiany" in msg.lower() or "changes" in msg.lower()):
                            newslist = session.news_feed()
                            send_message(recipient_id, "Przesyłam ostatnie dwa ogłoszenia")
                            send_message(recipient_id, f'{newslist[-1].content}')
                            send_message(recipient_id, f'{newslist[-2].content}')
                        elif (msg.lower().replace('!', '').replace('.', '') in ['hi', 'hello', 'hej', 'siema',
                                                                                'good morning', 'greetings']):
                            send_message(recipient_id, "Hej! Jestem Librekbot.")
                            send_message(recipient_id, "Potrafię przesłać Ci kilka ostatnich zmian w planie.")
                            send_message(recipient_id, "Napisz \"pomoc\", aby dowiedzieć się, jak mnie używać!")
                        elif (msg.lower().replace('!', '').replace('.', '') in ['pomoc', 'help']):
                            send_message(recipient_id, "Widzę, że jeszcze nie wiesz, jak mnie używać!")
                            send_message(recipient_id, "Mam nadzieję, że to Ci pomoże:")
                            send_message(recipient_id, "Jeśli chcesz mnie spytać o ostatnie zmiany w planie, napisz:")
                            send_message(recipient_id, "\"ostatnie zmiany\"")
                        elif (msg.lower().replace('!', '').replace('.', '') in ['info', 'informacje', 'author']):
                            send_message(recipient_id,
                                         "Zostałem stworzony, żebyś mógł łatwiej dowiedzieć się o zmianach w planie :)")
                        elif (msg.lower().replace('!', '').replace('.', '') in ['dzięki', 'dzieki', 'dziekuje',
                                                                                'dziękuję', 'thanks', 'thank\'s',
                                                                                'thank you']):
                            wiad = random.choice(["Zawsze do usług!", "Nie ma sprawy", "Miło było Ci pomóc!"])
                            send_message(recipient_id, wiad)
                        elif (msg.lower().replace('!', '').replace('.', '') in ['bye', 'do zobaczenia', 'goodbye',
                                                                                'see ya', 'see ya later', 'dobranoc',
                                                                                'good night']):
                            wiad = random.choice(["Zawsze do usług!", "Nie ma sprawy!", "Miło było Ci pomóc!"])
                            send_message(recipient_id, wiad)
                        else:
                            first = random.choice(
                                ["Niestety, ale tym razem nie udało mi się zrozumieć Twojej wiadomości.",
                                 "Nie wiem, jak Ci odpowiedzieć, może spróbujesz czegoś innego?",
                                 "Nie zrozumiałem Cię, czy możesz napisać inaczej?"])
                            send_message(recipient_id, first)
                            send_message(recipient_id, "Możesz mnie spytać o ostatnie zmiany w planie, pisząc:")
                            send_message(recipient_id, "\"ostatnie zmiany\"")
                            # send_message(recipient_id,newslist[-3])
                    # if user sends us a GIF, photo,video, or any other non-text item
                    if message['message'].get('attachments'):
                        response_sent_nontext = get_message()
                        send_message(recipient_id, response_sent_nontext)
    return "Message Processed"


def verify_fb_token(token_sent):
    # take token sent by facebook and verify it matches the verify token you sent
    # if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


# chooses a random message to send to the user
def get_message():
    sample_responses = ["Ale fajna fota!", "Jestem z Ciebie dumny.", "Dawaj więcej!", "Wow!"]
    # return selected item to the user
    return random.choice(sample_responses)


# uses PyMessenger to send response to user
def send_message(recipient_id, response):
    # sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"


@asyncio.coroutine
async def send_new_messages():
    while (True):
        # if(not session.user.is_valid):
        # session.user.revalidate_user()
        for news in session.news_feed():
            checksum = sha1(news.content.encode('utf-8')).hexdigest()
            if not SentAnnouncement.query.filter_by(checksum=checksum).first():
                db.session.add(SentAnnouncement(unique_id=news.unique_id, checksum=checksum))
                db.session.commit()

                for recipient in Recipient.query.all():
                    message = ""
                    for line in news.content.split("\n"):
                        otherClass = False
                        if (
                                "3f" not in line.lower() and "wszyscy" not in line.lower() and "wszystkie" not in line.lower() and "każda" not in line.lower()):
                            for i in range(1, 4):
                                for letter in string.ascii_lowercase:
                                    if (str(i) + letter in line.lower()):
                                        otherClass = True
                        if (not otherClass):
                            message += line + "\n"
                    send_message(recipient.fb_id, f'{message}')
                    print("do:" + str(recipient.fb_id))
        await asyncio.sleep(60 * 5)


def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_new_messages())


if __name__ == "__main__":
    send_message('2999999999999999', 'Włączyłem się!')
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=loop_in_thread, args=(loop,))
    t.start()
    app.run(host='0.0.0.0')
