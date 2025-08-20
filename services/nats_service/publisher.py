from nats.js.client import JetStreamContext
import json
import logging


logger = logging.getLogger(__name__)

async def call_publisher(js: JetStreamContext, chat_id: str,
                         message: str, subject: str) -> None:
    
    try:    
        data = {
            'chat_id': chat_id,
            'message': message
        }
        await js.publish(subject=subject,
                        payload=json.dumps(data).encode()
        )
        logger.info(
            f'Сообщение отправлено в NATS для пользователя {chat_id}'
        )
    
    except Exception as e:
        logger.error(f'Ошибка отправки сообщения в NATS: {e}')