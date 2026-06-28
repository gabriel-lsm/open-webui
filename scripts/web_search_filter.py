"""
title: Smart Web Search Filter
author: Antigravity
description: Um filtro que utiliza um modelo menor para decidir se deve ou não pesquisar na web usando DuckDuckGo, adicionando o contexto aos modelos finais no OpenRouter.
version: 1.0.0
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# Verifica e instala dependência
try:
    from duckduckgo_search import AsyncDDGS
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "duckduckgo-search"])
    from duckduckgo_search import AsyncDDGS


class Filter:
    class Valves(BaseModel):
        evaluator_model: str = Field(
            default="llama3-8b", 
            description="O modelo menor a ser usado para avaliar se a busca web é necessária (precisa estar disponível na sua lista de modelos)."
        )
        max_results: int = Field(
            default=3,
            description="Número máximo de resultados da busca a serem injetados."
        )

    def __init__(self):
        self.valves = self.Valves()

    async def _evaluate_need_for_search(self, user_message: str, __event_emitter__: Any = None, __request__: Any = None) -> bool:
        """
        Usa o modelo configurado para decidir (True/False) se a pergunta precisa de internet.
        """
        # Prompt simples para forçar o LLM a responder apenas YES ou NO
        system_prompt = (
            "Você é um classificador. "
            "Responda APENAS com a palavra 'YES' se a pergunta do usuário requer informações recentes, "
            "notícias atuais, preços em tempo real, ou dados que só podem ser encontrados pesquisando na internet hoje. "
            "Responda APENAS com a palavra 'NO' caso contrário."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Avaliando necessidade de busca na web...", "done": False},
                }
            )

        try:
            # Pega o cliente HTTP do próprio request se existir (Open-WebUI internal API)
            # Para não depender de bibliotecas externas complexas, usaremos a API interna de chat.
            # Como a documentação de Filtros varia, a forma segura de acessar outro modelo
            # é através do __request__.app.state se necessário, mas para simplificar
            # podemos tentar usar a função de chat_completion global do OpenWebUI.
            
            from open_webui.models.users import Users
            from open_webui.main import generate_chat_completion
            
            if __request__ and hasattr(__request__.state, 'user'):
                user = __request__.state.user
            else:
                user = None

            payload = {
                "model": self.valves.evaluator_model,
                "messages": messages,
                "stream": False,
                "max_tokens": 10
            }
            
            response = await generate_chat_completion(payload, user=user)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()
            
            if "YES" in content:
                return True
            return False

        except Exception as e:
            print(f"Erro na avaliação da busca: {e}")
            # Em caso de erro, por segurança não pesquisa para não bloquear o fluxo principal.
            return False

    async def _perform_search(self, query: str) -> str:
        """
        Realiza a busca no DuckDuckGo e formata a string de contexto.
        """
        try:
            context = "Contexto encontrado na web para responder à pergunta:\n\n"
            async with AsyncDDGS() as ddgs:
                results = [r async for r in ddgs.text(query, max_results=self.valves.max_results)]
                
                if not results:
                    return ""

                for idx, result in enumerate(results):
                    context += f"[{idx + 1}] Título: {result.get('title')}\n"
                    context += f"Resumo: {result.get('body')}\n"
                    context += f"Link: {result.get('href')}\n\n"
            
            return context
        except Exception as e:
            print(f"Erro ao buscar na web: {e}")
            return ""

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Any = None,
        __user__: Optional[dict] = None,
        __request__: Any = None
    ) -> dict:
        """
        Intercepta a mensagem antes de ir para o LLM.
        """
        messages = body.get("messages", [])
        
        if not messages:
            return body
            
        last_message = messages[-1]
        if last_message.get("role") != "user":
            return body

        user_content = last_message.get("content", "")
        
        if not user_content:
            return body

        # Avalia
        needs_search = await self._evaluate_need_for_search(user_content, __event_emitter__, __request__)

        if needs_search:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Buscando informações na web...", "done": False},
                    }
                )

            # Extrai contexto da web
            web_context = await self._perform_search(user_content)

            if web_context:
                # Modifica a mensagem do usuário injetando o contexto no final.
                # A instrução ajuda o modelo principal a entender o que fazer com os dados.
                modified_content = (
                    f"{user_content}\n\n"
                    f"---\n"
                    f"INFORMAÇÃO DO SISTEMA:\n"
                    f"Uma busca na web foi realizada automaticamente para ajudar você a responder. "
                    f"Por favor, utilize o seguinte contexto se for relevante, mas não cite as URLs bruscamente, "
                    f"responda de forma natural. Se a informação não for relevante, ignore-a.\n\n"
                    f"{web_context}"
                )
                
                last_message["content"] = modified_content
                body["messages"][-1] = last_message
                
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {"description": "Contexto da web adicionado com sucesso.", "done": True},
                        }
                    )
        else:
             if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Busca web não necessária para esta pergunta.", "done": True},
                    }
                )

        return body
