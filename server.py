# server.py

import anyio
import json
from loguru import logger
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from steps.move_in_steps import MOVE_IN_STEPS
from steps.resident_registration_steps import RESIDENT_REGISTRATION_STEP
from prompts.move_in_prompt import MOVE_IN_PROMPT
from prompts.resident_registration_prompt import RESIDENT_REGISTRATION_PROMPT
from interfaces.move_in_output import MoveInOutput
from interfaces.resident_registration_output import ResidentRegistrationOutput
from interfaces.output import Output
from fetch.fetch_move_in import fetch_move_in, fetch_check_phone_number, fetch_retrieve_address
from fetch.fetch_resident_registration import fetch_resident_registration, fetch_check_registration_number
from config import OPENAI_API_KEY, OPENAI_API_URL

from mcp.server.elicitation import (
    AcceptedElicitation,
    DeclinedElicitation,
    CancelledElicitation,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain.output_parsers import OutputFixingParser, PydanticOutputParser
from mcp.server.fastmcp import FastMCP, Context


mcp_server = FastMCP("Barrier Free Kiosk MCP Server", port=8001, host="0.0.0.0")

class ElicitationResponse(BaseModel):
    user_message: Optional[str] = Field(default=None)

class StepOutput(BaseModel):
    ai_message: Optional[str] = Field(default=None)
    data: Optional[str] = Field(default=None)
    cancel: Optional[bool] = Field(default=None)

async def retrieve_agent_chain(PROMPT: str):
    llm = ChatOpenAI(
        model="gpt-oss-20b", 
        base_url=OPENAI_API_URL,
        api_key=OPENAI_API_KEY,
        streaming=False
    )
    system_message = PROMPT

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ]
    )
    output_parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=StepOutput),
        llm=llm,
        max_retries=3,
    )
    agent_chain = prompt | llm | output_parser
    return agent_chain

@mcp_server.tool(name="move-in-conversation", title="전입신고")
async def move_in_conversation(ctx: Context, session_id: Optional[str] = None) -> Output:
    """사용자가 '전입신고' 관련 요청을 할 때 사용됩니다. 전입신고 절차를 진행합니다."""
    chat_history = []
    move_in_output = MoveInOutput()
    agent_chain = await retrieve_agent_chain(MOVE_IN_PROMPT)

    for step_name, step_prompt in MOVE_IN_STEPS:
        user_message = ""
        step_output = "nothing"
        retrieve_output = True

        while step_output == "nothing":
            try:
                ai_output = await agent_chain.ainvoke(
                    input={
                        "input": user_message,
                        "step_prompt": step_prompt,
                        "chat_history": chat_history,
                    }
                )

                if ai_output.cancel:
                    return Output(message="취소되었습니다. 어떤 서비스를 원하시나요?")

                if ai_output.data:
                    if step_name == "phone_number" and not fetch_check_phone_number(ai_output.data, move_in_output.name):
                        ai_output.ai_message = "정보를 찾을 수 없습니다. 전화번호를 다시 말씀해주세요."
                        ai_output.data = None
                    elif step_name == "before_sigungu":
                        retrieve_output = False
                        step_output = ai_output.data
                        ai_output.data = fetch_retrieve_address(move_in_output.name, move_in_output.phone_number)
                    elif step_name == "after_building_number_sub" and ai_output.data == "null":
                        retrieve_output = False
                        ai_output.data = None
                        step_output = ai_output.data
                    elif step_name == "other_service":
                        retrieve_output = False
                        step_output = None
                        if ai_output.data == "null":
                            ai_output.data = []
                        else:
                            ai_output.data = [part.strip() for part in ai_output.data.split(",")]
                    else:
                        retrieve_output = False
                        step_output = ai_output.data

                response = await ctx.elicit(
                    message=json.dumps(
                        {
                            "session_id": session_id,
                            "retrieve_output": retrieve_output,
                            "data": ai_output.data,
                            "ai_message": ai_output.ai_message,
                            "step_name": step_name,
                        }
                    ),
                    schema=ElicitationResponse,
                )

                match response:
                    case AcceptedElicitation(data=data):
                        user_message = data.user_message
                    case DeclinedElicitation():
                        break
                    case CancelledElicitation():
                        break

            except (anyio.ClosedResourceError, ConnectionError) as e:
                logger.exception(e)
                raise e
            except Exception as e:
                logger.exception(e)
                raise e

        if hasattr(move_in_output, step_name):
            setattr(move_in_output, step_name, step_output)

    code = fetch_move_in(move_in_output)

    if code != 200: return Output(message="오류가 발생했습니다. 다시 시도해 주십시오.", status_code=code)
    return Output(message="전입 신고가 완료되었습니다.", status_code=code)

@mcp_server.tool(name="resident-registration-conversation", title="주민등록초본 발급")
async def resident_registration_conversation(ctx: Context, session_id: Optional[str] = None) -> Output:
    """사용자가 '주민등록초본' 관련 서류 발급을 요청할 때 사용됩니다."""
    chat_history = []
    resident_registration_output = ResidentRegistrationOutput()
    agent_chain = await retrieve_agent_chain(RESIDENT_REGISTRATION_PROMPT)

    for step_name, step_prompt in RESIDENT_REGISTRATION_STEP:
        user_message = ""
        step_output = "nothing"
        retrieve_output = True

        while step_output == "nothing":
            try:
                new_step_prompt = step_prompt

                if step_name == 'check':
                    new_step_prompt = step_prompt.format(
                        number=resident_registration_output.number,
                        fee=4000
                    )

                ai_output = await agent_chain.ainvoke(
                    input={
                        "input": user_message,
                        "step_prompt": new_step_prompt,
                        "chat_history": chat_history,
                    }
                )

                if ai_output.cancel:
                    return Output(message="취소되었습니다. 어떤 서비스를 원하시나요?")

                if ai_output.data:
                    if step_name == "registration_number" and not fetch_check_registration_number(ai_output.data):
                        ai_output.ai_message = "정보를 찾을 수 없습니다. 주민등록번호를 다시 입력해주세요."
                        ai_output.data = None
                    else:
                        retrieve_output = False
                        step_output = ai_output.data

                response = await ctx.elicit(
                    message=json.dumps(
                        {
                            "session_id": session_id,
                            "retrieve_output": retrieve_output,
                            "data": ai_output.data,
                            "ai_message": ai_output.ai_message,
                            "step_name": step_name,
                        }
                    ),
                    schema=ElicitationResponse,
                )

                match response:
                    case AcceptedElicitation(data=data):
                        user_message = data.user_message
                    case DeclinedElicitation():
                        break
                    case CancelledElicitation():
                        break

            except (anyio.ClosedResourceError, ConnectionError) as e:
                logger.exception(e)
                raise e
            except Exception as e:
                logger.exception(e)
                raise e

        if hasattr(resident_registration_output, step_name):
            setattr(resident_registration_output, step_name, step_output)

    code = fetch_resident_registration(resident_registration_output)

    if code != 200: return Output(message="오류가 발생했습니다. 다시 시도해 주십시오.", status_code=code)
    return Output(message="주민등록초본을 출력 중입니다.", status_code=code)

if __name__ == "__main__":
    mcp_server.run(transport="streamable-http")