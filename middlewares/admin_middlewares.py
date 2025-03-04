from typing import Any

from aiogram import BaseMiddleware

class IsAdminMiddleware(BaseMiddleware):
    def __init__(self, telegram_ids: list[int]) -> None:
        self.telegram_ids = telegram_ids

    async def __call__(self,
                 handler,
                 event,
                 data) -> Any:
        user = data['event_from_user']
        user_id = user.id
        if user_id in self.telegram_ids:
            return await handler(event, data)

class DeleteKbMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data) -> Any:
        if data.get('delete_kb') and 'message' in data:
            await data['message'].edit_reply_markup()
        else:
            data['delete_kb'] = False
        result = await handler(event, data)
        data['delete_kb'] = False
        return result
