import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base import LLMProvider, LLMResponse
import os

logger = logging.getLogger(__name__)

class IBMWatsonProvider(LLMProvider):
    """
    Proveedor de LLM usando IBM Watson AI (watsonx.ai).
    
    Maneja automaticamente:
    - Obtención de access token desde IAM
    - Renovación automática cuando expira
    - Caché del token válido
    """
    
    def __init__(
        self, 
        model_name: str = "meta-llama/llama-3-3-70b-instruct",
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        api_url: Optional[str] = None,
        iam_url: Optional[str] = None
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("IBM_API_KEY")
        self.project_id = project_id or os.getenv("IBM_PROJECT_ID")
        self.api_url = api_url or os.getenv(
            "IBM_API_URL",
            "https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29"
        )
        self.iam_url = iam_url or "https://iam.cloud.ibm.com/identity/token"
        
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        if not self.api_key:
            raise ValueError("IBM API key no configurada. Define IBM_API_KEY en .env")
        
        if not self.project_id:
            raise ValueError(
                "IBM project_id no configurado. Define IBM_PROJECT_ID en .env. "
                "Obtén este valor desde tu proyecto en IBM Cloud."
            )
        
        logger.info(f"Proveedor IBM Watson inicializado con modelo: {self.model_name}")
    
    async def _get_access_token(self) -> str:
        """
        Obtiene un access token de IBM IAM usando la API key.
        El token se cachea y se renueva automáticamente cuando expira.
        """
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry - timedelta(minutes=5):
                return self._access_token
        
        logger.info("Obteniendo nuevo access token de IBM IAM...")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.iam_url,
                    headers=headers,
                    data=data
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    raise Exception(
                        f"Failed to get IAM token ({response.status_code}): {error_detail}"
                    )
                
                token_data = response.json()

                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                
                if not access_token:
                    raise ValueError("IAM response no contiene access_token")
                
                self._access_token = access_token
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"✓ Access token obtenido (válido por {expires_in}s)")
                return access_token
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error obteniendo IAM token: {e}")
            raise
        except Exception as e:
            logger.error(f"Error obteniendo IAM token: {e}")
            raise
    
    async def generate_async(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Genera una respuesta usando IBM Watson."""
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            default_system = (
                "You are a helpful, respectful and honest assistant. "
                "Always answer as helpfully as possible, while being safe. "
                "Your answers should not include any harmful, unethical, racist, "
                "sexist, toxic, dangerous, or illegal content."
            )
            messages.append({"role": "system", "content": default_system})
        
        messages.append({"role": "user", "content": prompt})
        
        return await self.generate_with_messages_async(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def generate_with_messages_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """Genera respuesta con historial de mensajes."""
        
        access_token = await self._get_access_token()
        
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "user":
                formatted_messages.append({
                    "role": role,
                    "content": [{"type": "text", "text": content}]
                })
            else:
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
        
        payload = {
            "messages": formatted_messages,
            "project_id": self.project_id,
            "model_id": self.model_name,
            "frequency_penalty": 0,
            "max_tokens": max_tokens or 2000,
            "presence_penalty": 0,
            "temperature": temperature,
            "top_p": 1
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"IBM Watson API error: {response.status_code} - {error_detail}")
                    raise Exception(f"IBM Watson API error ({response.status_code}): {error_detail}")
                
                data = response.json()
                
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("IBM Watson response no contiene 'choices'")
                
                content = choices[0].get("message", {}).get("content", "")
                
                return LLMResponse(
                    content=content,
                    model=self.model_name,
                    usage=data.get("usage"),
                    metadata={
                        "finish_reason": choices[0].get("finish_reason"),
                        "provider": "ibm_watson"
                    }
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error en IBM Watson API: {e}")
            raise
        except Exception as e:
            logger.error(f"Error en IBM Watson API: {e}")
            raise