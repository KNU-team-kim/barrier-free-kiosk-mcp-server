MOVE_IN_STEPS = [
    (
        "name",
        "Step 1, The user needs to provide their name. Ask the user to tell their name. If a name is provided, confirm."
    ),
    (
        "phone_number",
        "Step 2, The user needs to provide their phone number. Ask the user to tell their phone number, without giving any formatting instructions. If a phone number is provided without hyphens, automatically convert it into the format 010-1234-5678. If provided, confirm."
    ),
    (
        "reason",
        """
        Step 3, The user must decide the reason for moving in. Ask the user why they are moving in. If a reason is provided, confirm.
        Do NOT show any category list to the user. Instead, infer the correct category internally based on their response and store exactly one of: 
            - JOB (Employment: getting a job, starting a business, job relocation, etc.) 
            - FAMILY (Family: living with family, marriage, moving out from parents, etc.) 
            - HOUSE (Housing: buying a house, lease expiration, rent issues, redevelopment, etc.) 
            - EDUCATION (Education: admission, studies, children's education, etc.) 
            - ENVIRONMENT (Living environment: transportation, culture, facilities, etc.) 
            - NATURE (Natural environment: health, pollution, rural life, etc.)
        """
    ),
    (
        "before_sido",
        """
            Step 4, Ask the user to provide the classification of their previous place of residence. Ask for the city/province (시/도) without giving any formatting instructions. If provided, confirm.
                example of city/province: 대구광역시, 서울특별시 etc.  
            Do NOT show any example to the user.
        """
    ),
    (
        "before_sigungu",
        """
            Step 5, Ask the user to provide the classification of their previous place of residence. Ask for the district/county (시/군/구), without giving any formatting instructions. If provided, confirm.
                example of district/county: 강남구, 중구, 수원시 etc.
            Do NOT show any example to the user.
        """
    ),
    (
        "after_sido",
        """
            Step 6, Ask the user to provide the classification of their current place of residence. Ask for the city/province (시/도), without giving any formatting instructions. If provided, confirm.
                example of city/province: 대구광역시, 서울특별시 etc.  
            Do NOT show any example to the user.
        """
    ),
        (
        "after_sigungu",
        """
            Step 7, Ask the user to provide the classification of their current place of residence. Ask for the district/county (시/군/구), without giving any formatting instructions. If provided, confirm.
                example of district/county: 강남구, 중구, 수원시 etc.
            Do NOT show any example to the user.
        """
    ),
        (
        "after_road_name",
        """
            Step 8, Ask the user to provide the classification of their current place of residence. Ask for the road name (도로명), without giving any formatting instructions. If provided, confirm.
                example of road name: 대학로, 산격로, 대천로 etc.
            Do NOT show any example to the user.
        """
    ),
        (
        "after_building_number",
        """
            Step 9, Ask the user to provide the classification of their current place of residence. Ask for the building number (건물 번호), without giving any formatting instructions. If provided, confirm.
            Do NOT show any example to the user.
        """
    ),
        (
        "after_detail_address",
        """
            Step 10, Ask the user to provide the classification of their current place of residence. Ask for the detail address (상세 주소), without giving any formatting instructions. If provided, confirm.
                example of detail address: 100동 100호 etc.
            Do NOT show any example to the user.
        """
    )
]