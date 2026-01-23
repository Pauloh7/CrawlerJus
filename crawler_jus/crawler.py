import logging
import re
import asyncio
import base64
import hashlib
import json
from datetime import datetime
from bs4 import BeautifulSoup as bs
from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt,
)
from util import (
    remove_blank_space,
    remove_special_characters,
)
from processo import *
from curl_cffi.requests import AsyncSession,Response
from urllib.parse import urlencode

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
            verify=False,
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
    
    @staticmethod
    def solve_challenge(salt, challenge, maxnumber):
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
    async def request_auth(self,url) -> Processo:
        auth = await self.create_authorization()
        print(auth)
        response = await self.request_page(auth=auth,url=url)
        movimentos = await self.extract_movimentos(response.text)
        return auth
        

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5), reraise=True)
    async def request_page(self, auth: str,url: str) -> Processo:
        headers = self.headers_consulta
        headers["Authorization"] = auth
        return await self.client.get(
           url,headers=headers
        )                                                                                                                     


    def extract_basic_data(self, basic_data_json: dict) -> dict:
        data = {
            "nomeClasse": None,
            "nomeNatureza": None,
            "classeCNJ": None,
            "assuntoCNJ": None,
            "partes": [], 
        }
        data_ditc = json.loads(basic_data_json)
        basic = data_ditc["data"][0]
        partes = data_ditc["data"][0]["partes"]["parte"]
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


    def extract_movimentos(self, movimentos_json: bs) -> list[str, str]:
        """"""
        movimentos = []
        mov_dict = json.loads(movimentos_json)
        movimentos = mov_dict["data"]

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

        primeiro = await robo.request_auth("https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaMovimentacao?numeroProcesso=50016466620268210008&codComarca=8")
        print(primeiro.__dict__ if primeiro else None)

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
