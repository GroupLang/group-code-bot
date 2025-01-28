import pytest
from main import handle_update, process_provider_messages


@pytest.mark.asyncio
async def test_end_to_end():
    # test = {"update_id":551657663,"message":{"message_id":28,"from":{"id":471057601,"is_bot":False,"first_name":"Victor","last_name":"Adan","username":"vadanrod14","language_code":"es"},"chat":{"id":-1002366990567,"title":"testimo01","type":"supergroup"},"date":1738068403,"message_thread_id":27,"reply_to_message":{"message_id":27,"from":{"id":7505042242,"is_bot":True,"first_name":"GroupCodeBot","username":"group_code_bot"},"chat":{"id":-1002366990567,"title":"testimo01","type":"supergroup"},"date":1738068260,"text":"\\ud83d\\udce9 Message from provider:\\n(876a3f4c-747c-443a-9100-8b1a14496273)\\nfor instance: 9972d213-400a-4ea7-a087-c8d9d222fe67\\n\\u23f0 2025-01-28 12:32:50 UTC\\n\\nSolved instance 9972d213-400a-4ea7-a087-c8d9d222fe67 with PR https://github.com/numba/numba-examples/pull/45","entities":[{"offset":204,"length":47,"type":"url"}],"link_preview_options":{"url":"https://github.com/numba/numba-examples/pull/45"}},"text":"can you explain betteR?"}}
    # await handle_update(test)

    await process_provider_messages()

