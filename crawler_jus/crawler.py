import logging
import asyncio
import time
import base64
import hashlib
import json
import httpx
from crawler_jus.util import find_obfuscate_and_extract_big_int
from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt,
)
from curl_cffi.requests import AsyncSession
from typing import Optional, Tuple
import random
from api.exceptions import (
    TJRSRateLimit,
    TJRSUnauthorized,
    TJRSUpstreamError,
    TJRSNetworkError,
)


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
        self._bigints: Optional[Tuple[int, int]] = None
        self._bigints_lock = asyncio.Lock()
        self._auth_value: Optional[str] = None
        self._auth_expires_at: float = 0.0
        self._auth_lock = asyncio.Lock()
        self._auth_ttl_seconds = 300

    async def close(self):
        """Função que fecha o cliente de requisiçoes web"""
        await self.client.close()

    async def get_big_ints(self, force_refresh: bool = False) -> tuple[int, int]:
        """
        Retorna os 2 inteiros usados no BigInt(numérico) do main.js.
        Cacheia o resultado e só recalcula se force_refresh=True ou cache vazio.
        """
        if not force_refresh and self._bigints is not None:
            return self._bigints

        async with self._bigints_lock:
            if not force_refresh and self._bigints is not None:
                return self._bigints

            bigints = await find_obfuscate_and_extract_big_int()

            if not isinstance(bigints, (list, tuple)) or len(bigints) < 2:
                raise RuntimeError("Falha ao extrair BigInt do main.js")

            self._bigints = (int(bigints[0]), int(bigints[1]))
            return self._bigints

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

    async def sleep_backoff(self, attempt: int, base: float = 0.5, cap: float = 30.0):
        """Função que aguarda tempo baseado na quantidade de tentivas ja feitas
        Args:
            attempt (int): Quantidade de tentativas
        """
        exp = min(cap, base * (2 ** attempt))
        wait = random.uniform(0, exp)
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

    async def obfuscate(self, auth: str) -> str:
        """Função que calcula o segredo que vai junto ao token challenge com base no mesmo para acesso ao site
        Args:
            auth (str): Token challenge resolvido
        Returns:
            final_str (str): Token challenge mais segredo em base64
        """
        big0, big1 = await self.get_big_ints()
        id_num = int(auth.replace("ChaAnon_", ""))

        n = (id_num % big0) + big1

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
        challenge_token = await self.client.get(self.url_token_request)
        if challenge_token.status_code != 200:
            raise RuntimeError(
                f"Challenge request failed: {challenge_token.status_code}"
            )
        challenge_data = json.loads(challenge_token.text)
        challenge_result = await asyncio.to_thread(
            self.solve_challenge,
            challenge_data["salt"],
            challenge_data["challenge"],
            challenge_data["maxnumber"],
        )
        payload = {
            "algorithm": challenge_data["algorithm"],
            "challenge": challenge_data["challenge"],
            "number": challenge_result,
            "salt": challenge_data["salt"],
            "signature": challenge_data["signature"],
        }

        json_str = json.dumps(payload, separators=(",", ":"))
        token_base64 = base64.b64encode(json_str.encode()).decode()
        form_data = {"altcha": token_base64}
        authorization_response = await self.client.post(
            self.url_token_submit, data=form_data
        )
        authorization_json = json.loads(authorization_response.text)
        authorization_obfuscated = await self.obfuscate(authorization_json["username"])
        authorization = f"Basic {authorization_obfuscated}"

        return authorization

    async def request_page(self, url: str) -> str:
        """Função que executa as requisições das paginas de dados e movimentos com o challenge em cache,
        caso acesso nao seja autorizado pede para recriar o token de autorização
        Args:
            url (str): url da requisição
        Returns:
            resp (json): Retorna json que é retornado pelo site com as informações buscadas
        Raises:
            TJRSRateLimit: Erro de rate limit persistente
            TJRSBadResponse: Erro inesperado
        """
        
        max_attempts = 4
        last_error: str | None = None
        rate_limit_hits = 0
        timeout = httpx.Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0)

        for attempt in range(max_attempts):
            try:
                auth = await self.get_auth()
                headers = {**self.headers_consulta, "Authorization": auth}

                resp = await self.client.get(url, headers=headers, timeout=timeout)
                text = resp.text or ""

                # 401/403 -> refresh e tenta de novo
                if resp.status_code in (401, 403):
                    self._auth_value = None
                    self._auth_expires_at = 0

                    self._bigints = None  # invalida cache
                    await self.get_big_ints(force_refresh=True)

                    auth = await self.get_auth(force_refresh=True)
                    headers["Authorization"] = auth
                    resp = await self.client.get(url, headers=headers, timeout=timeout)
                    text = resp.text or ""

                    if resp.status_code in (401, 403):
                        raise TJRSUnauthorized("Authorization inválido mesmo após refresh")

                #  rate limit por status
                if resp.status_code == 429:
                    rate_limit_hits += 1
                    last_error = "HTTP 429 Too Many Requests"
                    await self.sleep_backoff(attempt, base=2, cap=60)
                    continue

                #  HTML (bloqueio/captcha)
                ctype = (resp.headers.get("Content-Type") or "").lower()
                if "text/html" in ctype or text.lstrip().startswith("<"):
                    last_error = "TJRS retornou HTML (não JSON)"
                    await self.sleep_backoff(attempt, base=2, cap=1)
                    continue

                # rate limit por payload
                is429, msg = self.is_rate_limited(text)
                if is429:
                    rate_limit_hits += 1
                    last_error = f"Rate limit: {msg}"
                    await self.sleep_backoff(attempt, base=2, cap=60)
                    continue

                # 5xx
                if resp.status_code >= 500:
                    last_error = f"TJRS 5xx ({resp.status_code})"
                    await self.sleep_backoff(attempt, base=2, cap=5)
                    continue

                # 4xx (fora 401/403/429)
                if resp.status_code >= 400:
                    last_error = f"TJRS 4xx ({resp.status_code})"
                    await self.sleep_backoff(attempt, base=2, cap=5)
                    continue

                # resposta vazia
                if not text.strip():
                    last_error = "Resposta vazia"
                    await self.sleep_backoff(attempt, base=2, cap=1)
                    continue

                # JSON inválido/parcial
                try:
                    json.loads(text)
                except Exception:
                    last_error = "JSON inválido/parcial"
                    await self.sleep_backoff(attempt, base=2, cap=1)
                    continue

                return text

            except TJRSUnauthorized:
                raise

            except httpx.TimeoutException:
                last_error = "Timeout consultando TJRS"
                await self.sleep_backoff(attempt, base=2, cap=5)
                continue

            except Exception as e:
                last_error = f"Exceção inesperada: {type(e).__name__}: {e}"
                await self.sleep_backoff(attempt, base=2, cap=5)
                continue

        # pós-loop
        if rate_limit_hits >= 1:
            raise TJRSRateLimit("Limite de chamadas atingido (TJRS).", retry_after=30)

        if last_error and "Timeout" in last_error:
            raise TJRSNetworkError(last_error)

        raise TJRSUpstreamError(
            f"Falha ao consultar TJRS após {max_attempts} tentativas. Último erro: {last_error}"
        )


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
            "numeroProcesso": basic.get("numeroCNJFormatado"),
            "numeroProcessoCNJ": basic.get("numeroCNJ"),
            "classeCNJ": basic.get("classeCNJ"),
            "assuntoCNJ": basic.get("assuntoCNJ"),
            "nomeClasse": basic.get("nomeClasse"),
            "nomeNatureza": basic.get("nomeNatureza"),
            
            "comarca": basic.get("comarca", {}).get("nome"),
            "codigoComarca": basic.get("codigoComarca"),
            
            "dataDistribuicao": basic.get("dataDistribuicao"),
            "dataPropositura": basic.get("dataPropositura"),
            
            "situacaoProcesso": basic.get("situacaoProcesso"),
            "segredoJustica": basic.get("segredoJustica"),
            "tipoProcesso": basic.get("tipoProcesso"),

            "orgaoJulgador": basic.get("orgaoJulgador", {}).get("nome"),
        }
        data["partes"] = partes_list
        processos_vinculados = [
            {
                "numeroProcesso": pv.get("numeroCNJ"),
                "numeroFormatado": pv.get("numeroCNJFormatado"),
                "classe": pv.get("classeCNJ"),
                "assunto": pv.get("assuntoCNJ"),
                "comarca": pv.get("codigoComarca"),
                "orgaoJulgador": pv.get("nomeOrgaoJulgador"),
                "ultimaMovimentacao": pv.get("dataUltimaMovimentacao"),
            }
            for pv in basic.get("processosVinculados", [])
        ]

        data["processosVinculados"] = processos_vinculados
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
