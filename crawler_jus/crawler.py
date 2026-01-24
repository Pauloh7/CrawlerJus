import logging
import asyncio
import base64
import hashlib
import json
from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt,
)
from .util import extract_comarca, remove_special_characters
from curl_cffi.requests import AsyncSession

logger = logging.getLogger()


class Crawler:
    """
    Robo que extrai dados do site TJAL(Tribunal de Justiça do Estado de Alagoas)

    Attributes:
        timeout (int): Padrao de timeout para tentativas de conexao
        urlconsutla (str): Url de consulta de processos de alagoas primeira instancia

    """

    def __init__(self):
        self.headers_consulta = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,pt-PT;q=0.5",
            "Authorization": "",
            "Origin": "https://consulta.tjrs.jus.br",
            "Referer": "https://consulta.tjrs.jus.br/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36 OPR/125.0.0.0"
            ),
            "Sec-CH-UA": "\"Opera GX\";v=\"125\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": "\"Windows\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=1, i",
        }
        self.client = AsyncSession(
            impersonate="chrome120",
            timeout=30,
            verify=True,
        )
        self.url_token_request = "https://consulta-processual-service.tjrs.jus.br/api/consulta-service/public/auth/token"
        self.url_token_submit = "https://consulta-processual-service.tjrs.jus.br/api/consulta-service/public/auth/submit"
        
    
    async def close(self):
        await self.client.close()

    def obfuscate(self, auth):
        id_num = int(auth.replace("ChaAnon_", ""))
        
        n = (id_num % 60029) + 90767
        
        me = id_num * n
    
        se = f"@{n}@{me}!"
        
        ie = hashlib.sha256(se.encode()).hexdigest()
        
        final_str = f"{auth}:{ie}"
        return base64.b64encode(final_str.encode()).decode()
    
    def solve_challenge(self, salt, challenge, maxnumber):
        for i in range(maxnumber + 1):
            attempt = salt + str(i)
            result = hashlib.sha256(attempt.encode()).hexdigest()
            
            if result == challenge:
                return i
        return None
    
    async def create_authorization(self):
        challenge_token = await self.client.get(
            self.url_token_request
        )
        challenge_data = json.loads(challenge_token.text)
        challenge_result = await asyncio.to_thread (self.solve_challenge, challenge_data["salt"], challenge_data["challenge"],  challenge_data["maxnumber"])
        payload = {
            "algorithm": challenge_data["algorithm"],
            "challenge": challenge_data["challenge"],
            "number": challenge_result,
            "salt": challenge_data["salt"],
            "signature": challenge_data["signature"]
        }

        json_str = json.dumps(payload, separators=(',', ':')) # remove espaços para o hash bater
        token_base64 = base64.b64encode(json_str.encode()).decode()
        form_data = {
            "altcha": token_base64 
        }
        authorization_response =  await self.client.post(
            self.url_token_submit, 
            data=form_data
            )
        authorization = json.loads(authorization_response.text)
        authorization = await asyncio.to_thread (self.obfuscate,authorization["username"])
        authorization = f"Basic {authorization}"

        return authorization
        
    


    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5), reraise=True)
    async def request_auth(self,url) -> str:
        auth = await self.create_authorization()
        response = await self.request_page(auth=auth,url=url)
        basic_data = await self.extract_basic_data(response.text)
        return basic_data
        

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5), reraise=True)
    async def request_page(self, auth: str,url: str) -> json:
        headers = {**self.headers_consulta, "Authorization": auth}
        return await self.client.get(
           url,headers=headers
        ).text                                                                                                                     


    def extract_basic_data(self, basic_data_json: json) -> dict:
        data_dict = json.loads(basic_data_json)
        basic = (data_dict.get("data") or [{}])[0]
        partes = basic.get("partes", {}).get("parte", [])
        partes_list = [
            {
                "descricaoTipo": p.get("descricaoTipo"),
                "nome": p.get("nome"),
            }
            for p in partes
]
        data = {
            "nomeClasse": basic.get("nomeClasse"),
            "nomeNatureza": basic.get("nomeNatureza"),
            "classeCNJ": basic.get("classeCNJ"),
            "assuntoCNJ": basic.get("assuntoCNJ"),
            "partes":partes_list
        }

        return data


    def extract_movimentos(self, movimentos_json: str) -> list[dict[str]]:
        """"""
        mov_dict = json.loads(movimentos_json)
        movimentos = mov_dict.get("data") or []

        movimentos_list = [
            {
                "data": m.get("data"),
                "descricao": m.get("descricao"),
            }
            for m in movimentos
        ]

        return movimentos_list




async def main():
    robo = Crawler()
    try:
        npu_list = [
        '5001646-66.2026.8.21.0008',
        '5001437-97.2026.8.21.0008',
        '5006512-41.2026.8.21.0001',
        '5002803-95.2026.8.21.0001',
        '5059773-31.2025.8.21.0008',
        '5037275-17.2025.8.21.0015',
        '5034351-53.2025.8.21.0073',
        '5324952-46.2025.8.21.0001',
        '5034160-31.2025.8.21.0033',
        '5317349-19.2025.8.21.0001',
        '5317128-36.2025.8.21.0001',
        '5010384-59.2025.8.21.0014',
        '5056077-84.2025.8.21.0008',
        '5003595-28.2025.8.21.0084',
        '6000461-52.2025.8.21.3001',
        '5027923-11.2025.8.21.0023',
        '5023236-79.2025.8.21.0026',
        '5027334-19.2025.8.21.0023'
        ]
        for npu in npu_list:
            npu = remove_special_characters(npu)
            comarca = extract_comarca(npu)
            url = f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaProcesso?numeroProcesso={npu}&codComarca={comarca}"
            result = await robo.request_auth(url)
            print(result)

    finally:
        await robo.client.close()

if __name__ == "__main__":
    asyncio.run(main())        

    # AL-code 07108025520188020001
    # AL-nocode 08033402420198020000
    # TJCE - 00703379120088060001
    # 0805757-08.2023.8.02.0000
    # 07114332320238020001
    # tribunal = extract_tribunal("07108025520188020001")
    # primeiro_grau_info = robo.send_request_primeiro_grau(
    #     "07108025520188020001", tribunal
    # )
    # print(primeiro_grau_info)
    # segundo_grau_info = robo.send_request_segundo_grau("07108025520188020001", tribunal)
    # print(segundo_grau_info)
