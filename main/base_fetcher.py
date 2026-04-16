import aiohttp
import logging
from abc import ABC, abstractmethod
from typing import Optional

class BaseFetcher(ABC):
    TIMEOUT = aiohttp.ClientTimeout(total=30)
    HEADERS = {"User-Agent": "meta-generator/1.0 (github.com/yourname/meta)"}

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.TIMEOUT,
                headers=self.HEADERS
            )
        return self._session
    
    async def get(self, url: str) -> Optional[str]:
        session = await self._get_session()
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logging.error(f"Failed to GET {url}, status={resp.status}")
                    return None
                return await resp.text()
        except Exception as e:
            logging.error(f"Request failed: {e}")
            return None
        
    async def get_json(self, url) -> Optional[dict | list]:
        import json
        text = await self.get(url)
        if text is None:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON for {url}: {e}")

    async def close(self):
        logging.info('Closing session')
        if self._session and not self._session.closed:
            await self._session.close()
    
#Interface
@property
@abstractmethod
def platform_id(self) -> str:
    pass

@property
@abstractmethod
def platform_name(self) -> str:
    pass

@property
@abstractmethod
def platform_uid(self) -> str:
    pass

@abstractmethod
async def fetch(self) -> list[str]:
    pass