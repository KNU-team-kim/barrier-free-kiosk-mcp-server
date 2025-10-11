# mcp_server.py

import json
import re
from typing import Optional, Literal

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, field_validator, create_model, constr

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser

from mcp.server.fastmcp import FastMCP, Context
from mcp.server.elicitation import (
    AcceptedElicitation,
    DeclinedElicitation,
    CancelledElicitation,
)

# .env 파일 로드
load_dotenv()

# MCP 서버 초기화
mcp_server = FastMCP("Civil Complaint MCP Server", port=8001, host="0.0.0.0")


# --- Pydantic 모델 정의 ---

class ElicitationResponse(BaseModel):
    """ Elicitation 콜백에서 사용자가 전달한 메시지를 담는 모델 """
    user_message: Optional[str] = Field(default=None)


class ResidentRegistrationOutput(BaseModel):
    """ 주민등록초본 발급 프로세스의 최종 결과물 모델 """
    resident_registration_number: Optional[constr(pattern=r"^\d{6}-\d{7}$")] = Field(
        default=None,
        description="사용자의 주민등록번호 ('xxxxxx-xxxxxxx' 형식).",
    )
    issuance_type: Optional[Literal["DETAILED", "SIMPLE"]] = Field(
        default=None,
        description="발급 형태. 'DETAILED'는 전체발급, 'SIMPLE'은 선택발급."
    )
    number_of_copies: Optional[int] = Field(
        default=None,
        description="발급 부수."
    )
    is_confirmed: Optional[bool] = Field(
        default=None,
        description="사용자가 최종적으로 내용 확인을 했는지 여부."
    )

    @field_validator("resident_registration_number")
    @classmethod
    def _validate_rrn(cls, v):
        if v is None:
            return v
        if not re.fullmatch(r"\d{6}-\d{7}", v):
            raise ValueError("주민등록번호 형식은 'xxxxxx-xxxxxxx' 여야 합니다.")
        return v


class MoveInDeclarationOutput(BaseModel):
    """ 전입신고 프로세스의 최종 결과물 모델 """
    status: str = Field(description="전입신고 진행 상태.")


# --- LLM 체인 생성 함수 ---

async def create_llm_chain(pydantic_object: type[BaseModel], system_prompt: str):
    """ LLM, 프롬프트, 출력 파서를 결합하여 LangChain 체인을 생성하는 헬퍼 함수 """
    llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    parser = PydanticOutputParser(pydantic_object=pydantic_object)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{user_message}")
    ])

    fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=llm, max_retries=3)
    return prompt | llm | fixing_parser


# --- NEW TOOL 1: 주민등록초본 발급 서비스 ---

@mcp_server.tool(name="issue_resident_registration")
async def issue_resident_registration(ctx: Context, session_id: str) -> ResidentRegistrationOutput:
    """ 주민등록초본 발급 절차를 단계별로 처리하는 Tool. 사용자가 주민등록초본 발급을 원할 때 호출됩니다. """
    
    logger.info(f"[{session_id}] Starting resident registration process.")
    output = ResidentRegistrationOutput()

    # --- STEP 1: 주민등록번호 입력 ---
    system_prompt_rrn = """
    당신은 주민등록번호 입력을 처리하는 AI입니다. 사용자의 입력을 'xxxxxx-xxxxxxx' 형식으로 변환해야 합니다.
    - 사용자가 하이픈(-) 없이 13자리 숫자만 입력하면, 6번째 자리 뒤에 하이픈을 추가하세요. (예: 9001011234567 -> 900101-1234567)
    - 형식이 올바르지 않으면 사용자에게 정중하게 재입력을 요청하는 메시지를 생성하세요.
    JSON 형식으로만 응답하세요. 예:
    {{"resident_registration_number": "012345-1234567"}}
    또는
    {{"ai_message": "오류 메시지"}}
    """
    RRNStep = create_model("RRNStep", resident_registration_number=(Optional[str], None), ai_message=(Optional[str], None))
    rrn_chain = await create_llm_chain(pydantic_object=RRNStep, system_prompt=system_prompt_rrn)

    ai_message = "주민등록초본 발급을 시작합니다. 주민등록번호 13자리를 입력해주세요. (예: 900101-1234567)"
    while output.resident_registration_number is None:
        response = await ctx.elicit(
            message=json.dumps({"session_id": session_id, "retrieve_output": True, "ai_message": ai_message, "step_name": "get_rrn"}),
            schema=ElicitationResponse,
        )
        if isinstance(response, AcceptedElicitation):
            parsed_rrn = await rrn_chain.ainvoke({"user_message": response.data.user_message})
            rrn_value = getattr(parsed_rrn, "resident_registration_number", None)
            msg_value = getattr(parsed_rrn, "ai_message", None)

            if rrn_value:
                if re.fullmatch(r"\d{13}", rrn_value):
                    rrn_value = f"{rrn_value[:6]}-{rrn_value[6:]}"
                if re.fullmatch(r"\d{6}-\d{7}", rrn_value):
                    output.resident_registration_number = rrn_value
                else:
                    ai_message = "형식이 올바르지 않습니다. 예: 900101-1234567"
            else:
                ai_message = msg_value or "형식이 올바르지 않습니다. 다시 입력해 주세요."
        else:
            return output

    # --- STEP 2: 발급 형태 선택 ---
    system_prompt_type = """
    사용자의 답변을 분석하여 발급 형태를 결정하세요.
    - '전체', '모두', '다' 등 전체를 의미하면 'DETAILED'
    - '선택', '일부', '특정 항목' 등 부분을 의미하면 'SIMPLE'
    JSON 형식으로만 응답하세요:
    {{"issuance_type": "DETAILED"}} 또는 {{"issuance_type": "SIMPLE"}}
    """
    TypeStep = create_model("TypeStep", issuance_type=(Literal["DETAILED", "SIMPLE"], ...))
    type_chain = await create_llm_chain(pydantic_object=TypeStep, system_prompt=system_prompt_type)

    ai_message = "발급 형태를 선택해주세요: 전체발급 또는 선택발급"
    while output.issuance_type is None:
        response = await ctx.elicit(
            message=json.dumps({"session_id": session_id, "retrieve_output": True, "ai_message": ai_message, "step_name": "get_issuance_type"}),
            schema=ElicitationResponse
        )
        if isinstance(response, AcceptedElicitation):
            parsed_type = await type_chain.ainvoke({"user_message": response.data.user_message})
            output.issuance_type = getattr(parsed_type, "issuance_type", None)
            if output.issuance_type is None:
                ai_message = "잘 이해하지 못했어요. '전체발급' 또는 '선택발급' 중 하나로 답해주세요."
        else:
            return output

    # --- STEP 3: 발급 부수 입력 ---
    system_prompt_copies = """
    사용자의 자연어 답변에서 발급할 부수를 정수형 숫자로 추출하세요.
    예: '한 부', '2장', '다섯개' -> 1, 2, 5.
    JSON 형식으로만 응답하세요:
    {{"number_of_copies": 1}}
    """
    CopiesStep = create_model("CopiesStep", number_of_copies=(int, ...))
    copies_chain = await create_llm_chain(pydantic_object=CopiesStep, system_prompt=system_prompt_copies)

    ai_message = "몇 부 발급하시겠습니까?"
    while output.number_of_copies is None:
        response = await ctx.elicit(
            message=json.dumps({"session_id": session_id, "retrieve_output": True, "ai_message": ai_message, "step_name": "get_copies"}),
            schema=ElicitationResponse
        )
        if isinstance(response, AcceptedElicitation):
            parsed_copies = await copies_chain.ainvoke({"user_message": response.data.user_message})
            output.number_of_copies = getattr(parsed_copies, "number_of_copies", None)
            if output.number_of_copies is None:
                ai_message = "숫자로 이해하지 못했어요. 예: 1부, 2부"
        else:
            return output

    # --- STEP 4: 내용 및 수수료 확인 ---
    system_prompt_confirm = """
    사용자의 답변이 긍정('네', '맞아요', '확인')인지 부정인지 판단하여 boolean 값으로 반환하세요.
    JSON 형식으로만 응답하세요:
    {{"is_confirmed": true}} 또는 {{"is_confirmed": false}}
    """
    ConfirmStep = create_model("ConfirmStep", is_confirmed=(bool, ...))
    confirm_chain = await create_llm_chain(pydantic_object=ConfirmStep, system_prompt=system_prompt_confirm)

    fee = 400
    confirmation_message = f"""
    [신청 내용 확인]
    - 신청 내용: 주민등록초본
    - 신청 부수: {output.number_of_copies}부
    - 수수료: {fee * output.number_of_copies}원

    위 내용이 맞으신가요? (네/아니오)
    """
    response = await ctx.elicit(
        message=json.dumps({"session_id": session_id, "retrieve_output": True, "ai_message": confirmation_message, "step_name": "confirm_details"}),
        schema=ElicitationResponse
    )
    if isinstance(response, AcceptedElicitation):
        parsed_confirm = await confirm_chain.ainvoke({"user_message": response.data.user_message})
        output.is_confirmed = getattr(parsed_confirm, "is_confirmed", None)
    else:
        return output

    final_message = "발급이 완료되었습니다. 감사합니다." if output.is_confirmed else "요청이 취소되었습니다. 처음부터 다시 시작해주세요."
    await ctx.elicit(
        message=json.dumps({"session_id": session_id, "retrieve_output": False, "ai_message": final_message, "step_name": "final_result"}),
        schema=ElicitationResponse
    )
    
    logger.info(f"[{session_id}] Resident registration process finished.")
    return output


# --- NEW TOOL 2: 전입신고 서비스 ---

@mcp_server.tool(name="process_move_in_declaration")
async def process_move_in_declaration(ctx: Context, session_id: str) -> MoveInDeclarationOutput:
    """ 전입신고 절차를 처리하는 Tool. 사용자가 이사 또는 전입신고를 원할 때 호출됩니다. """
    
    logger.info(f"[{session_id}] Starting move-in declaration process.")
    ai_message = "전입신고서 작성을 시작합니다. 자세한 절차는 추후 구현될 예정입니다."

    await ctx.elicit(
        message=json.dumps({
            "session_id": session_id,
            "retrieve_output": False,
            "ai_message": ai_message,
            "step_name": "start_move_in"
        }),
        schema=ElicitationResponse
    )

    return MoveInDeclarationOutput(status="move_in_declaration_started")


if __name__ == "__main__":
    mcp_server.run(transport="streamable-http")