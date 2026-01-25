import logging
import asyncio
import time
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
from typing import Optional
import random
from .exceptions import TJRSRateLimit

logger = logging.getLogger()


class Crawler:
    """
    Robo que extrai dados do site TJRS(Tribunal de Justiça do Estado do Rio Grande do Sul)

    Attributes:
        timeout (int): Padrao de timeout para tentativas de conexao
        headers_consulta: Headers padrao utilizado para requesiçoes de site,
        client: Cliente async que faz as requisiçoes
        url_token_request: Url de requisição do token challenge de acesso
        url_token_submit: Url de subimissão do token challenge de acesso
        _auth_value: Valor do challenge resolvido em cache
        _auth_expires_at: Horario em que a chave challenge em cache expira
        _auth_lock: Trava async de codigo critico
        _auth_ttl_seconds: Tempo medio que a chave challenge deve durar
    """

    def __init__(self):
        self.headers_consulta = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://consulta.tjrs.jus.br",
            "Referer": "https://consulta.tjrs.jus.br/",
            }
        self.client = AsyncSession(
            impersonate="chrome120",
            timeout=30,
            verify=True,
        )
        self.url_token_request = "https://consulta-processual-service.tjrs.jus.br/api/consulta-service/public/auth/token"
        self.url_token_submit = "https://consulta-processual-service.tjrs.jus.br/api/consulta-service/public/auth/submit"
        self._auth_value: Optional[str] = None
        self._auth_expires_at: float = 0.0
        self._auth_lock = asyncio.Lock()
        self._auth_ttl_seconds = 300 

    async def close(self):
        """Função que fecha o cliente de requisiçoes web"""
        await self.client.close()

    def is_rate_limited(self, text: str) -> tuple[bool, str]:
        """Função que testa se erro 429 esta no texto enviado
        Args:
            text (str): texto do json de reposta de consulta no site
        Returns:
            bool (bool): bool de retorno que indica se encontrou ou nao 429 no texto
            message (str) : mensagem do encontrada junto ao erro 429 
        """
        try:
            text_json = json.loads(text)
        except Exception:
            return False, ""

        if text_json.get("exceptionKey") == 429:
            message = (text_json.get("messages") or [""])[0]
            return True, message

        return False, ""
    
    async def sleep_backoff(self, attempt: int, base=1, cap=60):
        """Função que aguarda tempo baseado na quantidade de tentivas ja feitas
        Args:
            attempt (int): Quantidade de tentativas
        """
        wait = min(cap, base * (2 ** attempt))
        wait = wait + random.uniform(0, 1)       
        await asyncio.sleep(wait)

    async def get_auth(self, force_refresh: bool = False) -> str:
        """Função que controla o token challenge em cache
        Args:
            force_refresh (bool): bool que determina se o token challenge vai ser atualizado forçadamente
        Returns:
            auth (str): Token challenge resolvido
        """
        now = time.time()

        if not force_refresh and self._auth_value and now < self._auth_expires_at:
            return self._auth_value

        async with self._auth_lock:
            now = time.time()
            if not force_refresh and self._auth_value and now < self._auth_expires_at:
                return self._auth_value

            auth = await self.create_authorization()
            self._auth_value = auth
            self._auth_expires_at = now + self._auth_ttl_seconds
            return auth
    
    

    def obfuscate(self, auth: str)-> str:
        """Função que calcula o segredo que vai junto ao token challenge com base no mesmo para acesso ao site
        Args:
            auth (str): Token challenge resolvido
        Returns:
            final_str (str): Token challenge mais segredo em base64
        """
        id_num = int(auth.replace("ChaAnon_", ""))
        
        n = (id_num % 60029) + 90778
        
        me = id_num * n
    
        se = f"@{n}@{me}!"
        
        ie = hashlib.sha256(se.encode()).hexdigest()
        
        final_str = f"{auth}:{ie}"
        return base64.b64encode(final_str.encode()).decode()
    
    def solve_challenge(self, salt: int, challenge: int, maxnumber: int) -> int:
        """Função que calcula o token challenge
        Args:
            salt (int): Parte do calculo do desafio
            challenge(int): Número a ser encontrado
            maxnumber(int): Número maximo que challenge pode ter
        Returns:
            i (int): Número resultado do challenge
        """
        for i in range(maxnumber + 1):
            attempt = f"{salt}{i}"
            result = hashlib.sha256(attempt.encode()).hexdigest()
            
            if result == challenge:
                return i
        return None
    
    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5), reraise=True)
    async def create_authorization(self) -> str:
        """Função que controla todo o processo de criação da token challenge fazendo desde a requisição do desafio, a requisição de
        solução do challenge e retorno da chave para o acesso ao site
        Args:
        Returns:
            authorization (str): Token pronto para ser enviado na requisição de consulta ao site
        Raises:
        RuntimeError: Erro de requisição do challenge
        """
        challenge_token = await self.client.get(
            self.url_token_request
        )
        if challenge_token.status_code != 200:
            raise RuntimeError(f"Challenge request failed: {challenge_token.status_code}")
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
        authorization_json = json.loads(authorization_response.text)
        authorization_obfuscated = await asyncio.to_thread (self.obfuscate,authorization_json["username"])
        authorization = f"Basic {authorization_obfuscated}"

        return authorization
        

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(5), reraise=True)
    async def request_page(self, url: str) -> json:
        """Função que executa as requisições das paginas de dados e movimentos com o challenge em cache,
        caso acesso nao seja autorizado pede para recriar o token de autorização
        Args:
            url (str): Url da requisição
        Returns:
            resp (json): Retorna json que é retornado pelo site com as informações buscadas
        Raises:
            TJRSRateLimit: Erro de rate limit persistente
        """
        max_attempts = 8

        for attempt in range(max_attempts):
            auth = await self.get_auth()
            headers = {**self.headers_consulta, "Authorization": auth}
            resp = await self.client.get(url, headers=headers)
            text = resp.text

            if resp.status_code in (401, 403):
                auth = await self.get_auth(force_refresh=True)
                headers["Authorization"] = auth
                resp = await self.client.get(url, headers=headers)
                text = resp.text

            is429, msg = self.is_rate_limited(text)
            if is429:
                print(f"[429] {msg} | tentativa {attempt+1}/{max_attempts}")
                await self.sleep_backoff(attempt, base=2, cap=60)
                continue

        
            return text

        raise TJRSRateLimit("Limite de chamadas atingido (TJRS). Tente novamente.", retry_after=30)                                                                                             


    def extract_basic_data_partes(self, basic_data_json: str) -> dict:
        """Função que extrai dados basicos e partes do processo.
        Args:
            basic_data_json (json): Json com dados que vem do site
        Returns:
            data (dict): Dicionario com dados de interesse
        """
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
        """Função que extrai dados movimentos do processo.
        Args:
            movimentos_json (json): Json com movimentos que vem do site
        Returns:
            movimentos_list (list): Lista de dicionarios contendo data e descrição dos movimentos
        """
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
